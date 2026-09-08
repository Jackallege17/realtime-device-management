import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    created_at: datetime


class TelemetryIn(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[str, Any]


class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: uuid.UUID
    device_id: uuid.UUID
    recorded_at: datetime
    payload: dict[str, Any]


class IngestAccepted(BaseModel):
    event_id: uuid.UUID
    status: str = "queued"
