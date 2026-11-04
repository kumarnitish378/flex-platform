"""The per-client monthly billing export: one row per cab per day (B38, OPA-06).

**The basis is decided (owner, 2026-11-02; OQ-03).** The employer company pays the operator *per
cab per day* on the total running kilometres between duty start (cab in) and duty end (cab out),
dead kilometres between trips included, at the operator's `billing_rate_per_km` (Rs 8 to begin
with). This replaces the earlier per-ride, per-trip-share export. Riders never pay and nothing here
is addressed to them.

A row is one cab on one local day (operator timezone, by the day its duty started - a night duty
that runs past midnight belongs to the day it began). Its kilometres come from the GPS pings between
going on and off duty (`domain/cab_day_billing.py`); the odometer readings a driver may enter are a
cross-check, flagged when they disagree by more than `billing_odometer_gap_percent`, and are billed
only when an operator admin marks that session's odometer figure.

**Which client is billed.** A cab's day is billed to the client whose riders it carried. When it
carried more than one client's riders - or none - the row goes to the operator's default client
(`billing_default_client_id`; with a single client that is the client) and is flagged
`multiple_clients` / `no_client_trips`. How to split a shared cab-day is an open question (OQ-40).
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.domain.cab_day_billing import (
    Basis,
    CabDay,
    Flag,
    SessionFacts,
    build_cab_day,
)
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.state_machines import RequestStatus, TripStatus
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip
from app.modules.dispatch.trip_distance import measure_distance
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Client, Operator

COLUMNS = (
    "date",
    "cab",
    "drivers",
    "duty_in",
    "duty_out",
    "gps_km",
    "odometer_km",
    "gap_percent",
    "billed_km",
    "rate_per_km",
    "amount",
    "flags",
)

#: Requests that were really in the cab.
CARRIED = (RequestStatus.assigned, RequestStatus.picked_up, RequestStatus.dropped)
#: Trips that happened (or are happening).
REAL_TRIPS = (TripStatus.in_progress, TripStatus.completed)


@dataclass(slots=True)
class BillingRow:
    day: date
    cab: CabDay
    client_id: uuid.UUID
    rate_per_km: float | None

    def as_dict(self) -> dict[str, Any]:
        cab = self.cab
        return {
            "date": self.day.isoformat(),
            "cab": cab.vehicle,
            "drivers": list(cab.drivers),
            "duty_in": cab.duty_in.isoformat(),
            "duty_out": cab.duty_out.isoformat() if cab.duty_out else None,
            "gps_km": _round(cab.gps_km),
            "odometer_km": _round(cab.odometer_km),
            "gap_percent": _round(cab.gap_percent, 1),
            "billed_km": _round(cab.billed_km),
            "rate_per_km": self.rate_per_km,
            "amount": cab.amount,
            "flags": [str(flag) for flag in cab.flags],
            "sessions": [
                {
                    "id": s.session_id,
                    "driver": s.driver,
                    "duty_in": s.started_at.isoformat(),
                    "duty_out": s.ended_at.isoformat() if s.ended_at else None,
                    "gps_km": _round(s.gps_km),
                    "odometer_start_km": s.odometer_start_km,
                    "odometer_end_km": s.odometer_end_km,
                    "odometer_km": _round(s.odometer_km),
                    "basis": str(s.basis),
                }
                for s in cab.sessions
            ],
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
        """One line per cab per day, the same rows the JSON carries, then the month's total."""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in self.rows:
            record = row.as_dict()
            record["drivers"] = "; ".join(record["drivers"])
            record["flags"] = "; ".join(record["flags"])
            writer.writerow(
                {column: "" if record[column] is None else record[column] for column in COLUMNS}
            )
        total = self.summary
        writer.writerow(
            {
                "date": "TOTAL",
                "cab": f"{total['cab_days']} cab-days",
                "gps_km": "" if total["gps_km"] is None else total["gps_km"],
                "odometer_km": "" if total["odometer_km"] is None else total["odometer_km"],
                "billed_km": total["billed_km"],
                "rate_per_km": self.treatment["rate_per_km"] or "",
                "amount": "" if total["amount"] is None else total["amount"],
                "flags": f"{total['flagged_days']} flagged",
            }
        )
        return buffer.getvalue()


