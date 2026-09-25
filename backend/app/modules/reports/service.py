"""Ratings and the trip report (B18, EMP-07, OPA-05).

Two small features that share a definition: **wait** is the time from the rider asking to
the rider getting in. That is the number this whole product exists to reduce, so it is
measured once, here, and everything else reads it.

The report answers per client and per driver as OPA-05 asks, in JSON or CSV, from the
same computation - a CSV that disagrees with the dashboard is worse than no CSV.
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.domain.state_machines import RequestStatus, StopKind, StopStatus
from app.domain.stats import median, p90
from app.modules.dispatch.models import Trip, TripStop
from app.modules.people.models import Employee
from app.modules.reports.models import TripRating
from app.modules.requests.models import RideRequest

logger = get_logger(__name__)

#: EMP-07: "my last 90 days of trips".
HISTORY_DAYS = 90

CSV_COLUMNS = (
    "request_id",
    "client_id",
    "employee_id",
    "driver_id",
    "vehicle_id",
    "direction",
    "status",
    "requested_time",
    "created_at",
    "picked_up_at",
    "dropped_at",
    "wait_minutes",
)


@dataclass(slots=True)
class TripRow:
    """One request's line in the report."""

    request_id: uuid.UUID
    client_id: uuid.UUID
    employee_id: uuid.UUID
    driver_id: uuid.UUID | None
    vehicle_id: uuid.UUID | None
    direction: str
    status: str
    requested_time: datetime
    created_at: datetime
    picked_up_at: datetime | None
    dropped_at: datetime | None
    wait_minutes: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "client_id": str(self.client_id),
            "employee_id": str(self.employee_id),
            "driver_id": str(self.driver_id) if self.driver_id else None,
            "vehicle_id": str(self.vehicle_id) if self.vehicle_id else None,
            "direction": self.direction,
            "status": self.status,
            "requested_time": self.requested_time.isoformat(),
            "created_at": self.created_at.isoformat(),
            "picked_up_at": self.picked_up_at.isoformat() if self.picked_up_at else None,
            "dropped_at": self.dropped_at.isoformat() if self.dropped_at else None,
            "wait_minutes": round(self.wait_minutes, 1) if self.wait_minutes is not None else None,
        }


