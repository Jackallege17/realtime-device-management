import asyncio
import json
import uuid
from collections import defaultdict

import redis.asyncio as redis
from fastapi import WebSocket

from .config import settings


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, device_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[device_id].add(websocket)

    async def disconnect(self, device_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[device_id].discard(websocket)
            if not self._connections[device_id]:
                self._connections.pop(device_id, None)

    async def broadcast(self, device_id: uuid.UUID, message: dict) -> None:
        async with self._lock:
            sockets = list(self._connections.get(device_id, set()))
        dead = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(device_id, ws)


manager = ConnectionManager()


async def redis_fanout_listener(stop_event: asyncio.Event) -> None:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe("telemetry:live")
    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                continue
            try:
                data = json.loads(message["data"])
                await manager.broadcast(uuid.UUID(data["device_id"]), data)
            except (ValueError, KeyError, json.JSONDecodeError):
                continue
    finally:
        await pubsub.unsubscribe("telemetry:live")
        await pubsub.aclose()
        await client.aclose()
