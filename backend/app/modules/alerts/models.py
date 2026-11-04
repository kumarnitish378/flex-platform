"""Alerts (`data-model.md`, Alerts).

The table lands with B09 because the expiry job needs somewhere to record a near-expiry
warning. B17 adds the endpoints and the other alert types.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity
from app.domain.enums import AlertSeverity, AlertStatus, AlertType


class Alert(TenantEntity):
    __tablename__ = "alert"
    __table_args__ = (
        Index("ix_alert_operator_status", "operator_id", "status"),
        Index("ix_alert_request", "request_id"),
    )

    type: Mapped[str] = mapped_column(Enum(AlertType, native_enum=False, length=30), nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum(AlertSeverity, native_enum=False, length=20),
        nullable=False,
        default=AlertSeverity.warning,
    )
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE")
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="SET NULL")
    )
    data: Mapped[Any | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        Enum(AlertStatus, native_enum=False, length=20), nullable=False, default=AlertStatus.open
    )
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
