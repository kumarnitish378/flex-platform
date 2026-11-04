"""Notification records (`data-model.md`, Alerts, notifications, feedback; B16).

Every push is written here first and sent second. The row is the record of what the
product told a person: "I was never told my cab changed" is a support conversation that
needs an answer, and a log line that has rotated away is not one.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Entity


class Notification(Entity):
    __tablename__ = "notification"
    __table_args__ = (
        Index("ix_notification_user", "user_id", "sent_at"),
        # The app's unread badge reads exactly this.
        Index("ix_notification_unread", "user_id", "read_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    data: Mapped[Any | None] = mapped_column(JSONB)
    #: From the injected Clock, so the simulator's timeline holds (hard rule 2).
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    #: False when every device rejected it, so "we told them" is not assumed.
    delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
