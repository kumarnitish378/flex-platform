"""client_policy.employee_opt_out_allowed defaults to true

Revision ID: e4b2c81f90aa
Revises: c3f1a07de2b1
Create Date: 2026-10-17 07:00:00.000000

B28 made this column mean something for the first time: with it false, an employee
asking not to share is refused rather than silently pooled. That is the right
behaviour and the wrong default.

Asking not to share is a behaviour Phase 1 shipped with no gate at all, and
`client_policy` had no API until B28 - so a `false` in this column was never a decision
anybody made. Leaving the default at `false` would revoke a permission every rider
already had, and would mean that creating a policy row to set a detour limit silently
took it away.

Existing rows are flipped too, which is safe for exactly the same reason: the field was
unsettable, so no stored `false` can be deliberate. A client that wants to forbid
opting out now says so through `PUT /admin/clients/{id}/policy`.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e4b2c81f90aa"
down_revision: str | Sequence[str] | None = "c3f1a07de2b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE client_policy SET employee_opt_out_allowed = true")
    op.alter_column(
        "client_policy",
        "employee_opt_out_allowed",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("true"),
    )


def downgrade() -> None:
    op.alter_column(
        "client_policy",
        "employee_opt_out_allowed",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        server_default=sa.text("false"),
    )
