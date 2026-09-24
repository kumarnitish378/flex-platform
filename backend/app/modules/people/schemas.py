"""Employee request/response models, mirroring `api-spec.yaml`."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

PHONE_PATTERN = r"^\+[1-9][0-9]{7,14}$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LatLng(Strict):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class EmployeeInput(Strict):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(pattern=PHONE_PATTERN)
    office_id: uuid.UUID
    home_location: LatLng
    home_landmark: str | None = Field(default=None, max_length=200)
    priority: int = Field(default=5, ge=1, le=10)
    is_vip: bool = False
    night_escort_required: bool = False
    active: bool = True


class EmployeeUpdate(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    office_id: uuid.UUID | None = None
    home_location: LatLng | None = None
    home_landmark: str | None = Field(default=None, max_length=200)
    priority: int | None = Field(default=None, ge=1, le=10)
    is_vip: bool | None = None
    night_escort_required: bool | None = None
    active: bool | None = None


class EmployeeOut(Strict):
    id: uuid.UUID
    client_id: uuid.UUID
    zone_id: uuid.UUID | None = None
    name: str
    phone: str
    office_id: uuid.UUID
    home_location: LatLng | None = None
    home_landmark: str | None = None
    priority: int
    is_vip: bool
    night_escort_required: bool
    active: bool


class ImportRowError(Strict):
    """One problem with one row."""

    row: int
    field: str
    message: str


class ImportReport(Strict):
    total_rows: int
    valid_rows: int
    created: int = 0
    updated: int = 0
    errors: list[ImportRowError] = Field(default_factory=list)
