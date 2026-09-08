import json
from unittest.mock import AsyncMock

import pytest

from app import worker


def message(attempt: int = 0) -> str:
    return json.dumps(
        {
            "event_id": "05c9f685-740b-47f8-b6c6-1064e8910a81",
            "device_id": "65e38851-79e3-411a-b16d-52218af11bca",
            "recorded_at": "2026-09-08T12:00:00+00:00",
            "payload": {"temperature_c": 23.5},
            "attempt": attempt,
        }
    )


@pytest.mark.parametrize("raw", ["not-json", "[]"])
async def test_invalid_message_goes_to_dead_letter_queue(raw):
    client = AsyncMock()

    await worker.process_message(client, raw)

    client.lpush.assert_awaited_once()
    queue, encoded = client.lpush.await_args.args
    assert queue == worker.DEAD_LETTER_QUEUE
    assert json.loads(encoded)["attempt"] == worker.MAX_ATTEMPTS
    client.publish.assert_not_awaited()


async def test_transient_failure_is_requeued(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(worker, "persist", AsyncMock(side_effect=RuntimeError("database unavailable")))
    sleep = AsyncMock()
    monkeypatch.setattr(worker.asyncio, "sleep", sleep)

    await worker.process_message(client, message())

    sleep.assert_awaited_once_with(1)
    queue, encoded = client.lpush.await_args.args
    retried = json.loads(encoded)
    assert queue == worker.QUEUE
    assert retried["attempt"] == 1
    assert retried["last_error"] == "database unavailable"


async def test_exhausted_failure_goes_to_dead_letter_queue(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(worker, "persist", AsyncMock(side_effect=RuntimeError("still unavailable")))

    await worker.process_message(client, message(worker.MAX_ATTEMPTS - 1))

    queue, encoded = client.lpush.await_args.args
    assert queue == worker.DEAD_LETTER_QUEUE
    assert json.loads(encoded)["attempt"] == worker.MAX_ATTEMPTS


@pytest.mark.parametrize("inserted,publish_count", [(True, 1), (False, 0)])
async def test_only_newly_persisted_events_are_published(monkeypatch, inserted, publish_count):
    client = AsyncMock()
    monkeypatch.setattr(worker, "persist", AsyncMock(return_value=inserted))

    await worker.process_message(client, message())

    assert client.publish.await_count == publish_count
    client.lpush.assert_not_awaited()
