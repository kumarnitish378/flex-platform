"""suggestion_plan

Revision ID: e5a7c9b1f234
Revises: d4f6a8c0e123
Create Date: 2026-11-01 12:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e5a7c9b1f234"
down_revision: str | Sequence[str] | None = "d4f6a8c0e123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "suggestion", sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("suggestion", "plan")
