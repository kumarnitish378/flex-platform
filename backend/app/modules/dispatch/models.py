"""Trips and their stops (`data-model.md`, Requests and trips; B14).

A trip is one vehicle carrying one or more riders in one direction to or from one office.
Each rider on it contributes a pickup stop and a drop stop, so that finishing a stop can
move exactly one request's status (`trip-lifecycle.md` section 3).

`trip_event` is append-only, like `ride_request_event`: it is how "why did this trip take a
40-minute detour on 12 March" stays answerable, including which hard-rule violations the
supervisor accepted at assignment (ADR-0011).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity
from app.domain.enums import ActorType, Direction
from app.domain.state_machines import StopKind, StopStatus, TripStatus
from app.modules.tenancy.models import Point


def LineString() -> Geography:  # noqa: N802 - reads as a type at the call site
    """The route the driver actually follows, drawn once the trip starts (B15+)."""
    return Geography(geometry_type="LINESTRING", srid=4326)


#: `mode_used` values, matching `api-spec.yaml`. Phase 1 only ever writes "manual".
MODE_VALUES = ("manual", "semi_auto", "full_auto", "failsafe")
MODE_MANUAL = "manual"


class Trip(TenantEntity):
    __tablename__ = "trip"
    __table_args__ = (
        Index("ix_trip_operator_status", "operator_id", "status"),
        Index("ix_trip_vehicle_status", "vehicle_id", "status"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="RESTRICT"), nullable=False
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("driver.id", ondelete="RESTRICT"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Enum(Direction, native_enum=False, length=20), nullable=False
    )
    office_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("office.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(TripStatus, native_enum=False, length=20), nullable=False, default=TripStatus.planned
    )
    pooling_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: All from the injected Clock, never the database default (CLAUDE.md hard rule 2).
    planned_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_distance_m: Mapped[float | None] = mapped_column(Float)
    actual_distance_m: Mapped[float | None] = mapped_column(Float)
    empty_distance_m: Mapped[float | None] = mapped_column(Float)
    mode_used: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    #: LINESTRING once the route is drawn (B15+); null while the trip is only planned.
    route_geometry: Mapped[object | None] = mapped_column(LineString(), nullable=True)


class TripStop(TenantEntity):
    __tablename__ = "trip_stop"
    __table_args__ = (
        UniqueConstraint("trip_id", "sequence", name="uq_trip_stop_sequence"),
        Index("ix_trip_stop_trip", "trip_id", "sequence"),
        Index("ix_trip_stop_request", "request_id"),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    stop_type: Mapped[str] = mapped_column(
        Enum(StopKind, native_enum=False, length=20), nullable=False
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE"), nullable=False
    )
    location: Mapped[object] = mapped_column(Point(), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(StopStatus, native_enum=False, length=20), nullable=False, default=StopStatus.pending
    )
    planned_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: True when the ETA came from the approx provider rather than road routing (ADR-0010).
    eta_approximate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: Set once when the "cab 5 minutes away" notification fires, so it cannot fire
    #: twice as the ETA wobbles around the threshold (EMP-05, B16).
    near_alert_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: When `latest_eta` was last recomputed - not the same as `latest_eta` itself, which
    #: is a future arrival. The refresh job needs to know its own cadence (B15).
    eta_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: Where the driver actually was when they marked the stop, for disputes.
    event_location: Mapped[object | None] = mapped_column(Point(), nullable=True)


class TripEvent(TenantEntity):
    """Append-only. Never updated, never deleted."""

    __tablename__ = "trip_event"
    __table_args__ = (
        Index("ix_trip_event_trip", "trip_id", "at"),
        # Idempotency for driver actions (B15). Unique where present; many NULLs are
        # fine, because only driver-sent events carry a device key.
        Index("uq_trip_event_client_event", "client_event_id", unique=True),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip.id", ondelete="CASCADE"), nullable=False
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
    #: When the driver actually tapped, which is not when we heard about it: the app
    #: queues actions offline and sends them later (`coding-standards.md` section 5).
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: Device-generated idempotency key. A retried offline event must not apply twice.
    client_event_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    #: Notification targets, accepted violations, the rider added - whatever the
    #: transition needs to stay explainable later.
    data: Mapped[Any | None] = mapped_column(JSONB)
