"""duty_session_billing

Revision ID: f6b8d0c2a345
Revises: e5a7c9b1f234
Create Date: 2026-11-02 10:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f6b8d0c2a345"
down_revision: str | Sequence[str] | None = "e5a7c9b1f234"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("duty_session", sa.Column("odometer_start_km", sa.Float(), nullable=True))
    op.add_column("duty_session", sa.Column("odometer_end_km", sa.Float(), nullable=True))
    op.add_column("duty_session", sa.Column("gps_distance_m", sa.Float(), nullable=True))
    op.add_column("duty_session", sa.Column("billing_basis", sa.String(length=10), nullable=True))
    op.add_column(
        "duty_session",
        sa.Column("billing_basis_set_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "duty_session",
        sa.Column("billing_basis_set_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "duty_session", sa.Column("billing_basis_note", sa.String(length=200), nullable=True)
    )
    op.create_foreign_key(
        "duty_session_billing_basis_set_by_fkey",
        "duty_session",
        "app_user",
        ["billing_basis_set_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("duty_session_billing_basis_set_by_fkey", "duty_session", type_="foreignkey")
    for column in (
        "billing_basis_note",
        "billing_basis_set_at",
        "billing_basis_set_by",
        "billing_basis",
        "gps_distance_m",
        "odometer_end_km",
        "odometer_start_km",
    ):
        op.drop_column("duty_session", column)
