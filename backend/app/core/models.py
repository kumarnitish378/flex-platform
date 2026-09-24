"""Shared model plumbing: the declarative base's conventions.

Every table follows `data-model.md`: a UUID primary key, `created_at` and `updated_at`
in UTC, and — for tenant tables — an indexed `operator_id` that every query filters by.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.db import Base


def new_id() -> uuid.UUID:
    """Primary keys.

    `data-model.md` says "UUID v7 preferred, else v4". v7 is not in the standard library
    on our minimum Python (3.12), so v4 it is. Switching to v7 later is a change to this
    one function — worth doing for index locality on the high-volume tables (location_ping).
    """
    return uuid.uuid4()


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_id)


class TimestampMixin:
    """`created_at` / `updated_at`, both timezone-aware UTC.

    These come from the *database* clock, deliberately: they are row bookkeeping, not
    business facts. Any timestamp the business reasons about — `requested_time`,
    `hold_until`, `arrived_at` — must come from the injected `Clock` instead, or the
    simulator cannot control it (CLAUDE.md hard rule 2).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OperatorScopedMixin:
    """A tenant table. `operator_id` is indexed because every query filters on it."""

    @declared_attr
    @classmethod
    def operator_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            PG_UUID(as_uuid=True),
            ForeignKey("operator.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )


class Entity(UUIDMixin, TimestampMixin, Base):
    """Base for non-tenant tables (operators, users, OTP challenges)."""

    __abstract__ = True


class TenantEntity(UUIDMixin, TimestampMixin, OperatorScopedMixin, Base):
    """Base for tenant tables. Never query one without an `operator_id` filter."""

    __abstract__ = True


def tenant_index(table: str, *columns: str) -> Index:
    """Composite index starting at `operator_id`, the leading column of every lookup."""
    return Index(f"ix_{table}_operator_{'_'.join(columns)}", "operator_id", *columns)
