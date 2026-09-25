"""`location_ping` (`data-model.md`, Tracking).

Partitioned by month on `recorded_at` and kept for 90 days. Partitioning is not premature
here: at 200 vehicles pinging every 5 seconds this table grows by roughly 100 million rows
a year, and dropping a month is instant where deleting one is not.

No `updated_at`: a ping is a fact about an instant and is never edited.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.models import new_id
from app.domain.enums import GpsSource
from app.modules.tenancy.models import Point


class LocationPing(Base):
    __tablename__ = "location_ping"
    __table_args__ = (
        # A partitioned table's primary key must contain the partition key.
        PrimaryKeyConstraint("id", "recorded_at", name="pk_location_ping"),
        Index("ix_location_ping_vehicle_time", "vehicle_id", "recorded_at"),
        Index("ix_location_ping_operator_time", "operator_id", "recorded_at"),
        {"postgresql_partition_by": "RANGE (recorded_at)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), default=new_id)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False
    )
    operator_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    #: Device time — what the phone says. The ordering that matters.
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Server time — how late it arrived. The difference is the lag metric.
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[object] = mapped_column(Point, nullable=False)
    speed_mps: Mapped[float | None] = mapped_column(Float)
    heading_deg: Mapped[float | None] = mapped_column(Float)
    accuracy_m: Mapped[float | None] = mapped_column(Float)
    battery_pct: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(
        Enum(GpsSource, native_enum=False, length=10), nullable=False, default=GpsSource.app
    )
