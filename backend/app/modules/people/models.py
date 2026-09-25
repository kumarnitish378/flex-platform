"""Employees and their saved places (`data-model.md`, Customers).

An employee exists before the person ever logs in — client admins import them in bulk
(B07) — so `user_id` is nullable and filled at first login.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity
from app.modules.tenancy.models import Point

DEFAULT_PRIORITY = 5


class Employee(TenantEntity):
    """A rider."""

    __tablename__ = "employee"
    __table_args__ = (
        # One person per phone within a client; the same phone may work for two clients.
        UniqueConstraint("client_id", "phone", name="uq_employee_client_phone"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="ck_employee_priority_range"),
        Index("ix_employee_operator_client", "operator_id", "client_id"),
        Index("ix_employee_user", "user_id"),
        # No explicit index on home_location: GeoAlchemy2 creates a GIST spatial index
        # (idx_employee_home_location) for every geography column already.
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    office_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("office.id", ondelete="RESTRICT"), nullable=False
    )
    #: Required: every rider has a home end to their journey (`data-model.md`).
    home_location: Mapped[object] = mapped_column(Point(), nullable=False)
    home_landmark: Mapped[str | None] = mapped_column(String(300))
    # Derived from `zone.area`; stays null until zones exist (B07 keeps this a stub).
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("zone.id", ondelete="SET NULL")
    )
    # 1 is the highest priority (glossary.md).
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=DEFAULT_PRIORITY)
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    night_escort_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SavedPlace(TenantEntity):
    """A place an employee reuses, e.g. "Home", "Gate 3"."""

    __tablename__ = "saved_place"
    __table_args__ = (
        UniqueConstraint("employee_id", "label", name="uq_saved_place_employee_label"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("employee.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[object] = mapped_column(Point(), nullable=False)
    landmark: Mapped[str | None] = mapped_column(String(300))
