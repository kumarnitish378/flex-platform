"""Sim control request/response models (`api-spec.yaml` SimClock)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import VehicleType


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


class ReleaseRequest(Strict):
    """Give up a claim on the backend (see `/simctl/reset`'s `run_id`)."""

    run_id: str = Field(max_length=128)


class FleetSpec(Strict):
    """One group of cabs to seed, as the scenario describes them."""

    type: VehicleType
    count: int = Field(ge=1, le=500)


class ResetRequest(Strict):
    scenario_yaml: str | None = None
    start_time: datetime | None = None
    #: How big a world to seed. The defaults are the fixture in `testing-strategy.md`
    #: section 4; a scenario larger than that says so, because a fixed fixture caps every
    #: scenario at the smallest one (M06).
    employees: int | None = Field(default=None, ge=1, le=2000)
    vehicles: int | None = Field(default=None, ge=1, le=500)
    #: The exact mix of cabs to seed. Without this only the *number* of vehicles was
    #: honoured and the composition came from the fixture, so a scenario asking for two
    #: VIP cars could silently get one - and a VIP scenario with no VIP car tests
    #: nothing. Overrides `vehicles` when both are given.
    fleet: list[FleetSpec] | None = None
    #: Identifies the run claiming this backend. A reset while another run holds the
    #: claim is refused, because it would truncate that run's world out from under it.
    run_id: str | None = Field(default=None, max_length=128)
    #: Take the backend over anyway - for a claim left behind by a crashed run.
    force: bool = False
    #: How many of the seeded employees are VIPs. Defaults to one, the historic fixture.
    vip_employees: int | None = Field(default=None, ge=0, le=500)


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
    #: Which of those employees are VIPs. A scenario about VIP handling (S07) cannot be
    #: written without this: bursting ordinary riders would report a VIP result that was
    #: never tested.
    vip_employee_ids: list[uuid.UUID]
    vehicle_ids: list[uuid.UUID]
    #: Which of those vehicles are VIP cars, so a scenario can check that a VIP was not
    #: put in an ordinary cab (`allocation-rules.md` section 2 rule 4).
    vip_vehicle_ids: list[uuid.UUID]
    driver_ids: list[uuid.UUID]
    users: list[SeededUser]
    now: datetime
