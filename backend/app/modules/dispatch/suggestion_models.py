"""The `suggestion` table: offers the system made, and what became of them (B25).

B23 computed suggestions and returned them without storing anything, deliberately -
acceptance rate only means something where the *system* is doing the offering, which is
a `semi_auto` scope, and nothing ran in one yet. B25 is that scope, so the offers are
recorded now.

**Phase 2's exit criterion is "suggestion acceptance > 70%", and it cannot be evaluated
unless the offer exists as a row.** A suggestion that is only ever computed on a GET is
a recommendation nobody can audit: there is no way afterwards to say what the system
proposed, when, or whether the human took it.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity, tenant_index
from app.domain.failsafe import SuggestionStatus


class Suggestion(TenantEntity):
    """One vehicle the system offered for one request."""

    __tablename__ = "suggestion"
    __table_args__ = (
        tenant_index("suggestion", "request_id"),
        tenant_index("suggestion", "status"),
        # The sweep's query: everything still open whose timer has run out.
        tenant_index("suggestion", "status", "failsafe_due_at"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False
    )
    #: The trip this would join, or `NULL` when it would open a new one. No foreign key:
    #: a trip that is later cancelled must not delete the record of what was offered.
    trip_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    #: 1 is the system's first choice. Stored rather than derived, because the ranking
    #: it had *at the time* is the thing worth auditing - cost moves as traffic does.
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    #: The §5 phrases exactly as the supervisor saw them. Kept verbatim: "+4 min for
    #: Rahul" is the claim they acted on, and recomputing it later gives a different
    #: number against a different world.
    reasons: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    status: Mapped[str] = mapped_column(
        Enum(SuggestionStatus, native_enum=False, length=20),
        nullable=False,
        default=SuggestionStatus.offered,
    )
    #: From the injected Clock, never the database default - the simulator has to be
    #: able to make a failsafe fire (CLAUDE.md hard rule 2).
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: When the failsafe is due. Recomputed when an escalation extends it.
    failsafe_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: Set once, when `escalate` fires the first time, so the second timeout assigns.
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    #: Why a supervisor rejected it, when they say. Free text rather than a code: this
    #: is the training data Phase 3 tunes the cost function with, and a fixed list
    #: decided now would only record the reasons we already thought of.
    decided_note: Mapped[str | None] = mapped_column(String(300))
