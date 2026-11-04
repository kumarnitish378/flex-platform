"""ride_request pickup_location

Where a vehicle must collect a rider when that is not the usual place for their
direction. Needed because a breakdown can leave a rider who was already on board
standing at the roadside: their re-ride starts there, not at home and not at the
office (ADR-0016, OQ-27).

Revision ID: a1c4de77b210
Revises: 8311e6620dc8
Create Date: 2026-10-02 00:00:00.000000

"""

from collections.abc import Sequence

import geoalchemy2  # noqa: F401  (geography columns render as geoalchemy2.types.*)
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1c4de77b210"
down_revision: str | Sequence[str] | None = "8311e6620dc8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ride_request",
        sa.Column(
            "pickup_location",
            geoalchemy2.types.Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                from_text="ST_GeogFromText",
                name="geography",
                nullable=True,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ride_request", "pickup_location")
