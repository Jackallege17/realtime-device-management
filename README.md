# Real-Time Device Management Platform

A full-stack reference application for registering devices, accepting bursty telemetry, persisting queryable history, and delivering newly persisted events to authorized browser clients in real time.

## Architecture

```text
React + Vite dashboard
        | REST (JWT bearer token)
        | WebSocket (JWT query parameter)
        v
FastAPI API --------------------------------------------------+
        |                                                     | Redis pub/sub subscriber
        | owner checks                                        |
        v                                                     v
Redis telemetry:queue --> Python worker --> PostgreSQL --> telemetry:live
                             |                    |             Redis channel
                             | retry              |
                             +--> telemetry:dead  +--> history queries
```

The API validates the JWT and device ownership before accepting telemetry. A successful ingestion request returns `202 Accepted` after `LPUSH`; it does **not** mean that PostgreSQL has committed the event. The worker consumes the FIFO queue with `BRPOP`, inserts one event per transaction, and publishes only newly inserted rows. API processes subscribed to `telemetry:live` fan out those committed events to WebSocket connections for the same device.

PostgreSQL is the history system of record. `telemetry.event_id` has a global unique constraint, and `INSERT ... ON CONFLICT DO NOTHING` makes client and worker retries idempotent: the first persisted payload wins. The `(device_id, recorded_at)` index supports newest-first history reads and cursor-like `before` filtering.

## Implemented behavior

- Email/password registration and login; passwords are hashed with bcrypt and access tokens are signed HS256 JWTs.
- Bearer-token authentication for all device REST endpoints.
- Device-scoped authorization for listing, ingesting, reading history, and opening WebSockets. A device owned by another user is returned as not found.
- Asynchronous Redis-backed ingestion with generated or client-supplied event IDs.
- PostgreSQL idempotency and newest-first telemetry history (`limit` 1–1000).
- Worker retries with 1, 2, and 4 second exponential delays, followed by `telemetry:dead` on the fourth failed attempt.
- Invalid/non-object queue messages are moved to the dead-letter queue rather than terminating the worker.
- Live delivery only after a new row commits; idempotent duplicates are not published again.

## Run locally

Requirements: Docker with the Compose plugin. Ports 8000 and 5173 must be available.

```bash
cp .env.example .env
docker compose up --build
```

The checked-in `.env.example` contains development-only credentials. Set a strong, private `JWT_SECRET` before any shared or production deployment.

Open the dashboard at <http://localhost:5173> and the OpenAPI UI at <http://localhost:8000/docs>. Check the stack without deleting its data:

```bash
docker compose ps
docker compose exec -T api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```

Stop containers while preserving the named PostgreSQL volume:

```bash
docker compose stop
```

Do not use `docker compose down -v` if the local database must be retained.

## API

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/devices
POST /api/devices
POST /api/devices/{device_id}/telemetry
GET  /api/devices/{device_id}/telemetry?limit=100&before=<ISO-8601 timestamp>
WS   /ws/devices/{device_id}?token=<jwt>
GET  /health
```

Example telemetry payload:

```json
{
  "event_id": "5f3d6cd5-f2f0-4a5e-9cc3-5c135bb542b4",
  "recorded_at": "2026-09-08T05:00:00Z",
  "metrics": {
    "temperature_c": 23.7,
    "cpu_pct": 41.2
  }
}
```

Both `event_id` and `recorded_at` are optional. The API generates them when omitted.

## Tests

Build the current source before container-based validation:

```bash
docker compose up -d --build
```

Run the complete backend suite, including tests against the live API, Redis, worker, and PostgreSQL:

```bash
docker compose exec -T api python -m pytest
```

Run the two groups separately:

```bash
docker compose exec -T api python -m pytest -m "not integration"
docker compose exec -T api python -m pytest -m integration tests/test_integration.py
```

Validate the frontend production bundle:

```bash
docker compose exec -T frontend npm run build
```

The GitHub Actions workflow starts PostgreSQL, Redis, the API, and the worker; runs non-integration and integration tests; and builds the frontend with the committed npm lockfile.

### Verified on 2026-09-08

- Backend: 12/12 tests passed on Python 3.12.14 and pytest 8.4.1.
- Frontend: TypeScript and Vite production build passed (28 modules transformed).
- Automated integration coverage: registration/login errors, missing and invalid JWTs, device creation, asynchronous persistence, first-write-wins idempotency, cross-user history/ingestion denial, unauthorized WebSocket rejection, and authorized live WebSocket delivery.
- Automated worker coverage: retry requeue, exhausted retry dead-lettering, invalid-message dead-lettering, new-event publication, and duplicate publication suppression.
- Manual dashboard smoke test: registration, login, device creation, telemetry submission, Live telemetry, and History.
- Compose services observed running: API, worker, frontend, healthy PostgreSQL, and healthy Redis.

## Benchmark

Run the benchmark inside the API container so it can query PostgreSQL directly as well as call the HTTP API:

```bash
docker compose exec -T api python scripts/load_test.py \
  --events 5000 \
  --concurrency 100 \
  --persistence-timeout 180
