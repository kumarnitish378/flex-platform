"""Duty sessions (`data-model.md`, Fleet).

A row per on-duty period, so "who was driving that cab at 18:40" is answerable, and so
GPS retention can be tied to duty (non-functional.md: driver GPS only while on duty).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
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
    #: Mosquitto's `$7$` hash. The plaintext is returned once and never stored.
    mqtt_password_hash: Mapped[str | None] = mapped_column(String(300))
