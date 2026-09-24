"""`operator_config` and its history (`data-model.md`, Dispatch control)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity


class OperatorConfig(TenantEntity):
    """One configured value. Absent rows fall back to the documented default."""

    __tablename__ = "operator_config"
    __table_args__ = (UniqueConstraint("operator_id", "key", name="uq_operator_config_key"),)

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    # jsonb, because the values are numbers, booleans, times and enum strings.
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    # Incremented on every change; lets a client detect a lost update.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class OperatorConfigHistory(TenantEntity):
    """Append-only record of every change.

    Separate from `audit_log` on purpose: `allocation-rules.md` treats config as
    versioned data, and reconstructing "what was the detour limit last Tuesday" from a
    generic audit stream is painful. Rows are never updated or deleted.
    """

    __tablename__ = "operator_config_history"
    __table_args__ = (Index("ix_operator_config_history_key", "operator_id", "key", "created_at"),)

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Any | None] = mapped_column(JSONB)
    new_value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
