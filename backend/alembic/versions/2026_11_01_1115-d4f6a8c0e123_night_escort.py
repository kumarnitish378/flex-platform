"""night_escort

Revision ID: d4f6a8c0e123
Revises: c3e5a7b9d123
Create Date: 2026-11-01 11:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d4f6a8c0e123"
down_revision: str | Sequence[str] | None = "c3e5a7b9d123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("employee", sa.Column("gender", sa.String(length=10), nullable=True))
    op.add_column("trip", sa.Column("escort_basis", sa.String(length=30), nullable=True))
    op.add_column(
        "trip", sa.Column("escort_confirmed_by", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "trip", sa.Column("escort_confirmed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("trip", sa.Column("escort_note", sa.String(length=200), nullable=True))
    op.create_foreign_key(
        "trip_escort_confirmed_by_fkey",
        "trip",
        "app_user",
        ["escort_confirmed_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("trip_escort_confirmed_by_fkey", "trip", type_="foreignkey")
    for column in ("escort_note", "escort_confirmed_at", "escort_confirmed_by", "escort_basis"):
        op.drop_column("trip", column)
    op.drop_column("employee", "gender")
