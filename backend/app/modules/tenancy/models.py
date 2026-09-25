"""Operators, clients, offices, client policies and zones (`data-model.md`).

Enums are stored as VARCHAR with a CHECK constraint (`native_enum=False`) rather than as
PostgreSQL enum types: adding a value to a native enum needs a migration that cannot run
inside a transaction on older servers, and these lists will grow.
"""

from __future__ import annotations

import uuid
from datetime import time

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Entity, TenantEntity
from app.domain.enums import ClientStatus, OperatorStatus

# Points and polygons are geography (not geometry) so distance is in metres on a sphere
# without us choosing a projection (`data-model.md` header).
#
# Factories, not shared instances: GeoAlchemy2 stamps a column's `nullable` onto the type
# object, so one shared `Geography` handed to several columns leaks the first NOT NULL it
# sees to all the others. That silently made `employee.home_location` NOT NULL.


def Point() -> Geography:  # noqa: N802 - reads as a type at the call site
    return Geography(geometry_type="POINT", srid=4326)


def Polygon() -> Geography:  # noqa: N802
    return Geography(geometry_type="POLYGON", srid=4326)


class Operator(Entity):
    """A cab company. The tenant boundary: everything else hangs off this."""

    __tablename__ = "operator"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(OperatorStatus, native_enum=False, length=20),
        nullable=False,
        default=OperatorStatus.active,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Kolkata")
    automation_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Client(TenantEntity):
    """A corporate customer of an operator."""

    __tablename__ = "client"
    __table_args__ = (UniqueConstraint("operator_id", "name", name="uq_client_operator_name"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(200))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(
        Enum(ClientStatus, native_enum=False, length=20),
        nullable=False,
        default=ClientStatus.active,
    )


class Office(TenantEntity):
    """A client site. Trips run to and from these."""

    __tablename__ = "office"
    __table_args__ = (UniqueConstraint("client_id", "name", name="uq_office_client_name"),)

    client_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("client.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[object] = mapped_column(Point(), nullable=False)
    address_text: Mapped[str | None] = mapped_column(String(500))


class ClientPolicy(TenantEntity):
    """Per-client overrides of operator config.

    The nullable numbers may only make a rule *stricter* than the operator default
    (`allocation-rules.md` §1, "stricter only"). That rule is enforced in the config
    service (B05), not here, because it needs the operator value to compare against.
    """

    __tablename__ = "client_policy"
    __table_args__ = (
        UniqueConstraint("client_id", name="uq_client_policy_client"),
        CheckConstraint(
            "max_detour_factor IS NULL OR (max_detour_factor >= 1.0 AND max_detour_factor <= 3.0)",
            name="ck_client_policy_detour_factor_range",
        ),
        CheckConstraint(
            "max_detour_minutes IS NULL OR (max_detour_minutes >= 0 AND max_detour_minutes <= 60)",
            name="ck_client_policy_detour_minutes_range",
        ),
        CheckConstraint(
            "pickup_window_minutes IS NULL"
            " OR (pickup_window_minutes >= 0 AND pickup_window_minutes <= 30)",
            name="ck_client_policy_pickup_window_range",
        ),
        CheckConstraint(
            "no_show_wait_minutes IS NULL"
            " OR (no_show_wait_minutes >= 1 AND no_show_wait_minutes <= 15)",
            name="ck_client_policy_no_show_range",
        ),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client.id", ondelete="CASCADE"), nullable=False
    )
    pooling_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    employee_opt_out_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    night_safety_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    night_start: Mapped[time | None] = mapped_column(Time)
    night_end: Mapped[time | None] = mapped_column(Time)
    max_detour_factor: Mapped[float | None] = mapped_column(Numeric(3, 2))
    max_detour_minutes: Mapped[int | None] = mapped_column(Integer)
    pickup_window_minutes: Mapped[int | None] = mapped_column(Integer)
    no_show_wait_minutes: Mapped[int | None] = mapped_column(Integer)


class Zone(TenantEntity):
    """An operational area, used for pooling and for mode scoping."""

    __tablename__ = "zone"
    __table_args__ = (UniqueConstraint("operator_id", "name", name="uq_zone_operator_name"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    area: Mapped[object] = mapped_column(Polygon(), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
