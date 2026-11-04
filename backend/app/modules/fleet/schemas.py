"""Admin request/response models, mirroring `api-spec.yaml`."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import Role, TrackerType, VehicleType
from app.domain.state_machines import VehicleStatus

PHONE_PATTERN = r"^\+[1-9][0-9]{7,14}$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LatLng(Strict):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


# --- clients and offices ------------------------------------------------------


class ClientInput(Strict):
    name: str = Field(min_length=1, max_length=200)
    contact_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, pattern=PHONE_PATTERN)


class ClientOut(ClientInput):
    id: uuid.UUID


class OfficeInput(Strict):
    name: str = Field(min_length=1, max_length=200)
    location: LatLng
    address_text: str | None = Field(default=None, max_length=500)


class OfficeOut(Strict):
    id: uuid.UUID
    client_id: uuid.UUID
    name: str
    location: LatLng
    address_text: str | None = None


# --- vehicles -------------------------------------------------------------------


class VehicleInput(Strict):
    registration_no: str = Field(min_length=1, max_length=20)
    model: str | None = Field(default=None, max_length=100)
    vehicle_type: VehicleType
    seat_capacity: int = Field(ge=1, le=12)
    tracker_type: TrackerType = TrackerType.app


class VehicleUpdate(Strict):
    """PATCH: every field optional, but an empty body is rejected by the router."""

    registration_no: str | None = Field(default=None, min_length=1, max_length=20)
    model: str | None = Field(default=None, max_length=100)
    vehicle_type: VehicleType | None = None
    seat_capacity: int | None = Field(default=None, ge=1, le=12)
    tracker_type: TrackerType | None = None
    status: VehicleStatus | None = None
    current_driver_id: uuid.UUID | None = None


class VehicleOut(Strict):
    id: uuid.UUID
    registration_no: str
    model: str | None = None
    vehicle_type: VehicleType
    seat_capacity: int
    tracker_type: TrackerType
    status: VehicleStatus
    current_driver_id: uuid.UUID | None = None


# --- drivers ----------------------------------------------------------------------


class DriverInput(Strict):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(pattern=PHONE_PATTERN)
    licence_last4: str | None = Field(default=None, pattern=r"^[A-Za-z0-9]{4}$")
    default_vehicle_id: uuid.UUID | None = None
    active: bool = True


class DriverUpdate(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    licence_last4: str | None = Field(default=None, pattern=r"^[A-Za-z0-9]{4}$")
    default_vehicle_id: uuid.UUID | None = None
    active: bool | None = None


class DriverOut(Strict):
    id: uuid.UUID
    name: str
    phone: str
    licence_last4: str | None = None
    default_vehicle_id: uuid.UUID | None = None
    active: bool


# --- users --------------------------------------------------------------------------


class UserInvite(Strict):
    phone: str = Field(pattern=PHONE_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    # The contract restricts invites to these three; drivers and employees are created
    # through their own records, and platform_admin is never invited by an operator.
    role: Role = Field(json_schema_extra={"enum": ["supervisor", "client_admin", "operator_admin"]})
    client_id: uuid.UUID | None = None


class InvitedUser(Strict):
    user_id: uuid.UUID
    phone: str
    name: str
    role: Role
    client_id: uuid.UUID | None = None
