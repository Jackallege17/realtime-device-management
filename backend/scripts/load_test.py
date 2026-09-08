#!/usr/bin/env python3
import argparse
import asyncio
import os
import statistics
import time
import uuid
from datetime import datetime

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    idx = min(len(values) - 1, int((len(values) - 1) * p))
    return values[idx]


async def wait_for_persistence(
    database_url: str,
    device_id: str,
    expected_events: int,
    timeout_seconds: float,
) -> tuple[int, datetime | None, datetime | None, float]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    started = time.perf_counter()
    try:
        while True:
            async with engine.connect() as connection:
                row = (
                    await connection.execute(
                        text(
                            "SELECT count(*) AS count, min(created_at) AS first_row_timestamp, "
                            "max(created_at) AS last_row_timestamp FROM telemetry WHERE device_id = :device_id"
                        ),
                        {"device_id": uuid.UUID(device_id)},
                    )
                ).one()
            if row.count >= expected_events:
                return row.count, row.first_row_timestamp, row.last_row_timestamp, time.perf_counter() - started
            if time.perf_counter() - started >= timeout_seconds:
                return row.count, row.first_row_timestamp, row.last_row_timestamp, time.perf_counter() - started
            await asyncio.sleep(0.05)
    finally:
        await engine.dispose()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--persistence-timeout", type=float, default=120.0)
    args = parser.parse_args()

    if args.events < 1:
        parser.error("--events must be at least 1")
    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1")

    email = f"bench-{uuid.uuid4().hex[:8]}@example.com"
    password = "benchmark-password"
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(base_url=args.url, timeout=timeout) as client:
        register = await client.post("/api/auth/register", json={"email": email, "password": password})
        register.raise_for_status()
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        create_device = await client.post("/api/devices", json={"name": "load-test-device"}, headers=headers)
        create_device.raise_for_status()
        device_id = create_device.json()["id"]
        sem = asyncio.Semaphore(args.concurrency)
        latencies: list[float] = []

        async def send_one(i: int) -> None:
            async with sem:
                start = time.perf_counter()
                r = await client.post(
                    f"/api/devices/{device_id}/telemetry",
                    json={"metrics": {"seq": i, "temperature_c": 20 + (i % 15) * 0.1}},
                    headers=headers,
                )
                r.raise_for_status()
                latencies.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        await asyncio.gather(*(send_one(i) for i in range(args.events)))
        enqueue_elapsed = time.perf_counter() - start

        persistence = None
        if args.database_url:
            persistence = await wait_for_persistence(
                args.database_url,
                device_id,
                args.events,
                args.persistence_timeout,
            )

        query_times = []
        for _ in range(20):
            q0 = time.perf_counter()
            r = await client.get(f"/api/devices/{device_id}/telemetry?limit=100", headers=headers)
            r.raise_for_status()
            query_times.append((time.perf_counter() - q0) * 1000)

    print(f"requests={args.events} concurrency={args.concurrency}")
    print(f"API enqueue throughput: {args.events / enqueue_elapsed:.1f} req/s")
    print(f"API enqueue latency ms: p50={statistics.median(latencies):.2f} p95={percentile(latencies, .95):.2f} p99={percentile(latencies, .99):.2f}")
    print(f"history query latency ms: p50={statistics.median(query_times):.2f} p95={percentile(query_times, .95):.2f}")

    if persistence is None:
        print("PostgreSQL persistence: not measured (set DATABASE_URL or --database-url)")
        return

    persisted, first_row_timestamp, last_row_timestamp, drain_elapsed = persistence
    end_to_end_elapsed = enqueue_elapsed + drain_elapsed
    print(f"PostgreSQL persisted: {persisted}/{args.events} events")
    print(f"PostgreSQL end-to-end persistence throughput: {persisted / end_to_end_elapsed:.1f} events/s")
    print(f"Post-enqueue drain time (last 202 to observed full persistence): {drain_elapsed:.3f} s")
    if persisted > 1 and first_row_timestamp is not None and last_row_timestamp is not None:
        row_timestamp_span = (last_row_timestamp - first_row_timestamp).total_seconds()
        if row_timestamp_span > 0:
            print(
                "Worker/PostgreSQL row-timestamp-span throughput (approx.): "
                f"{(persisted - 1) / row_timestamp_span:.1f} events/s"
            )
        else:
            print("Worker/PostgreSQL row-timestamp-span throughput (approx.): unavailable (zero timestamp span)")
    if persisted < args.events:
        raise RuntimeError(
            f"persistence timeout: only {persisted}/{args.events} events reached PostgreSQL "
            f"within {args.persistence_timeout:.1f} s"
        )


if __name__ == "__main__":
    asyncio.run(main())
