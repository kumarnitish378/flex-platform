"""Duty sessions (`data-model.md`, Fleet).

A row per on-duty period, so "who was driving that cab at 18:40" is answerable, and so
GPS retention can be tied to duty (non-functional.md: driver GPS only while on duty).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity


class DutySession(TenantEntity):
    __tablename__ = "duty_session"
    __table_args__ = (
        Index("ix_duty_session_driver", "driver_id", "started_at"),
        Index("ix_duty_session_vehicle", "vehicle_id", "started_at"),
        # One open session per vehicle at a time; enforced as a partial unique index
        # because two drivers sharing a cab's credentials would corrupt its GPS stream.
        Index(
            "uq_duty_session_open_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=("ended_at IS NULL"),
        ),
        Index(
            "uq_duty_session_open_driver",
            "driver_id",
            unique=True,
            postgresql_where=("ended_at IS NULL"),
        ),
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("driver.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False
    )
    #: From the injected Clock, never the database default.
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: What the dashboard showed when the driver went on and off duty, in km. Optional: a driver
    #: who does not enter one is billed on GPS. The gap against the GPS figure is how a bad
    #: reading - or a phone that lost signal for an hour - gets noticed (per-cab-per-day billing).
    odometer_start_km: Mapped[float | None] = mapped_column(Float)
    odometer_end_km: Mapped[float | None] = mapped_column(Float)
    #: Metres the cab moved between going on and off duty, measured from its pings when the
    #: session closed (jitter and bad fixes ignored). NULL until then, or when it sent too
    #: few pings: "not measured", never zero.
    gps_distance_m: Mapped[float | None] = mapped_column(Float)
    #: `gps` (the default when NULL) or `odometer`: which figure this day is billed on. Only an
    #: operator admin sets it, and who and when is kept.
    billing_basis: Mapped[str | None] = mapped_column(String(10))
    billing_basis_set_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    billing_basis_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    billing_basis_note: Mapped[str | None] = mapped_column(String(200))
    #: Mosquitto's `$7$` hash. The plaintext is returned once and never stored.
    mqtt_password_hash: Mapped[str | None] = mapped_column(String(300))
