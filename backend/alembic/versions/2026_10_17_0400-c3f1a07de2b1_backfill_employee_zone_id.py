"""backfill employee zone_id from the zone polygons

Revision ID: c3f1a07de2b1
Revises: 9a0667968b8c
Create Date: 2026-10-17 04:00:00.000000

Data only, no schema change. `employee.zone_id` has existed since B07 and been null in
every row since, because nothing derived it. B27 derives it on every write of a home
location - but that only fixes rows written from now on, and an operator who imported
their people last month would see every zone report zero until each employee was
touched again.

A no-op wherever the `zone` table is empty, which is everywhere today. It is here
rather than in a script because an upgrade must not need a second manual step somebody
can forget: the column is wrong until this runs, and nothing complains while it is.

`ST_Covers`, not `ST_Contains`, and smallest zone first - the same two judgement calls
`ZoneService` makes, for the same reasons. If this query and that one ever disagree,
this is the copy to change second.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3f1a07de2b1"
down_revision: str | Sequence[str] | None = "9a0667968b8c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Derive every employee's zone from their home location."""
    op.execute(
        """
        UPDATE employee AS e
        SET zone_id = (
            SELECT z.id
            FROM zone AS z
            WHERE z.operator_id = e.operator_id
              AND z.active
              AND ST_Covers(z.area::geometry, e.home_location::geometry)
            ORDER BY ST_Area(z.area::geography), z.name
            LIMIT 1
        )
        WHERE e.zone_id IS NULL
        """
    )


def downgrade() -> None:
    """Deliberately not reversed.

    Clearing `zone_id` would also erase derivations made by ordinary writes since the
    upgrade, which this migration did not create and has no business destroying. The
    column was nullable before and is nullable after; downgrading loses nothing.
    """
