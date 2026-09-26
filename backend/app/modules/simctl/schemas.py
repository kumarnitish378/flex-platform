"""Sim control request/response models (`api-spec.yaml` SimClock)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SimClockUpdate(Strict):
    now: datetime | None = None
    advance_seconds: int | None = Field(default=None, description="alternative to now")


class SimClockState(Strict):
    now: datetime
    #: What the jump triggered, so the simulator can assert on it without a second call.
    expired: int = 0
    near_expiry_alerts: int = 0
    #: Stop ETAs recomputed by the jump (B15), so a scenario can assert on them.
    stop_etas_refreshed: int = 0
    #: Vehicles that went quiet and were alerted on by the jump (B17).
    stale_vehicle_alerts: int = 0


class ResetRequest(Strict):
    scenario_yaml: str | None = None
    start_time: datetime | None = None
    #: How big a world to seed. The defaults are the fixture in `testing-strategy.md`
    #: section 4; a scenario larger than that says so, because a fixed fixture caps every
    #: scenario at the smallest one (M06).
    employees: int | None = Field(default=None, ge=1, le=2000)
    vehicles: int | None = Field(default=None, ge=1, le=500)


class SeededUser(Strict):
    role: str
    phone: str
    user_id: uuid.UUID
    access_token: str


class ResetResult(Strict):
    operator_id: uuid.UUID
    client_id: uuid.UUID
    office_ids: list[uuid.UUID]
    zone_ids: list[uuid.UUID]
    employee_ids: list[uuid.UUID]
    vehicle_ids: list[uuid.UUID]
    driver_ids: list[uuid.UUID]
    users: list[SeededUser]
    now: datetime
