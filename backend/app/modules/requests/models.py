"""Ride requests and their event log (`data-model.md`, Requests and trips).

`ride_request_event` is append-only: every status change writes one, with who did it and
why. That is what makes "why was this cancelled at 18:42" answerable six months later,
and it is required by `trip-lifecycle.md` for every transition.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity
from app.domain.enums import ActorType, Direction, RequestChannel, Urgency
from app.domain.state_machines import RequestStatus
from app.modules.tenancy.models import Point


class RideRequest(TenantEntity):
    __tablename__ = "ride_request"
    __table_args__ = (
        Index("ix_ride_request_operator_status", "operator_id", "status"),
        Index("ix_ride_request_employee_time", "employee_id", "requested_time"),
        # The dispatch board reads "everything still open for this operator" constantly.
        Index("ix_ride_request_open", "operator_id", "status", "requested_time"),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employee.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Enum(Direction, native_enum=False, length=20), nullable=False
    )
    office_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("office.id", ondelete="RESTRICT"), nullable=False
    )
    #: Home/pickup for to_office, drop for from_office.
    location: Mapped[object] = mapped_column(Point(), nullable=False)
    landmark: Mapped[str | None] = mapped_column(String(200))
    requested_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    urgency: Mapped[str] = mapped_column(
        Enum(Urgency, native_enum=False, length=20), nullable=False, default=Urgency.medium
    )
    no_sharing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        Enum(RequestStatus, native_enum=False, length=20),
        nullable=False,
        default=RequestStatus.requested,
    )
    channel: Mapped[str] = mapped_column(
        Enum(RequestChannel, native_enum=False, length=20),
        nullable=False,
        default=RequestChannel.app,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    lock_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="SET NULL")
    )
    forced_priority: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hold_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    override_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[str | None] = mapped_column(String(200))
    #: Set from the Clock at creation, never from the database default: the simulator
    #: has to be able to make a request expire.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Set once when the near-expiry alert fires, so it cannot fire twice.
    near_expiry_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def is_locked(self) -> bool:
        return self.lock_vehicle_id is not None


class RideRequestEvent(TenantEntity):
    """Append-only. Never updated, never deleted."""

    __tablename__ = "ride_request_event"
    __table_args__ = (Index("ix_ride_request_event_request", "request_id", "at"),)

    request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_type: Mapped[str] = mapped_column(
        Enum(ActorType, native_enum=False, length=20), nullable=False
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    reason: Mapped[str | None] = mapped_column(String(200))
    #: Event time from the injected Clock, not the row's created_at.
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[Any | None] = mapped_column(JSONB)
