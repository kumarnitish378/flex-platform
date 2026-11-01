"""The per-client monthly billing export (B38, OPA-06).

> **OPA-06 · Billing export** · Phase 3 - per client, per period: trips, km, invoice-ready CSV.

**The basis is decided (owner, 2026-11-01; OQ-03): the operator bills the client company per
kilometre.** Riders never pay, so nothing here is addressed to an employee and no employee-facing
response carries a charge. The export gives a client's month as **kilometres** - each traceable to
the rows it came from - with rides, trips and riders alongside as information only (a trip count is
not a billing basis). `billing_rate_per_km` (operator config, `0` = not set) turns kilometres into
an `amount`; the rate is the operator's own and is not defaulted. Three treatments an invoice would
otherwise have to guess at stay config keys, still provisional because OQ-01 is open:

* `billing_no_show_billable` (default **true**): a cab was sent and the rider was not there;
* `billing_late_cancel_billable` (default **false**): the rider cancelled after a cab had
  been assigned; a request cancelled while still queued costs nothing and is never billable;
* `billing_distance_basis` (default **`trip_share`**): `trip_share` bills each rider their
  equal share of the kilometres the cab actually drove, so the shares of a trip add up to the
  trip's measured distance and the invoice reconciles with the `trip` rows; `direct` bills
  the rider's own journey (great-circle x road factor) regardless of pooling.

The two cancellation defaults are **mine, provisional, and listed for the owner**
(`decision-log.md`): nothing in the repository says how the pilot operator treats a no-show or a
late cancel.

A month is the operator's calendar month in their own timezone, by when the rider asked.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.geo import coords
from app.domain.errors import NotFound, ValidationFailed
from app.domain.geo import LatLng, haversine_km
from app.domain.state_machines import RequestStatus, StopKind, StopStatus
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip, TripStop
from app.modules.fleet.models import Vehicle
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Client, Office, Operator

#: Matches `approx`'s road factor (`control-model.md` section 6).
ROAD_FACTOR = 1.4

COLUMNS = (
    "date",
    "request_id",
    "employee",
    "direction",
    "status",
    "billable",
    "billable_reason",
    "trip_id",
    "vehicle",
    "riders_on_trip",
    "direct_km",
    "trip_share_km",
    "billable_km",
)


@dataclass(slots=True)
class BillingRow:
    day: date
    request_id: uuid.UUID
    employee: str
    direction: str
    status: str
    billable: bool
    billable_reason: str
    trip_id: uuid.UUID | None
    vehicle: str | None
    riders_on_trip: int
    direct_km: float | None
    trip_share_km: float | None
    billable_km: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "date": self.day.isoformat(),
            "request_id": str(self.request_id),
            "employee": self.employee,
            "direction": self.direction,
            "status": self.status,
            "billable": self.billable,
            "billable_reason": self.billable_reason,
            "trip_id": str(self.trip_id) if self.trip_id else None,
            "vehicle": self.vehicle,
            "riders_on_trip": self.riders_on_trip,
            "direct_km": _round(self.direct_km),
            "trip_share_km": _round(self.trip_share_km),
            "billable_km": _round(self.billable_km),
        }


@dataclass(slots=True)
class BillingExport:
    client_id: uuid.UUID
    client_name: str
    month: str
    treatment: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    rows: list[BillingRow] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "client_id": str(self.client_id),
            "client_name": self.client_name,
            "month": self.month,
            "treatment": self.treatment,
            "summary": self.summary,
            "rows": [row.as_dict() for row in self.rows],
        }

    def as_csv(self) -> str:
        """One line per ride, the same rows the JSON carries."""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in self.rows:
            record = row.as_dict()
            writer.writerow(
                {column: "" if record[column] is None else record[column] for column in COLUMNS}
            )
        return buffer.getvalue()


class BillingService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    async def export(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, month: str
    ) -> BillingExport:
        start, end = _month_bounds(month, await self._timezone(operator_id))
        client = await self.session.scalar(
            select(Client).where(Client.id == client_id).where(Client.operator_id == operator_id)
        )
        if client is None:
            raise NotFound("Client not found")

        settings = await ConfigService(self.session, self.clock).all_values(operator_id)
        treatment = {
            "no_show_billable": bool(settings["billing_no_show_billable"]),
            "late_cancel_billable": bool(settings["billing_late_cancel_billable"]),
            "distance_basis": str(settings["billing_distance_basis"]),
            # The unit the client is billed in. Fixed, not configurable: per kilometre.
            "basis": "per_km",
            "rate_per_km": float(settings["billing_rate_per_km"]) or None,
        }

        requests = list(
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.operator_id == operator_id)
                    .where(RideRequest.client_id == client_id)
                    .where(RideRequest.queued_at >= start)
                    .where(RideRequest.queued_at < end)
                    .order_by(RideRequest.queued_at, RideRequest.id)
                )
            ).scalars()
        )
        trips = await self._trips({r.trip_id for r in requests if r.trip_id})
        carried = await self._carried(list(trips))
        vehicles = await self._vehicles({trip.vehicle_id for trip in trips.values()})
        names = await self._employees({r.employee_id for r in requests})
        offices = await self._offices({r.office_id for r in requests})
        assigned_then_cancelled = await self._assigned_before_cancel(
            [r.id for r in requests if r.status == str(RequestStatus.cancelled)]
        )
        zone = ZoneInfo(await self._timezone(operator_id))

        rows: list[BillingRow] = []
        for request in requests:
            trip = trips.get(request.trip_id) if request.trip_id else None
            shared_by = max(carried.get(trip.id, 0), 1) if trip else 1
            trip_share = (
                trip.actual_distance_m / 1000.0 / shared_by
                if trip and trip.actual_distance_m is not None
                else None
            )
            direct = _direct_km(request, offices.get(request.office_id))
            billable, why = _billable(
                request, treatment, was_assigned=request.id in assigned_then_cancelled
            )
            chosen = (trip_share if treatment["distance_basis"] == "trip_share" else direct) or 0.0
            rows.append(
                BillingRow(
                    day=request.queued_at.astimezone(zone).date(),
                    request_id=request.id,
                    employee=names.get(request.employee_id, ""),
                    direction=str(request.direction),
                    status=str(request.status),
                    billable=billable,
                    billable_reason=why,
                    trip_id=trip.id if trip else None,
                    vehicle=vehicles.get(trip.vehicle_id) if trip else None,
                    riders_on_trip=shared_by if trip else 0,
                    direct_km=direct,
                    trip_share_km=trip_share,
                    billable_km=chosen if billable else 0.0,
                )
            )

        export = BillingExport(client_id, client.name, month, treatment, {}, rows)
        export.summary = _summary(rows, float(settings["billing_rate_per_km"]) or None)
        return export

    # --- queries -------------------------------------------------------------------------

    async def _timezone(self, operator_id: uuid.UUID) -> str:
        zone = await self.session.scalar(
            select(Operator.timezone).where(Operator.id == operator_id)
        )
        return zone or "UTC"

    async def _trips(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, Trip]:
        if not ids:
            return {}
        rows = await self.session.execute(select(Trip).where(Trip.id.in_(ids)))
        return {trip.id: trip for trip in rows.scalars()}

    async def _carried(self, trip_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Riders who really got in, per trip, across **all** clients: the cab's km are shared
        by everyone it carried, whoever's invoice they are on."""
        if not trip_ids:
            return {}
        rows = await self.session.execute(
            select(TripStop.trip_id, TripStop.request_id)
            .where(TripStop.trip_id.in_(trip_ids))
            .where(TripStop.stop_type == str(StopKind.pickup))
            .where(TripStop.status == str(StopStatus.done))
        )
        found: dict[uuid.UUID, set[uuid.UUID]] = {}
        for trip_id, request_id in rows:
            found.setdefault(trip_id, set()).add(request_id)
        return {trip_id: len(requests) for trip_id, requests in found.items()}

    async def _vehicles(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(Vehicle.id, Vehicle.registration_no).where(Vehicle.id.in_(ids))
        )
        return {row[0]: row[1] for row in rows}

    async def _employees(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not ids:
            return {}
        rows = await self.session.execute(
            select(Employee.id, Employee.name).where(Employee.id.in_(ids))
        )
        return {row[0]: row[1] for row in rows}

    async def _offices(self, ids: set[uuid.UUID]) -> dict[uuid.UUID, Office]:
        if not ids:
            return {}
        rows = await self.session.execute(select(Office).where(Office.id.in_(ids)))
        return {office.id: office for office in rows.scalars()}

    async def _assigned_before_cancel(self, cancelled: list[uuid.UUID]) -> set[uuid.UUID]:
        """Cancelled requests that had a cab assigned at some point (a late cancellation)."""
        if not cancelled:
            return set()
        from app.modules.requests.models import RideRequestEvent

        rows = await self.session.execute(
            select(RideRequestEvent.request_id)
            .where(RideRequestEvent.request_id.in_(cancelled))
            .where(RideRequestEvent.to_status == str(RequestStatus.assigned))
        )
        return set(rows.scalars())


# --- the rules, pure -----------------------------------------------------------------------


def _billable(
    request: RideRequest, treatment: dict[str, Any], *, was_assigned: bool
) -> tuple[bool, str]:
    """Is this ride on the invoice, and why (or why not)."""
    status = request.status
    if status == str(RequestStatus.dropped):
        return True, "completed"
    if status == str(RequestStatus.no_show):
        return (
            bool(treatment["no_show_billable"]),
            "no_show_billed" if treatment["no_show_billable"] else "no_show_not_billed",
        )
    if status == str(RequestStatus.cancelled):
        if not was_assigned:
            return False, "cancelled_before_assignment"
        return (
            bool(treatment["late_cancel_billable"]),
            "late_cancel_billed" if treatment["late_cancel_billable"] else "late_cancel_not_billed",
        )
    if status == str(RequestStatus.expired):
        return False, "expired_unserved"
    return False, "not_finished"


def _direct_km(request: RideRequest, office: Office | None) -> float | None:
    """The rider's own journey: great-circle x road factor, between where they are collected
    and where they are dropped."""
    if office is None:
        return None
    home = LatLng(*coords(request.pickup_location or request.location))
    there = LatLng(*coords(office.location))
    return haversine_km(home, there) * ROAD_FACTOR


def _summary(rows: list[BillingRow], rate_per_km: float | None = None) -> dict[str, Any]:
    billable = [row for row in rows if row.billable]
    trips = {row.trip_id for row in billable if row.trip_id}
    return {
        "rides": len(rows),
        "billable_rides": len(billable),
        "completed": sum(1 for r in rows if r.billable_reason == "completed"),
        "no_shows": sum(1 for r in rows if r.status == str(RequestStatus.no_show)),
        "cancellations": sum(1 for r in rows if r.status == str(RequestStatus.cancelled)),
        "billable_trips": len(trips),
        "riders": len({row.employee for row in billable}),
        "billable_km": _round(sum(row.billable_km for row in billable)),
        # Kilometres x the operator's rate; `None` until a rate is set - never a guessed price.
        "amount": (
            _round(sum(row.billable_km for row in billable) * rate_per_km, 2)
            if rate_per_km
            else None
        ),
    }


def _month_bounds(month: str, timezone: str) -> tuple[datetime, datetime]:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month or ""):
        raise ValidationFailed("month must look like 2026-10", {"month": month})
    try:
        year_text, month_text = month.split("-")
        year, number = int(year_text), int(month_text)
        first = datetime(year, number, 1, tzinfo=ZoneInfo(timezone))
    except (ValueError, TypeError) as exc:
        raise ValidationFailed("month must look like 2026-10", {"month": month}) from exc
    following = (
        datetime(year + 1, 1, 1, tzinfo=ZoneInfo(timezone))
        if number == 12
        else datetime(year, number + 1, 1, tzinfo=ZoneInfo(timezone))
    )
    return first, following


def _round(value: float | None, digits: int = 3) -> float | None:
    return None if value is None else round(value, digits)
