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
    rows: list[dict[str, Any]] = Field(default_factory=list)
