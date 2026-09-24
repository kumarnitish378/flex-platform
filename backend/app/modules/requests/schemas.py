"""Ride request request/response models, mirroring `api-spec.yaml`."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Direction, Urgency
from app.domain.state_machines import RequestStatus


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LatLng(Strict):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class RideRequestInput(Strict):
    direction: Direction
    requested_time: datetime
    employee_id: uuid.UUID | None = Field(
        default=None, description="required when created on behalf; ignored for employee role"
    )
    location: LatLng | None = Field(default=None, description="defaults to employee home")
    landmark: str | None = Field(default=None, max_length=200)
    urgency: Urgency = Urgency.medium
    no_sharing: bool = False


class CancelInput(Strict):
    reason: str | None = Field(default=None, max_length=200)


class RideRequestOut(Strict):
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str | None = None
    client_id: uuid.UUID
    direction: Direction
    office_id: uuid.UUID
    location: LatLng
    landmark: str | None = None
    requested_time: datetime
    urgency: Urgency
    no_sharing: bool
    status: RequestStatus
    waiting_since: datetime
    trip_id: uuid.UUID | None = None
    assignment: None = Field(
        default=None,
        description="populated once dispatch assigns a vehicle (B14)",
    )
    locked: bool = False
    cancel_reason: str | None = None
    expires_at: datetime
