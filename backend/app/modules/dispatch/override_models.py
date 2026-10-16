"""The `override_log` table (`data-model.md`, `control-model.md` §3 rule 6, B26).

"Every override written to `override_log` (who, what, before, after, reason, time)."
Two things make this more than an audit trail:

* **It is the expiry.** Rule 5 gives every standing override an `expires_at`, and rule 5
  has to take effect with nothing running. The open row *is* the override; the columns
  on `ride_request`, `trip` and `vehicle` are the applied state, and a read checks the
  row's expiry before trusting them. Un-applying an override is therefore one `UPDATE`
  of `expires_at` on this table, not a sweep.
* **It is training data.** Rule 7: Phase 3-4 tune the optimizer from what supervisors
  actually overrode and why, which only works if `before` and `after` are the real
  values and not a prose summary of them.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity, tenant_index
from app.domain.overrides import OverrideAction, ReasonCode


class OverrideLog(TenantEntity):
    """One override a human applied, and what it changed."""

    __tablename__ = "override_log"
    __table_args__ = (
        # The question every read path asks: "is there an override still in force on
        # this thing?" - so the index is the one that answers it.
        tenant_index("override_log", "action", "expires_at"),
        tenant_index("override_log", "request_id"),
        tenant_index("override_log", "trip_id"),
        tenant_index("override_log", "vehicle_id"),
        # The report of rule 4's flagged overrides, by day.
        tenant_index("override_log", "at"),
    )

    action: Mapped[str] = mapped_column(
        Enum(OverrideAction, native_enum=False, length=30), nullable=False
    )
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE")
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trip.id", ondelete="CASCADE")
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="CASCADE")
    )

    #: The fields this action touched, before and after. Narrow on purpose: a whole-row
    #: snapshot would bury the one value that changed and would record a rider's home
    #: location in a table nobody thinks of as holding personal data.
    before: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    after: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    reason_code: Mapped[str] = mapped_column(
        Enum(ReasonCode, native_enum=False, length=30), nullable=False
    )
    note: Mapped[str | None] = mapped_column(String(500))

    #: Rule 4: the hard rules this override waived, if any. A column rather than a flag
    #: inside `after`, because "show me every hard-rule override this week" is a report
    #: an operator admin runs, and `jsonb` predicates are not something a report should
    #: have to know about.
    waived_violations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    #: Rule 5. `NULL` means "until the trip ends" - the open-ended form the rule allows.
    #: Set to the moment of release when the inverse action (`unlock`) closes this row.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    #: Who. `SET NULL` rather than `CASCADE`: a supervisor leaving the company must not
    #: delete the record of the decisions they made.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL")
    )
    #: From the injected Clock, never `now()` - the simulator has to be able to place an
    #: override at a simulated moment (CLAUDE.md hard rule 2).
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