class BillingService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    async def export(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, month: str
    ) -> BillingExport:
        timezone = await self._timezone(operator_id)
        start, end = _month_bounds(month, timezone)
        client = await self.session.scalar(
            select(Client).where(Client.id == client_id).where(Client.operator_id == operator_id)
        )
        if client is None:
            raise NotFound("Client not found")

        settings = await ConfigService(self.session, self.clock).all_values(operator_id)
        rate = float(settings["billing_rate_per_km"]) or None
        threshold = float(settings["billing_odometer_gap_percent"])
        default_client, default_unset = await self._default_client(
            operator_id, str(settings["billing_default_client_id"])
        )
        zone = ZoneInfo(timezone)
        now = self.clock.now()

        groups: dict[tuple[uuid.UUID, date], list[SessionFacts]] = defaultdict(list)
        plates: dict[uuid.UUID, str] = {}
        windows: dict[tuple[uuid.UUID, date], tuple[datetime, datetime]] = {}
        for duty, plate, driver_name in await self._sessions(operator_id, start, end):
            key = (duty.vehicle_id, duty.started_at.astimezone(zone).date())
            groups[key].append(await self._facts(duty, driver_name))
            plates[duty.vehicle_id] = plate
            low, high = windows.get(key, (duty.started_at, duty.ended_at or now))
            windows[key] = (min(low, duty.started_at), max(high, duty.ended_at or now))

        clients_by_trip = await self._clients_by_trip(operator_id, start, end)
        trips = await self._trips(operator_id, start, end)

        rows: list[BillingRow] = []
        for (vehicle_id, day), facts in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            low, high = windows[(vehicle_id, day)]
            served: set[uuid.UUID] = set()
            for trip in trips:
                if (
                    trip.vehicle_id == vehicle_id
                    and trip.started_at is not None
                    and low <= trip.started_at <= high
                ):
                    served |= clients_by_trip.get(trip.id, set())
            extra: list[Flag] = []
            if len(served) == 1:
                billed_to = next(iter(served))
            else:
                billed_to = default_client
                extra.append(Flag.multiple_clients if served else Flag.no_client_trips)
                if default_unset:
                    extra.append(Flag.default_client_unset)
            if billed_to != client_id:
                continue
            cab = build_cab_day(
                vehicle=plates[vehicle_id],
                day=day.isoformat(),
                sessions=facts,
                threshold_percent=threshold,
                rate_per_km=rate,
                extra_flags=extra,
            )
            rows.append(BillingRow(day, cab, client_id, rate))

        export = BillingExport(
            client_id,
            client.name,
            month,
            {
                "basis": "per_cab_per_day_km",
                "rate_per_km": rate,
                "odometer_gap_threshold_percent": threshold,
                "default_client_id": str(default_client),
            },
            {},
            rows,
        )
        export.summary = _summary(rows)
        return export

    async def set_basis(
        self,
        operator_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        basis: str,
        note: str | None,
    ) -> DutySession:
        """An operator admin chooses which figure a duty session is billed on."""
        try:
            chosen = Basis(basis)
        except ValueError:
            raise ValidationFailed("basis must be gps or odometer", {"basis": basis}) from None
        duty = await self.session.scalar(
            select(DutySession)
            .where(DutySession.id == session_id)
            .where(DutySession.operator_id == operator_id)
        )
        if duty is None:
            raise NotFound("Duty session not found")
        if chosen is Basis.odometer and (
            duty.odometer_start_km is None
            or duty.odometer_end_km is None
            or duty.odometer_end_km < duty.odometer_start_km
        ):
            raise Conflict(
                "Both odometer readings are needed to bill on the odometer",
                {"session_id": str(session_id)},
            )
        duty.billing_basis = str(chosen)
        duty.billing_basis_set_by = user_id
        duty.billing_basis_set_at = self.clock.now()
        duty.billing_basis_note = note
        await self.session.flush()
        return duty

    # --- queries -------------------------------------------------------------------------

    async def _timezone(self, operator_id: uuid.UUID) -> str:
        zone = await self.session.scalar(
            select(Operator.timezone).where(Operator.id == operator_id)
        )
        return zone or "UTC"

    async def _sessions(
        self, operator_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[tuple[DutySession, str, str]]:
        rows = await self.session.execute(
            select(DutySession, Vehicle.registration_no, Driver.name)
            .join(Vehicle, Vehicle.id == DutySession.vehicle_id)
            .join(Driver, Driver.id == DutySession.driver_id)
            .where(DutySession.operator_id == operator_id)
            .where(DutySession.started_at >= start)
            .where(DutySession.started_at < end)
            .order_by(DutySession.started_at)
        )
        return [(duty, str(plate), str(name)) for duty, plate, name in rows]

    async def _facts(self, duty: DutySession, driver: str) -> SessionFacts:
        """The session as billing sees it. A closed session's distance was fixed when it closed;
        an open one (or one from before that was recorded) is measured now."""
        metres = duty.gps_distance_m
        if metres is None:
            metres = await measure_distance(
                self.session, duty.vehicle_id, duty.started_at, duty.ended_at or self.clock.now()
            )
        return SessionFacts(
            session_id=str(duty.id),
            driver=driver,
            started_at=duty.started_at,
            ended_at=duty.ended_at,
            gps_km=None if metres is None else metres / 1000.0,
            odometer_start_km=duty.odometer_start_km,
            odometer_end_km=duty.odometer_end_km,
            basis=Basis(duty.billing_basis) if duty.billing_basis else Basis.gps,
        )

    async def _trips(self, operator_id: uuid.UUID, start: datetime, end: datetime) -> list[Trip]:
        rows = await self.session.execute(
            select(Trip)
            .where(Trip.operator_id == operator_id)
            .where(Trip.status.in_([str(status) for status in REAL_TRIPS]))
            .where(Trip.started_at >= start)
            .where(Trip.started_at < end)
        )
        return list(rows.scalars())

    async def _clients_by_trip(
        self, operator_id: uuid.UUID, start: datetime, end: datetime
    ) -> dict[uuid.UUID, set[uuid.UUID]]:
        """Whose riders each trip carried."""
        rows = await self.session.execute(
            select(RideRequest.trip_id, RideRequest.client_id)
            .join(Trip, Trip.id == RideRequest.trip_id)
            .where(Trip.operator_id == operator_id)
            .where(Trip.started_at >= start)
            .where(Trip.started_at < end)
            .where(RideRequest.status.in_([str(status) for status in CARRIED]))
        )
        found: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
        for trip_id, client in rows:
            found[trip_id].add(client)
        return found

    async def _default_client(
        self, operator_id: uuid.UUID, configured: str
    ) -> tuple[uuid.UUID, bool]:
        """The client a shared or empty cab-day is billed to, and whether it was a guess.

        Configured when the operator said so. With exactly one client there is nothing to guess.
        With several and none configured, the oldest is used and every such row says so.
        """
        clients = list(
            (
                await self.session.execute(
                    select(Client.id)
                    .where(Client.operator_id == operator_id)
                    .order_by(Client.created_at, Client.id)
                )
            ).scalars()
        )
        if not clients:
            raise NotFound("The operator has no clients")
        if configured:
            try:
                chosen = uuid.UUID(configured)
            except ValueError:
                chosen = None
            if chosen is not None and chosen in clients:
                return chosen, False
        return clients[0], len(clients) > 1


def _summary(rows: list[BillingRow]) -> dict[str, Any]:
    gps = [row.cab.gps_km for row in rows if row.cab.gps_km is not None]
    odo = [row.cab.odometer_km for row in rows if row.cab.odometer_km is not None]
    amounts = [row.cab.amount for row in rows if row.cab.amount is not None]
    return {
        "cab_days": len(rows),
        "cabs": len({row.cab.vehicle for row in rows}),
        "gps_km": _round(sum(gps)) if gps else None,
        "odometer_km": _round(sum(odo)) if odo else None,
        "billed_km": _round(sum(row.cab.billed_km for row in rows)),
        # Kilometres x the operator's rate; `None` until a rate is set - never a guessed price.
        "amount": _round(sum(amounts), 2) if amounts else None,
        "flagged_days": sum(1 for row in rows if row.cab.flags),
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
