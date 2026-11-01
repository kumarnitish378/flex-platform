"""The full operator report (B39, OPA-05 "Phase 3 full").

Phase 1's report answered "how long did people wait". Phase 3 has to answer the questions
the phase exists to move, from the records the platform already keeps:

* **wait distribution** - the shape, not just the median and p90;
* **pooling** - how many trips carried more than one rider, and riders per trip;
* **cab-km per trip** and **vehicles used** - from what the cabs drove (`trip.actual_distance_m`,
  measured from their pings at completion), never from what dispatch planned;
* **overrides by reason** - how often a human stepped in, and why (`override_log`);
* **suggestion acceptance** - what OQ-39 asks for, with its definition stated rather than
  assumed;
* **who assigned** - supervisor, failsafe or optimizer (B34).

One computation feeds JSON and CSV, so the two cannot disagree.

**Acceptance (OQ-39).** The Phase 2 exit criterion is "suggestion acceptance > 70%" and the
open question is what it is measured over. This report does not pick: it counts only the
system's *first choice* (rank 1) that a person or the failsafe settled in the period, never
counts a `failsafe_assigned` as an acceptance (nobody agreed to it) and never counts a
`superseded` offer as a verdict (the world moved), and reports both readings the open
question names - `acceptance_rate` (an approval) and `acceptance_rate_with_alternatives`
(an approval, or a rejection in favour of a cab the system had also offered). Until OQ-39 is
answered, quote neither without saying which.
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.domain.errors import ValidationFailed
from app.domain.failsafe import SuggestionStatus
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, TripStatus
from app.domain.stats import median, p90
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.optimizer_models import OptimizerRun
from app.modules.dispatch.override_models import OverrideLog
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.reports.service import ReportService, TripRow
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Operator

#: Wait buckets in minutes, lower bound inclusive. The last is open-ended.
WAIT_BUCKETS = ((0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 45), (45, 60), (60, None))


def _label(low: int, high: int | None) -> str:
    return f"{low}+" if high is None else f"{low}-{high}"


@dataclass(slots=True)
class OperationsReport:
    start: date
    end: date
    requests: dict[str, int] = field(default_factory=dict)
    wait: dict[str, Any] = field(default_factory=dict)
    pooling: dict[str, Any] = field(default_factory=dict)
    distance: dict[str, Any] = field(default_factory=dict)
    overrides: dict[str, Any] = field(default_factory=dict)
    suggestions: dict[str, Any] = field(default_factory=dict)
    assignments: dict[str, int] = field(default_factory=dict)
    optimizer: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "period": {"from": self.start.isoformat(), "to": self.end.isoformat()},
            "requests": self.requests,
            "wait": self.wait,
            "pooling": self.pooling,
            "distance": self.distance,
            "overrides": self.overrides,
            "suggestions": self.suggestions,
            "assignments_by_actor": self.assignments,
            "optimizer": self.optimizer,
        }

    def as_csv(self) -> str:
        """`section,metric,value` - flat on purpose, so it opens in a spreadsheet unedited."""
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["section", "metric", "value"])
        for section, content in self.as_dict().items():
            if section == "period":
                continue
            for key, value in _flatten(content):
                writer.writerow([section, key, "" if value is None else value])
        return buffer.getvalue()


def _flatten(content: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(content, dict):
        flat: list[tuple[str, Any]] = []
        for key, value in content.items():
            flat.extend(_flatten(value, f"{prefix}{key}."))
        return flat
    return [(prefix.rstrip("."), content)]


class OperationsReportService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    async def report(
        self,
        operator_id: uuid.UUID,
        start: date,
        end: date,
        client_id: uuid.UUID | None = None,
    ) -> OperationsReport:
        if end < start:
            raise ValidationFailed(
                "`to` cannot be before `from`", {"from": str(start), "to": str(end)}
            )
        zone = ZoneInfo(await self._timezone(operator_id))
        window_start = datetime.combine(start, time.min, tzinfo=zone)
        window_end = datetime.combine(end + timedelta(days=1), time.min, tzinfo=zone)

        rows = await ReportService(self.session, self.clock)._rows(  # noqa: SLF001 - one definition of wait
            operator_id, window_start, window_end - timedelta(microseconds=1), client_id=client_id
        )
        trips = await self._trips(operator_id, window_start, window_end, client_id)
        boarded = await self._boarded(list(trips))

        report = OperationsReport(start=start, end=end)
        report.requests = _request_counts(rows)
        report.wait = _wait(rows)
        report.pooling, report.distance = _trip_figures(trips, boarded)
        report.overrides = await self._overrides(operator_id, window_start, window_end, client_id)
        report.suggestions = await self._suggestions(
            operator_id, window_start, window_end, client_id
        )
        report.assignments = _assignments(rows)
        report.optimizer = await self._optimizer(operator_id, window_start, window_end)
        return report

    # --- queries -------------------------------------------------------------------------

    async def _timezone(self, operator_id: uuid.UUID) -> str:
        zone = await self.session.scalar(
            select(Operator.timezone).where(Operator.id == operator_id)
        )
        return zone or "UTC"

    async def _trips(
        self,
        operator_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        client_id: uuid.UUID | None,
    ) -> dict[uuid.UUID, Trip]:
        query = (
            select(Trip)
            .where(Trip.operator_id == operator_id)
            .where(Trip.status == str(TripStatus.completed))
            .where(Trip.completed_at >= window_start)
            .where(Trip.completed_at < window_end)
        )
        trips = {trip.id: trip for trip in (await self.session.execute(query)).scalars()}
        if client_id is None or not trips:
            return trips
        # A trip belongs to a client's report if any of its riders is theirs.
        mine = set(
            (
                await self.session.execute(
                    select(RideRequest.trip_id)
                    .where(RideRequest.trip_id.in_(list(trips)))
                    .where(RideRequest.client_id == client_id)
                )
            ).scalars()
        )
        return {trip_id: trip for trip_id, trip in trips.items() if trip_id in mine}

    async def _boarded(self, trip_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        """Riders who actually got in, per trip: completed pickup stops, not listed ones."""
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

    async def _overrides(
        self,
        operator_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        client_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        query = (
            select(OverrideLog)
            .where(OverrideLog.operator_id == operator_id)
            .where(OverrideLog.at >= window_start)
            .where(OverrideLog.at < window_end)
        )
        logs = list((await self.session.execute(query)).scalars())
        if client_id is not None:
            ids = {log.request_id for log in logs if log.request_id}
            mine = (
                set(
                    (
                        await self.session.execute(
                            select(RideRequest.id)
                            .where(RideRequest.id.in_(ids))
                            .where(RideRequest.client_id == client_id)
                        )
                    ).scalars()
                )
                if ids
                else set()
            )
            logs = [log for log in logs if log.request_id in mine]
        by_reason: dict[str, int] = {}
        by_action: dict[str, int] = {}
        for log in logs:
            by_reason[str(log.reason_code)] = by_reason.get(str(log.reason_code), 0) + 1
            by_action[str(log.action)] = by_action.get(str(log.action), 0) + 1
        return {
            "total": len(logs),
            "hard_rule_overrides": sum(1 for log in logs if log.waived_violations),
            "by_reason": dict(sorted(by_reason.items())),
            "by_action": dict(sorted(by_action.items())),
        }

    async def _suggestions(
        self,
        operator_id: uuid.UUID,
        window_start: datetime,
        window_end: datetime,
        client_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        query = (
            select(Suggestion)
            .where(Suggestion.operator_id == operator_id)
            .where(Suggestion.rank == 1)
            .where(Suggestion.decided_at >= window_start)
            .where(Suggestion.decided_at < window_end)
            .where(
                Suggestion.status.in_(
                    [
                        str(SuggestionStatus.accepted),
                        str(SuggestionStatus.rejected),
                        str(SuggestionStatus.failsafe_assigned),
                    ]
                )
            )
        )
        decided = list((await self.session.execute(query)).scalars())
        request_ids = {item.request_id for item in decided}
        requests: dict[uuid.UUID, RideRequest] = {}
        if request_ids:
            requests = {
                r.id: r
                for r in (
                    await self.session.execute(
                        select(RideRequest).where(RideRequest.id.in_(request_ids))
                    )
                ).scalars()
            }
        if client_id is not None:
            decided = [
                item
                for item in decided
                if requests.get(item.request_id)
                and requests[item.request_id].client_id == client_id
            ]

        accepted = sum(1 for s in decided if s.status == str(SuggestionStatus.accepted))
        rejected = [s for s in decided if s.status == str(SuggestionStatus.rejected)]
        failsafe = sum(1 for s in decided if s.status == str(SuggestionStatus.failsafe_assigned))

        alternatives = 0
        if rejected:
            alternatives = await self._chose_an_offered_alternative(rejected, requests)

        answered = accepted + len(rejected)
        return {
            "answered_by_a_person": answered,
            "accepted": accepted,
            "rejected": len(rejected),
            "failsafe_assigned": failsafe,
            "rejected_for_an_offered_alternative": alternatives,
            "acceptance_rate": _rate(accepted, answered),
            "acceptance_rate_with_alternatives": _rate(accepted + alternatives, answered),
        }

    async def _chose_an_offered_alternative(
        self, rejected: list[Suggestion], requests: dict[uuid.UUID, RideRequest]
    ) -> int:
        """Rejections where the supervisor sent a cab the system had also offered (rank 2-3)."""
        request_ids = [item.request_id for item in rejected]
        siblings: dict[uuid.UUID, set[uuid.UUID]] = {}
        rows = await self.session.execute(
            select(Suggestion.request_id, Suggestion.vehicle_id)
            .where(Suggestion.request_id.in_(request_ids))
            .where(Suggestion.rank > 1)
        )
        for request_id, vehicle_id in rows:
            siblings.setdefault(request_id, set()).add(vehicle_id)
        trip_ids = {r.trip_id for r in requests.values() if r.trip_id}
        vehicles: dict[uuid.UUID, uuid.UUID] = {}
        if trip_ids:
            vehicles = {
                row[0]: row[1]
                for row in await self.session.execute(
                    select(Trip.id, Trip.vehicle_id).where(Trip.id.in_(trip_ids))
                )
            }
        count = 0
        for item in rejected:
            request = requests.get(item.request_id)
            if request is None or request.trip_id is None:
                continue
            if vehicles.get(request.trip_id) in siblings.get(item.request_id, set()):
                count += 1
        return count

    async def _optimizer(
        self, operator_id: uuid.UUID, window_start: datetime, window_end: datetime
    ) -> dict[str, Any]:
        runs = list(
            (
                await self.session.execute(
                    select(OptimizerRun)
                    .where(OptimizerRun.operator_id == operator_id)
                    .where(OptimizerRun.started_at >= window_start)
                    .where(OptimizerRun.started_at < window_end)
                )
            ).scalars()
        )
        return {
            "runs": len(runs),
            "failed": sum(1 for run in runs if run.status == "failed"),
            "applied": sum(run.applied for run in runs),
            "suggested": sum(run.suggested for run in runs),
            "hinted": sum(run.hinted for run in runs),
        }


# --- pure aggregation (so each number can be reproduced from a fixture by hand) ---------------


def _rate(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else round(numerator / denominator, 4)


def _request_counts(rows: list[TripRow]) -> dict[str, int]:
    counts = {
        "total": len(rows),
        "completed": 0,
        "no_shows": 0,
        "cancelled": 0,
        "expired": 0,
        "still_open": 0,
    }
    for row in rows:
        if row.status == str(RequestStatus.dropped):
            counts["completed"] += 1
        elif row.status == str(RequestStatus.no_show):
            counts["no_shows"] += 1
        elif row.status == str(RequestStatus.cancelled):
            counts["cancelled"] += 1
        elif row.status == str(RequestStatus.expired):
            counts["expired"] += 1
        else:
            counts["still_open"] += 1
    return counts


def _wait(rows: list[TripRow]) -> dict[str, Any]:
    waits = [row.wait_minutes for row in rows if row.wait_minutes is not None]
    distribution = {_label(low, high): 0 for low, high in WAIT_BUCKETS}
    for minutes in waits:
        for low, high in WAIT_BUCKETS:
            if minutes >= low and (high is None or minutes < high):
                distribution[_label(low, high)] += 1
                break
    return {
        "measured": len(waits),
        "median_minutes": _round(median(waits)),
        "p90_minutes": _round(p90(waits)),
        "distribution": distribution,
    }


def _trip_figures(
    trips: dict[uuid.UUID, Trip], boarded: dict[uuid.UUID, int]
) -> tuple[dict[str, Any], dict[str, Any]]:
    carrying = {
        trip_id: count for trip_id, count in boarded.items() if count > 0 and trip_id in trips
    }
    riders = sum(carrying.values())
    pooled = sum(1 for count in carrying.values() if count >= 2)
    vehicles = {trips[trip_id].vehicle_id for trip_id in carrying}

    measured = [
        trips[trip_id].actual_distance_m
        for trip_id in carrying
        if trips[trip_id].actual_distance_m is not None
    ]
    km = [metres / 1000.0 for metres in measured if metres is not None]
    pooling = {
        "trips": len(carrying),
        "riders_carried": riders,
        "riders_per_trip": _round(riders / len(carrying)) if carrying else None,
        "pooled_trips": pooled,
        "pooling_rate": _rate(pooled, len(carrying)),
        "vehicles_used": len(vehicles),
    }
    distance = {
        "trips_measured": len(km),
        "cab_km_total": _round(sum(km), 3) if km else None,
        "cab_km_per_trip": _round(sum(km) / len(km), 3) if km else None,
        "cab_km_per_rider": (
            _round(
                sum(km)
                / sum(carrying[t] for t in carrying if trips[t].actual_distance_m is not None),
                3,
            )
            if km
            else None
        ),
    }
    return pooling, distance


def _assignments(rows: list[TripRow]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if row.assigned_by is not None:
            counts[row.assigned_by] = counts.get(row.assigned_by, 0) + 1
    return dict(sorted(counts.items()))


def _round(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)
