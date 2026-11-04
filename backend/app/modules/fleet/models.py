"""Vehicles and drivers (`data-model.md`, Fleet).

`duty_session` is deliberately absent: it belongs to B11 with the duty endpoints, and a
table with no writer is a table nobody has thought about.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity
from app.domain.enums import TrackerType, VehicleType
from app.domain.state_machines import VehicleStatus


class Vehicle(TenantEntity):
    """A cab."""

    __tablename__ = "vehicle"
    __table_args__ = (
        # Registrations are unique per operator, not globally: two operators can
        # legitimately have run the same plate at different times.
        UniqueConstraint("operator_id", "registration_no", name="uq_vehicle_operator_rego"),
        UniqueConstraint("mqtt_username", name="uq_vehicle_mqtt_username"),
        CheckConstraint(
            "seat_capacity >= 1 AND seat_capacity <= 12", name="ck_vehicle_seat_capacity"
        ),
        Index("ix_vehicle_operator_status", "operator_id", "status"),
    )

    registration_no: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    vehicle_type: Mapped[str] = mapped_column(
        Enum(VehicleType, native_enum=False, length=20), nullable=False
    )
    seat_capacity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(VehicleStatus, native_enum=False, length=20),
        nullable=False,
        default=VehicleStatus.off_duty,
    )
    current_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("driver.id", ondelete="SET NULL")
    )
    # Issued at duty start (B11); unique so one credential cannot publish as two cabs.
    mqtt_username: Mapped[str | None] = mapped_column(String(100))
    tracker_type: Mapped[str] = mapped_column(
        Enum(TrackerType, native_enum=False, length=20),
        nullable=False,
        default=TrackerType.app,
    )


class Driver(TenantEntity):
    """A person who drives. Separate from `app_user`: a driver exists before first login."""

    __tablename__ = "driver"
    __table_args__ = (
        UniqueConstraint("operator_id", "phone", name="uq_driver_operator_phone"),
        CheckConstraint(
            "licence_last4 IS NULL OR licence_last4 ~ '^[A-Za-z0-9]{4}$'",
            name="ck_driver_licence_last4",
        ),
        Index("ix_driver_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    licence_last4: Mapped[str | None] = mapped_column(String(4))
    default_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        # No FK: vehicle.current_driver_id already points the other way, and a pair of
        # hard FKs makes both rows undeletable without a dance. Validated in the service.
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
