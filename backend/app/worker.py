import asyncio
import json
import uuid
from datetime import datetime

import redis.asyncio as redis
from sqlalchemy.dialects.postgresql import insert

from .config import settings
from .db import SessionLocal
from .models import Telemetry

QUEUE = "telemetry:queue"
DEAD_LETTER_QUEUE = "telemetry:dead"
MAX_ATTEMPTS = 4


async def persist(message: dict) -> bool:
    stmt = (
        insert(Telemetry)
        .values(
            event_id=uuid.UUID(message["event_id"]),
            device_id=uuid.UUID(message["device_id"]),
            recorded_at=datetime.fromisoformat(message["recorded_at"]),
            payload=message["payload"],
        )
        .on_conflict_do_nothing(index_elements=[Telemetry.event_id])
        .returning(Telemetry.event_id)
    )
    async with SessionLocal() as session:
        result = await session.execute(stmt)
        inserted = result.scalar_one_or_none() is not None
        await session.commit()
    return inserted


async def process_message(client: redis.Redis, raw: str) -> None:
    try:
        message = json.loads(raw)
        if not isinstance(message, dict):
            raise ValueError("queue message must be a JSON object")
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        dead_message = {
            "raw": raw,
            "attempt": MAX_ATTEMPTS,
            "last_error": f"invalid queue message: {exc}",
        }
        await client.lpush(DEAD_LETTER_QUEUE, json.dumps(dead_message))
        return

    try:
        inserted = await persist(message)
        if inserted:
            await client.publish("telemetry:live", json.dumps(message))
    except Exception as exc:
        try:
            attempt = int(message.get("attempt", 0)) + 1
        except (TypeError, ValueError):
            attempt = MAX_ATTEMPTS
        message["attempt"] = attempt
        message["last_error"] = str(exc)
        if attempt >= MAX_ATTEMPTS:
            await client.lpush(DEAD_LETTER_QUEUE, json.dumps(message))
        else:
            await asyncio.sleep(min(2 ** (attempt - 1), 8))
            await client.lpush(QUEUE, json.dumps(message))


async def run() -> None:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    print("telemetry worker started", flush=True)
    try:
        while True:
            item = await client.brpop(QUEUE, timeout=2)
            if item is None:
                continue
            _, raw = item
            await process_message(client, raw)
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(run())
