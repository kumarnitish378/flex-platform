"""Measure a finished trip's distance from the pings its cab sent (B38, B39).

The length itself is `domain/trip_distance.py`; this is the part that reads the pings.
`location_ping` is partitioned by time and indexed by vehicle, so the query is bounded on
both and touches only the partitions the trip's hours fall in.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.trip_distance import Fix, path_length_m
from app.modules.dispatch.models import Trip


async def measure_trip_distance(session: AsyncSession, trip: Trip) -> float | None:
    """Metres the trip's cab moved between the trip starting and finishing.

    `None` when the trip never started or never finished, or when the cab sent no pings in
    that time - which is "not measured", not "drove nowhere": a report that read it as zero
    would flatter cab-km per trip exactly when GPS was lost.
    """
    if trip.started_at is None or trip.completed_at is None:
        return None
    rows = await session.execute(
        text(
            """
            SELECT recorded_at, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng
            FROM location_ping
            WHERE vehicle_id = :vehicle_id
              AND recorded_at >= :started_at
              AND recorded_at <= :completed_at
            ORDER BY recorded_at
            """
        ).bindparams(
            vehicle_id=trip.vehicle_id, started_at=trip.started_at, completed_at=trip.completed_at
        )
    )
    fixes = [Fix(row.recorded_at, row.lat, row.lng) for row in rows]
    if len(fixes) < 2:
        return None
    return path_length_m(fixes)
