import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from .auth import decode_access_token
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Device
from .realtime import manager, redis_fanout_listener
from .redis_client import redis_client
from .routers import auth, devices


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    stop_event = asyncio.Event()
    listener = asyncio.create_task(redis_fanout_listener(stop_event))
    app.state.redis_stop_event = stop_event
    try:
        yield
    finally:
        stop_event.set()
        await listener
        await redis_client.aclose()
        await engine.dispose()


app = FastAPI(title="Real-Time Device Management Platform", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(devices.router)


@app.get("/health")
async def health() -> dict[str, str]:
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.websocket("/ws/devices/{device_id}")
async def device_stream(websocket: WebSocket, device_id: uuid.UUID, token: str):
    try:
        user_id = decode_access_token(token)
        async with SessionLocal() as session:
            result = await session.execute(select(Device.id).where(Device.id == device_id, Device.owner_id == user_id))
            if result.scalar_one_or_none() is None:
                await websocket.close(code=4404)
                return
    except Exception:
        await websocket.close(code=4401)
        return

    await manager.connect(device_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(device_id, websocket)
