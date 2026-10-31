"""The `optimizer_run` table: every batch the optimizer was handed, and what it found (B30).

One row per run, written whether or not anything was placed. That is deliberate:

* "A batch that finds no solution leaves every request exactly as it was" is a claim about
  what *didn't* happen, and the only way to audit it afterwards is a record that the batch
  ran and found nothing;
* B36 decides the optimizer is down from the age and outcome of the last run;
* B39's reports and M11's metrics count batches, solver used, and how many requests each
  one placed.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity, tenant_index

#: `solved` - at least one request was placed. `no_solution` - the solver ran and placed
#: none. `failed` - it raised; the batch was left untouched and B36 treats it as a symptom.
#: `paused` - automation was paused, so the sweep did not solve anything and said so: a
#: marker that the optimizer was alive and deliberately idle, which is what stops a long
#: pause being mistaken for a dead worker on the first sweep after it ends (B36).
RUN_STATUSES = ("solved", "no_solution", "failed", "paused")


class OptimizerRun(TenantEntity):
    __tablename__ = "optimizer_run"
    __table_args__ = (tenant_index("optimizer_run", "started_at"),)

    #: From the injected Clock, never the database default (CLAUDE.md hard rule 2).
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    #: `greedy`, `darp`, or `greedy_fallback`.
    solver: Mapped[str | None] = mapped_column(String(20))
    requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    placed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unplaced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: How the plan was delivered, by the mode of each request's scope (B32).
    applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suggested: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hinted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: Wall-clock cost of the solve. Measurement, not business time, so it is the one
    #: place a real timer is read.
    solve_seconds: Mapped[float | None] = mapped_column(Float)
    plan_cost: Mapped[float | None] = mapped_column(Float)
    request_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    #: The plan as proposed: placements and the unplaced with their reasons.
    plan: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(String(500))
    #: The mode this batch was delivered under: `full_auto` applied, `semi_auto` offered,
    #: `manual` hinted (B32). A batch spanning scopes is one run per mode.
    mode: Mapped[str | None] = mapped_column(String(20))


class OptimizerHint(TenantEntity):
    """What the optimizer would do for a request in a `manual` scope (B32).

    `allocation-rules.md` §6: in `manual` the proposed trips "are shown as hints only".
    Not a `suggestion`: nobody is being asked to answer, there is no failsafe timer, and
    counting it among the offers would corrupt the acceptance metric Phase 2 is judged by.
    A hint is replaced by the next batch's and dies when its request does.
    """

    __tablename__ = "optimizer_hint"
    __table_args__ = (tenant_index("optimizer_hint", "request_id"),)

    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("optimizer_run.id", ondelete="CASCADE"), nullable=False
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ride_request.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False
    )
    #: No foreign key: a trip cancelled later must not delete what was once suggested.
    trip_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    rider_order: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    pickup_eta_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasons: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    #: Set when a later batch replaces this hint or the request leaves the queue.
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
