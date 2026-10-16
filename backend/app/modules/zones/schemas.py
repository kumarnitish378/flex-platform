"""Request and response bodies for `/admin/zones`, matching `api-spec.yaml` (B27)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.requests.schemas import LatLng


class ZoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=200)
    #: The outer ring, in order, open or closed. Three corners is the fewest that can
    #: enclose anything; the validation that matters - distinctness and self-crossing -
    #: happens in `to_polygon`, where the geometry library can answer it.
    boundary: list[LatLng] = Field(min_length=3)
    active: bool = True


class ZoneUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=200)
    boundary: list[LatLng] | None = Field(default=None, min_length=3)
    active: bool | None = None


class ZoneOut(BaseModel):
    id: uuid.UUID
    name: str
    boundary: list[LatLng]
    active: bool
    #: Employees whose home falls in this zone. An inactive zone covers nobody and
    #: reports zero, which is the point of deactivating one.
    employee_count: int = 0