```

The metrics deliberately separate two stages:

- **API enqueue throughput and latency** measure the telemetry HTTP requests through their `202 Accepted` responses. This is Redis enqueue capacity, not database write throughput.
- **PostgreSQL end-to-end persistence throughput** measures all persisted events divided by elapsed time from the first request until the database count reaches the requested total.
- **Worker/PostgreSQL row-timestamp-span throughput (approx.)** uses the span between the first and last `telemetry.created_at` values. PostgreSQL `now()` supplies a transaction timestamp, not a true commit timestamp, so this is only an approximate view of the single-worker persistence pipeline and must not be interpreted as actual commit throughput.
- **Post-enqueue drain time** is the elapsed time from the final HTTP `202 Accepted` response until the benchmark observes that all target events have been persisted.

### Local result (single run, 2026-09-08)

Environment: macOS 15.7.9 on arm64; Docker Desktop Engine 29.7.2; Docker Compose 5.5.1; Docker VM allocation 8 CPUs and 4,106,604,544 bytes (~3.82 GiB) memory; PostgreSQL 16.15; Redis 7.4.11. The stack was a non-isolated local development environment with one API process and one worker. Results are not production capacity claims.

```text
requests=5000 concurrency=100
API enqueue throughput: 841.0 req/s
API enqueue latency ms: p50=109.14 p95=142.90 p99=290.01
history query latency ms: p50=3.10 p95=4.19
PostgreSQL persisted: 5000/5000 events
PostgreSQL end-to-end persistence throughput: 754.3 events/s
Post-enqueue drain time (last 202 to observed full persistence): 0.683 s
Worker/PostgreSQL row-timestamp-span throughput (approx.): 757.0 events/s
```

For a concurrency sweep, each point creates a new user/device and reports the same metrics:

```bash
docker compose exec -T api sh -c 'EVENTS=2000 ./scripts/run_benchmark_matrix.sh http://localhost:8000'
```

Benchmark rows remain in the named local PostgreSQL volume unless removed explicitly. The benchmark does not delete them.

## Known limitations

- This is a development Compose stack. Vite serves the frontend in dev mode; TLS, a reverse proxy, hardened secrets, and production process management are not configured.
- JWTs have no refresh/revocation flow. The WebSocket token is passed in the query string and may appear in access/proxy logs; use a safer handshake or redaction strategy in production.
- Redis AOF is enabled, but no Redis volume is declared. Recreating the Redis container can lose queued events.
- `BRPOP` removes a message before the PostgreSQL commit. A worker crash during that in-flight window can lose one event; there is no processing-list acknowledgement/reclaim protocol.
- Retry backoff sleeps inside the single worker and temporarily blocks later events. The dead-letter queue has no replay or administrative UI.
- Redis pub/sub is best-effort and has no replay. A disconnected browser must refresh PostgreSQL history after reconnecting.
- Database tables are created with SQLAlchemy `create_all`; schema migrations are not configured.
- `/health` checks PostgreSQL only. It does not prove Redis connectivity, worker liveness, queue drain, or frontend health.
- There is no rate limiting, telemetry payload size policy, observability stack, automated browser test, or retention policy.
- Performance results are one local run and should be rerun on the intended deployment hardware with representative payloads and sustained load.
