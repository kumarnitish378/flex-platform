"""Trip ratings (`data-model.md`, Alerts, notifications, feedback; B18, EMP-07)."""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Entity


class TripRating(Entity):
    """One rating per request. EMP-07: "rate the trip 1-5 ... (once per trip)"."""

    __tablename__ = "trip_rating"
    __table_args__ = (
        # The uniqueness is the "once per trip" rule; enforcing it in the service alone
        # would lose to two taps on a slow connection.
        UniqueConstraint("request_id", name="uq_trip_rating_request"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_trip_rating_range"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employee.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))
