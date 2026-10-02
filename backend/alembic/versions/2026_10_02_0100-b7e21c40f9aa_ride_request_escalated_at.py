"""ride_request escalated_at and queued_at

`escalated_at` is set once when an unassigned request is escalated, so the supervisor is
alerted once however many times the sweep runs (ADR-0019, allocation-rules.md 3.1).

`queued_at` is when the rider asked, from the injected Clock. `created_at` is the row's
own bookkeeping and comes from the database's `now()` - the *system* clock - so under the
simulator it is real wall time while every event it is compared against is simulated.
Anything that measures waiting has to use `queued_at` (CLAUDE.md hard rule 2). Existing
rows are backfilled from `created_at`, which is the best available answer for them and is
exactly right for every row written by a non-simulated run.

Revision ID: b7e21c40f9aa
Revises: a1c4de77b210
Create Date: 2026-10-02 01:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7e21c40f9aa"
down_revision: str | Sequence[str] | None = "a1c4de77b210"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ride_request", sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("ride_request", sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE ride_request SET queued_at = created_at WHERE queued_at IS NULL")
    op.alter_column("ride_request", "queued_at", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ride_request", "queued_at")
    op.drop_column("ride_request", "escalated_at")