@dataclass(slots=True)
class TripReport:
    trips: int = 0
    requests: int = 0
    median_wait_minutes: float | None = None
    p90_wait_minutes: float | None = None
    no_shows: int = 0
    cancellations: int = 0
    rows: list[TripRow] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "trips": self.trips,
            "requests": self.requests,
            "median_wait_minutes": _round(self.median_wait_minutes),
            "p90_wait_minutes": _round(self.p90_wait_minutes),
            "no_shows": self.no_shows,
            "cancellations": self.cancellations,
            "rows": [row.as_dict() for row in self.rows],
        }

    def as_csv(self) -> str:
        """The same rows the JSON carries, so the two can never disagree."""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(CSV_COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in self.rows:
            record = row.as_dict()
            writer.writerow({column: record[column] for column in CSV_COLUMNS})
        return buffer.getvalue()


class ReportService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    # --- ratings (EMP-07) --------------------------------------------------------

    async def rate(
        self,
        operator_id: uuid.UUID,
        request_id: uuid.UUID,
        employee_id: uuid.UUID,
        rating: int,
        comment: str | None = None,
    ) -> TripRating:
        """Rate a finished ride. Once, by the person who took it."""
        if not 1 <= rating <= 5:
            raise ValidationFailed("rating must be between 1 and 5", {"rating": rating})

        request = await self.session.scalar(
            select(RideRequest)
            .where(RideRequest.id == request_id)
            .where(RideRequest.operator_id == operator_id)
        )
        if request is None:
            raise NotFound("Ride request not found")
        if request.employee_id != employee_id:
            # Rating someone else's ride would put words in their mouth.
            raise Forbidden("That ride is not yours to rate")
        if request.status != str(RequestStatus.dropped):
            raise Conflict("A ride can only be rated after it finishes", {"status": request.status})

        existing = await self.session.scalar(
            select(TripRating).where(TripRating.request_id == request_id)
        )
        if existing is not None:
            raise Conflict("This ride has already been rated", {"request_id": str(request_id)})

        row = TripRating(
            request_id=request_id, employee_id=employee_id, rating=rating, comment=comment
        )
        self.session.add(row)
        await self.session.flush()
        logger.info("trip_rated", request_id=str(request_id), rating=rating)
        return row

    async def history(self, operator_id: uuid.UUID, employee_id: uuid.UUID) -> list[TripRow]:
        """EMP-07: the rider's last 90 days, with the wait they actually had."""
        since = self.clock.now() - timedelta(days=HISTORY_DAYS)
        return await self._rows(operator_id, since, self.clock.now(), employee_id=employee_id)

    # --- the operator report (OPA-05) ------------------------------------------------

    async def trip_report(
        self,
        operator_id: uuid.UUID,
        start: date,
        end: date,
        client_id: uuid.UUID | None = None,
    ) -> TripReport:
        """Everything in the window, summarised and itemised.

        The window is inclusive of both dates: an operator asking for 1st to 7th means
        seven days, not six and a bit.
        """
        if end < start:
            raise ValidationFailed(
                "`to` cannot be before `from`", {"from": str(start), "to": str(end)}
            )

        window_start = datetime.combine(start, time.min, tzinfo=self.clock.now().tzinfo)
        window_end = datetime.combine(end, time.max, tzinfo=self.clock.now().tzinfo)
        rows = await self._rows(operator_id, window_start, window_end, client_id=client_id)

        waits = [row.wait_minutes for row in rows if row.wait_minutes is not None]
        report = TripReport(
            trips=len({row.request_id for row in rows if row.picked_up_at is not None}),
            requests=len(rows),
            median_wait_minutes=median(waits),
            p90_wait_minutes=p90(waits),
            no_shows=sum(1 for row in rows if row.status == str(RequestStatus.no_show)),
            cancellations=sum(1 for row in rows if row.status == str(RequestStatus.cancelled)),
            rows=rows,
        )
        logger.info(
            "trip_report",
            operator_id=str(operator_id),
            requests=report.requests,
            trips=report.trips,
        )
        return report

    # --- the shared query ----------------------------------------------------------------

    async def _rows(
        self,
        operator_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        client_id: uuid.UUID | None = None,
        employee_id: uuid.UUID | None = None,
    ) -> list[TripRow]:
        """Requests in the window, with the pickup and drop times their stops recorded."""
        query = (
            select(RideRequest)
            .where(RideRequest.operator_id == operator_id)
            .where(RideRequest.created_at >= window_start)
            .where(RideRequest.created_at <= window_end)
            .order_by(RideRequest.created_at)
        )
        if client_id is not None:
            query = query.where(RideRequest.client_id == client_id)
        if employee_id is not None:
            query = query.where(RideRequest.employee_id == employee_id)
        requests = list((await self.session.execute(query)).scalars().all())
        if not requests:
            return []

        stop_times = await self._stop_times([request.id for request in requests])
        trips = await self._trips({r.trip_id for r in requests if r.trip_id is not None})

        rows: list[TripRow] = []
        for request in requests:
            picked_up, dropped = stop_times.get(request.id, (None, None))
            trip = trips.get(request.trip_id) if request.trip_id else None
            rows.append(
                TripRow(
                    request_id=request.id,
                    client_id=request.client_id,
                    employee_id=request.employee_id,
                    driver_id=trip.driver_id if trip else None,
                    vehicle_id=trip.vehicle_id if trip else None,
                    direction=request.direction,
                    status=request.status,
                    requested_time=request.requested_time,
                    created_at=request.created_at,
                    picked_up_at=picked_up,
                    dropped_at=dropped,
                    wait_minutes=_wait_minutes(request.created_at, picked_up),
                )
            )
        return rows

    async def _stop_times(
        self, request_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[datetime | None, datetime | None]]:
        result = await self.session.execute(
            select(TripStop.request_id, TripStop.stop_type, TripStop.done_at)
            .where(TripStop.request_id.in_(request_ids))
            .where(TripStop.status == str(StopStatus.done))
        )
        times: dict[uuid.UUID, tuple[datetime | None, datetime | None]] = {}
        for request_id, stop_type, done_at in result.all():
            picked_up, dropped = times.get(request_id, (None, None))
            if stop_type == str(StopKind.pickup):
                picked_up = done_at
            else:
                dropped = done_at
            times[request_id] = (picked_up, dropped)
        return times

    async def _trips(self, trip_ids: set[uuid.UUID]) -> dict[uuid.UUID, Trip]:
        if not trip_ids:
            return {}
        result = await self.session.execute(select(Trip).where(Trip.id.in_(trip_ids)))
        return {trip.id: trip for trip in result.scalars().all()}

    async def employee_for_user(
        self, operator_id: uuid.UUID, user_id: uuid.UUID
    ) -> uuid.UUID | None:
        employee_id: uuid.UUID | None = await self.session.scalar(
            select(Employee.id)
            .where(Employee.user_id == user_id)
            .where(Employee.operator_id == operator_id)
        )
        return employee_id


def _wait_minutes(asked_at: datetime, picked_up_at: datetime | None) -> float | None:
    """From asking to getting in. `None` while the ride has not happened.

    Counting an unfinished or cancelled request as a zero-minute wait would flatter every
    average in the product, which is precisely the number the pilot is judged on.
    """
    if picked_up_at is None:
        return None
    return (picked_up_at - asked_at).total_seconds() / 60.0


def _round(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None
