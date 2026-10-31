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

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity, tenant_index

#: `solved` - at least one request was placed. `no_solution` - the solver ran and placed
#: none. `failed` - it raised; the batch was left untouched and B36 treats it as a symptom.
RUN_STATUSES = ("solved", "no_solution", "failed")


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
