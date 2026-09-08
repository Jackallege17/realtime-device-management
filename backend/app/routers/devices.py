import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..dependencies import get_current_user, get_owned_device
from ..models import Device, Telemetry, User
from ..redis_client import redis_client
from ..schemas import DeviceCreate, DeviceOut, IngestAccepted, TelemetryIn, TelemetryOut

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Device]:
    result = await db.execute(select(Device).where(Device.owner_id == current_user.id).order_by(Device.created_at))
    return list(result.scalars())


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def create_device(
    body: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    device = Device(owner_id=current_user.id, name=body.name)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.post("/{device_id}/telemetry", response_model=IngestAccepted, status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    device_id: uuid.UUID,
    body: TelemetryIn,
    _device: Device = Depends(get_owned_device),
) -> IngestAccepted:
    message = {
        "event_id": str(body.event_id),
        "device_id": str(device_id),
        "recorded_at": body.recorded_at.isoformat(),
        "payload": body.metrics,
        "attempt": 0,
    }
    await redis_client.lpush("telemetry:queue", json.dumps(message))
    return IngestAccepted(event_id=body.event_id)


@router.get("/{device_id}/telemetry", response_model=list[TelemetryOut])
async def history(
    device_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    before: datetime | None = None,
    _device: Device = Depends(get_owned_device),
    db: AsyncSession = Depends(get_db),
) -> list[Telemetry]:
    query = select(Telemetry).where(Telemetry.device_id == device_id)
    if before is not None:
        query = query.where(Telemetry.recorded_at < before)
    query = query.order_by(Telemetry.recorded_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars())
