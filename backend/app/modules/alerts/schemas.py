"""Request and response bodies for `/alerts`, `/sos` and `/driver/issues`."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AlertOut(BaseModel):
    id: uuid.UUID
    type: str
    severity: str
    status: str
    created_at: datetime
    request_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class SosInput(BaseModel):
    """EMP-08. Only the position is required: whoever presses this is in trouble."""

    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    trip_id: uuid.UUID | None = None


class DriverIssueInput(BaseModel):
    """DRV-06."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["breakdown", "accident", "traffic_block", "rider_issue", "other"]
    note: str | None = Field(default=None, max_length=300)
    trip_id: uuid.UUID | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
