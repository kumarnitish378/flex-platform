"""Bodies for the rating endpoint and the trip report."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RatingInput(BaseModel):
    """EMP-07: 1-5 with an optional comment, once per trip."""

    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


class RatingOut(BaseModel):
    request_id: Any
    rating: int
    comment: str | None = None


class TripReportOut(BaseModel):
    trips: int
    requests: int
    median_wait_minutes: float | None = None
    p90_wait_minutes: float | None = None
    no_shows: int
    cancellations: int
    #: Requests assigned by each kind of actor (B34).
    assignments_by_actor: dict[str, int] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class OperationsReportOut(BaseModel):
    """`GET /reports/operations` (B39). Sections are documented in `api-spec.yaml`."""

    period: dict[str, str]
    requests: dict[str, int]
    wait: dict[str, Any]
    pooling: dict[str, Any]
    distance: dict[str, Any]
    overrides: dict[str, Any]
    suggestions: dict[str, Any]
    assignments_by_actor: dict[str, int]
    optimizer: dict[str, Any]


class BillingBasisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    basis: str
    note: str | None = Field(default=None, max_length=200)


class BillingBasisOut(BaseModel):
    session_id: Any
    basis: str
    set_by: Any = None
    set_at: Any = None
    note: str | None = None


class BillingExportOut(BaseModel):
    """`GET /reports/billing` (B38): one row per cab per day."""

    client_id: Any
    client_name: str
    month: str
    treatment: dict[str, Any]
    summary: dict[str, Any]
    rows: list[dict[str, Any]] = Field(default_factory=list)
