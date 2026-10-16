"""Request and response bodies for `/dispatch/*`, matching `api-spec.yaml`."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Direction, VehicleType
from app.domain.overrides import OverrideAction, OverrideCommand, ReasonCode
from app.modules.requests.schemas import LatLng


class AddedMinutes(BaseModel):
    request_id: uuid.UUID
    minutes: float


class CandidateOut(BaseModel):
    vehicle_id: uuid.UUID
    registration_no: str
    trip_id: uuid.UUID | None = None
    eta_to_pickup_seconds: int
    eta_approximate: bool = False
    seats_free_after: int
    #: How old this vehicle's position is by the server's clock; `None` if it has never
    #: reported one. `gps_stale` in `violations` says only that it crossed the threshold.
    gps_age_seconds: float | None = None
    added_minutes_existing: list[AddedMinutes] = Field(default_factory=list)
    new_trip: bool = True
    #: Phase 2 fills these; Phase 1 has no cost function and no ranked reasons.
    cost: float | None = None
    reasons: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)


class VehicleLiveOut(BaseModel):
    id: uuid.UUID
    registration_no: str
    model: str | None = None
    vehicle_type: VehicleType
    seat_capacity: int
    status: str
    position: LatLng | None = None
    position_at: datetime | None = None
    stale: bool
    active_trip_id: uuid.UUID | None = None
    seats_free: int


class TripStopOut(BaseModel):
    id: uuid.UUID
    sequence: int
    stop_type: str
    request_id: uuid.UUID
    location: LatLng
    status: str
    planned_eta: datetime | None = None
    latest_eta: datetime | None = None
    eta_approximate: bool = False
    arrived_at: datetime | None = None
    done_at: datetime | None = None


class TripOut(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    direction: Direction
    office_id: uuid.UUID
    status: str
    pooling_blocked: bool
    mode_used: str
    stops: list[TripStopOut] = Field(default_factory=list)
    #: Hard rules this assignment broke and the supervisor accepted (ADR-0011).
    violations: list[str] = Field(default_factory=list)


class AssignInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: uuid.UUID
    vehicle_id: uuid.UUID
    trip_id: uuid.UUID | None = None
    reason_code: str | None = None
    note: str | None = Field(default=None, max_length=200)


class DriverEventInput(BaseModel):
    """One tap from the driver app (`api-spec.yaml` requestBodies/DriverEvent)."""

    model_config = ConfigDict(extra="forbid")

    #: Generated on the device so a retry is recognisable as the same tap.
    client_event_id: uuid.UUID
    #: When the driver tapped, which may be long before we hear about it.
    occurred_at: datetime
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class AutomationOut(BaseModel):
    automation_paused: bool


class AutomationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automation_paused: bool
    reason_code: str
    note: str | None = Field(default=None, max_length=200)


class OverrideInput(BaseModel):
    """One supervisor override (`control-model.md` §3, `api-spec.yaml` OverrideInput)."""

    model_config = ConfigDict(extra="forbid")

    action: OverrideAction
    reason_code: ReasonCode
    request_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    target_vehicle_id: uuid.UUID | None = None
    hold_until: datetime | None = None
    #: Omitted means "end of the current shift" (§3 rule 5). An explicit `null` means
    #: "until the trip ends", which the same rule allows - so the two are not the same
    #: request, and `model_fields_set` is what tells them apart.
    expires_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)

    def to_command(self) -> OverrideCommand:
        return OverrideCommand(
            action=self.action,
            reason_code=self.reason_code,
            request_id=self.request_id,
            trip_id=self.trip_id,
            vehicle_id=self.vehicle_id,
            target_vehicle_id=self.target_vehicle_id,
            hold_until=self.hold_until,
            expires_at=self.expires_at,
            expiry_specified="expires_at" in self.model_fields_set,
            note=self.note,
        )


class AffectedRequestOut(BaseModel):
    request_id: uuid.UUID
    employee_name: str
    added_minutes: float | None = None
    eta_change_minutes: float | None = None
    requeued: bool = False


class ImpactOut(BaseModel):
    """§3 rule 2's confirm screen."""

    affected_requests: list[AffectedRequestOut] = Field(default_factory=list)
    zones_without_available_vehicle: list[str] = Field(default_factory=list)
    #: Each one naming the config key that set the limit, where there is one (B21).
    hard_rule_violations: list[str] = Field(default_factory=list)


class OverrideResultOut(BaseModel):
    override_id: uuid.UUID
    impact: ImpactOut
    #: When this override lapses. `null` means it stands until the trip ends.
    expires_at: datetime | None = None
    trip_id: uuid.UUID | None = None
