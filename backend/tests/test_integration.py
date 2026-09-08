import asyncio
import json
import os
import time
import uuid

import httpx
import pytest
import websockets
from websockets.exceptions import InvalidStatus

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
WS_URL = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")


def register(client: httpx.Client, prefix: str) -> tuple[str, str]:
    email = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/register", json={"email": email, "password": "integration-password"})
    assert response.status_code == 201, response.text
    return email, response.json()["access_token"]


def wait_for_event(client: httpx.Client, device_id: str, headers: dict[str, str], event_id: str) -> list[dict]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        response = client.get(f"/api/devices/{device_id}/telemetry", headers=headers)
        assert response.status_code == 200, response.text
        rows = response.json()
        if any(row["event_id"] == event_id for row in rows):
            return rows
        time.sleep(0.1)
    pytest.fail(f"telemetry event {event_id} was not persisted")


@pytest.mark.integration
def test_authentication_endpoints():
    with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
        email, token = register(client, "auth")
        assert client.post("/api/auth/register", json={"email": email, "password": "integration-password"}).status_code == 409
        assert client.post("/api/auth/login", json={"email": email, "password": "wrong-password"}).status_code == 401
        login = client.post("/api/auth/login", json={"email": email.upper(), "password": "integration-password"})
        assert login.status_code == 200
        assert login.json()["access_token"] != ""
        assert client.get("/api/devices").status_code == 401
        assert client.get("/api/devices", headers={"Authorization": "Bearer invalid"}).status_code == 401


@pytest.mark.integration
def test_end_to_end_ingestion_and_history():
    with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
        _, token = register(client, "integration")
        headers = {"Authorization": f"Bearer {token}"}

        r = client.post("/api/devices", json={"name": "test-device"}, headers=headers)
        assert r.status_code == 201, r.text
        device_id = r.json()["id"]

        event_id = str(uuid.uuid4())
        r = client.post(
            f"/api/devices/{device_id}/telemetry",
            json={"event_id": event_id, "metrics": {"temperature_c": 24.2}},
            headers=headers,
        )
        assert r.status_code == 202, r.text

        wait_for_event(client, device_id, headers, event_id)

        # Retry the exact same event: unique event_id keeps the write idempotent.
        r = client.post(
            f"/api/devices/{device_id}/telemetry",
            json={"event_id": event_id, "metrics": {"temperature_c": 99}},
            headers=headers,
        )
        assert r.status_code == 202
        sentinel_id = str(uuid.uuid4())
        r = client.post(
            f"/api/devices/{device_id}/telemetry",
            json={"event_id": sentinel_id, "metrics": {"sentinel": True}},
            headers=headers,
        )
        assert r.status_code == 202
        rows = wait_for_event(client, device_id, headers, sentinel_id)
        assert sum(row["event_id"] == event_id for row in rows) == 1
        original = next(row for row in rows if row["event_id"] == event_id)
        assert original["payload"] == {"temperature_c": 24.2}

        # Device-scoped authorization: another user must not see this device.
        _, other_token = register(client, "other")
        other_headers = {"Authorization": f"Bearer {other_token}"}
        forbidden = client.get(f"/api/devices/{device_id}/telemetry", headers=other_headers)
        assert forbidden.status_code == 404
        forbidden = client.post(
            f"/api/devices/{device_id}/telemetry",
            json={"metrics": {"unauthorized": True}},
            headers=other_headers,
        )
        assert forbidden.status_code == 404


@pytest.mark.integration
async def test_websocket_authorization_and_live_delivery():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=5.0) as client:
        owner_email = f"ws-owner-{uuid.uuid4().hex[:8]}@example.com"
        owner = await client.post("/api/auth/register", json={"email": owner_email, "password": "integration-password"})
        owner_token = owner.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        device = await client.post("/api/devices", json={"name": "websocket-device"}, headers=owner_headers)
        device_id = device.json()["id"]

        other_email = f"ws-other-{uuid.uuid4().hex[:8]}@example.com"
        other = await client.post("/api/auth/register", json={"email": other_email, "password": "integration-password"})
        other_token = other.json()["access_token"]

        with pytest.raises(InvalidStatus):
            async with websockets.connect(f"{WS_URL}/ws/devices/{device_id}?token={other_token}"):
                pass

        async with websockets.connect(f"{WS_URL}/ws/devices/{device_id}?token={owner_token}") as websocket:
            event_id = str(uuid.uuid4())
            response = await client.post(
                f"/api/devices/{device_id}/telemetry",
                json={"event_id": event_id, "metrics": {"live": True}},
                headers=owner_headers,
            )
            assert response.status_code == 202
            message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=10))
            assert message["event_id"] == event_id
            assert message["device_id"] == device_id
            assert message["payload"] == {"live": True}
