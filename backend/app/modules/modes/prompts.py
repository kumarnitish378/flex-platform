"""Mode-switch prompts: the system suggests, a person decides (`control-model.md` §5, B35).

Every minute-ish, for each scope that is currently on automation, this measures the last
`mode_prompt_window_minutes` and, if any of §5's four conditions holds, raises a
`mode_prompt` alert saying so. When the conditions clear, the alert resolves itself.

**What this never does is change a mode.** The alert carries the scope's id and the numbers
that tripped it; the app offers the supervisor a button that calls the ordinary
`PUT /admin/mode-settings/{id}` - a different endpoint behind a different permission, which
is the whole point. `tests/unit/test_mode_prompts_never_switch.py` fails if any module other
than the mode-setting service writes the `mode` column.

**A scope** is a `mode_setting` row. Only rows currently on `semi_auto` or `full_auto`,
and whose time window is open, are measured: a prompt to switch a scope that is already
manual, or whose evening rule is not in force, would be noise.

**Measuring a scope** means attributing requests to it, and `resolve_mode` already does
that - the setting that wins is the scope the request belongs to - so a request's scope is
exactly the one the platform used to decide how to treat it.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.enums import AlertType, Direction
from app.domain.failsafe import SuggestionStatus
from app.domain.mode_prompts import (
    Observation,
    PromptThresholds,
    ScopeWindow,
    evaluate,
)
from app.domain.modes import Mode, ModeScope, RequestScope, in_window, resolve_mode
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, VehicleStatus
from app.domain.timeofday import local
from app.modules.alerts.models import Alert
from app.modules.alerts.service import AlertService
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import TripStop
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.fleet.models import Vehicle
from app.modules.modes.service import ModeService
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest, RideRequestEvent
from app.modules.tenancy.models import Operator
from app.modules.tracking.models import LocationPing

logger = get_logger(__name__)

AUTOMATIC = (Mode.semi_auto, Mode.full_auto)
#: A request is never waiting longer than its expiry (`request_expiry_minutes`, at most 8
#: hours), so this many hours back from a past instant is enough to find everything that
#: could have been pending then.
LOOKBACK_HOURS = 9


@dataclass(frozen=True, slots=True)
class PromptSweep:
    raised: int = 0
    updated: int = 0
    resolved: int = 0


class ModePromptService:
    def __init__(self, session: AsyncSession, clock: Clock, eta: Any = None) -> None:
        self.session = session
        self.clock = clock
        self.eta = eta
        self.config = ConfigService(session, clock)
        self.modes = ModeService(session, clock)
        self.alerts = AlertService(session, clock)

    async def run_due_mode_prompts(self, operator_id: uuid.UUID | None = None) -> PromptSweep:
        """One pass over every operator's automatic scopes."""
        query = select(Operator.id)
        if operator_id is not None:
            query = query.where(Operator.id == operator_id)
        total = PromptSweep()
        for operator in sorted((await self.session.execute(query)).scalars(), key=str):
            result = await self._operator(operator)
            # The optimizer's own sweep cannot report that it is not running, so this
            # separate task is the one that notices (control-model.md section 6, B36).
            await self._optimizer_watch(operator)
            total = PromptSweep(
                raised=total.raised + result.raised,
                updated=total.updated + result.updated,
                resolved=total.resolved + result.resolved,
            )
        return total

    async def _optimizer_watch(self, operator_id: uuid.UUID) -> None:
        from app.modules.dispatch.optimizer_service import OptimizerService
        from app.modules.dispatch.service import DispatchService

        # The sweep only reads and raises alerts, so it needs no routing: an approximate
        # ETA service is a stand-in that is never asked a question.
        await OptimizerService(
            self.session, self.clock, DispatchService(self.session, self.clock, self.eta)
        ).sync_health_alert(operator_id)

    # --- one operator ---------------------------------------------------------------

    async def _operator(self, operator_id: uuid.UUID) -> PromptSweep:
        now = self.clock.now()
        settings = await self.config.all_values(operator_id)
        thresholds = PromptThresholds(
            window_minutes=int(settings["mode_prompt_window_minutes"]),
            rejected_share=float(settings["mode_prompt_rejected_share"]),
            eta_error_minutes=float(settings["mode_prompt_eta_error_minutes"]),
            pending_multiple=float(settings["mode_prompt_pending_multiple"]),
            fleet_share=float(settings["mode_prompt_fleet_share"]),
            min_samples=int(settings["mode_prompt_min_samples"]),
        )
        baseline_days = int(settings["mode_prompt_baseline_days"])
        operator = await self.session.get(Operator, operator_id)
        timezone = operator.timezone if operator is not None else "UTC"
        scopes = await self.modes.scopes(operator_id)
        active = [
            scope
            for scope in scopes
            if scope.mode in AUTOMATIC and in_window(scope, local(now, timezone))
        ]

        existing = await self._open_prompts(operator_id)
        windows = await self._measure(
            operator_id, scopes, active, thresholds, baseline_days, timezone, settings
        )

        raised = updated = resolved = 0
        for scope in active:
            observed = evaluate(windows[scope.id], thresholds)
            prompt = existing.pop(scope.id, None)
            if observed and prompt is None:
                await self._raise(operator_id, scope, observed, thresholds)
                raised += 1
            elif observed and prompt is not None:
                if _changed(prompt, observed):
                    prompt.data = _payload(scope, observed, thresholds)
                    await self.session.flush()
                    updated += 1
            elif prompt is not None:
                await self._resolve(prompt)
                resolved += 1
        # A prompt for a scope that is no longer on automation, or no longer in force, has
        # nothing left to suggest.
        for stale in existing.values():
            await self._resolve(stale)
            resolved += 1
        return PromptSweep(raised, updated, resolved)

    # --- measuring ------------------------------------------------------------------

    async def _measure(
        self,
        operator_id: uuid.UUID,
        scopes: list[ModeScope],
        active: list[ModeScope],
        thresholds: PromptThresholds,
        baseline_days: int,
        timezone: str,
        settings: dict[str, Any],
    ) -> dict[uuid.UUID, ScopeWindow]:
        if not active:
            return {}
        now = self.clock.now()
        since = now - timedelta(minutes=thresholds.window_minutes)

        suggestions = await self._decided_suggestions(operator_id, since)
        pickups = await self._pickups(operator_id, since)
        queued = list(
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.operator_id == operator_id)
                    .where(RideRequest.status == str(RequestStatus.queued))
                )
            ).scalars()
        )
        history = await self._historical_requests(operator_id, now, baseline_days)

        wanted = {
            *(request_id for request_id, _ in suggestions),
            *(request_id for request_id, _ in pickups),
            *(request.id for request in queued),
            *(request.id for request in history),
        }
        scope_of = await self._scopes_of(operator_id, wanted, scopes, timezone)
        fleet_size, fleet_degraded = await self._fleet(
            operator_id, int(settings["stale_gps_seconds"])
        )
        normal = await self._normal_pending(history, scope_of, now, baseline_days, operator_id)

        result: dict[uuid.UUID, ScopeWindow] = {}
        for scope in active:
            decided = [status for rid, status in suggestions if scope_of.get(rid) == scope.id]
            errors = tuple(minutes for rid, minutes in pickups if scope_of.get(rid) == scope.id)
            result[scope.id] = ScopeWindow(
                decided_suggestions=len(decided),
                rejected_suggestions=sum(1 for s in decided if s == str(SuggestionStatus.rejected)),
                eta_errors_minutes=errors,
                pending_now=sum(1 for request in queued if scope_of.get(request.id) == scope.id),
                pending_normal=normal.get(scope.id),
                fleet_size=fleet_size,
                fleet_degraded=fleet_degraded,
            )
        return result

    async def _decided_suggestions(
        self, operator_id: uuid.UUID, since: datetime
    ) -> list[tuple[uuid.UUID, str]]:
        """Suggestions settled in the window (superseded ones are not a verdict)."""
        rows = await self.session.execute(
            select(Suggestion.request_id, Suggestion.status)
            .where(Suggestion.operator_id == operator_id)
            .where(Suggestion.rank == 1)
            .where(Suggestion.decided_at >= since)
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
        return [(row[0], str(row[1])) for row in rows]

    async def _pickups(
        self, operator_id: uuid.UUID, since: datetime
    ) -> list[tuple[uuid.UUID, float]]:
        """|actual - planned| pickup, in minutes, for pickups completed in the window."""
        rows = await self.session.execute(
            select(TripStop.request_id, TripStop.planned_eta, TripStop.done_at)
            .where(TripStop.operator_id == operator_id)
            .where(TripStop.stop_type == str(StopKind.pickup))
            .where(TripStop.status == str(StopStatus.done))
            .where(TripStop.done_at >= since)
            .where(TripStop.planned_eta.is_not(None))
        )
        return [
            (row[0], abs((row[2] - row[1]).total_seconds()) / 60.0)
            for row in rows
            if row[1] is not None and row[2] is not None
        ]

    async def _fleet(self, operator_id: uuid.UUID, stale_after: int) -> tuple[int, int]:
        """Vehicles in service, and how many of them are stale or out of service."""
        now = self.clock.now()
        vehicles = list(
            (
                await self.session.execute(
                    select(Vehicle)
                    .where(Vehicle.operator_id == operator_id)
                    .where(Vehicle.status != str(VehicleStatus.off_duty))
                )
            ).scalars()
        )
        if not vehicles:
            return 0, 0
        latest = {
            row[0]: row[1]
            for row in await self.session.execute(
                select(LocationPing.vehicle_id, LocationPing.recorded_at)
                .where(LocationPing.operator_id == operator_id)
                .where(LocationPing.recorded_at >= now - timedelta(hours=1))
                .order_by(LocationPing.vehicle_id, LocationPing.recorded_at)
            )
        }
        degraded = 0
        for vehicle in vehicles:
            if vehicle.status == str(VehicleStatus.out_of_service):
                degraded += 1
                continue
            seen = latest.get(vehicle.id)
            if seen is None or (now - seen).total_seconds() > stale_after:
                degraded += 1
        return len(vehicles), degraded

    async def _historical_requests(
        self, operator_id: uuid.UUID, now: datetime, days: int
    ) -> list[RideRequest]:
        if days <= 0:
            return []
        earliest = now - timedelta(days=days, hours=LOOKBACK_HOURS)
        return list(
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.operator_id == operator_id)
                    .where(RideRequest.queued_at >= earliest)
                    .where(RideRequest.queued_at < now - timedelta(hours=1))
                )
            ).scalars()
        )

    async def _normal_pending(
        self,
        history: list[RideRequest],
        scope_of: dict[uuid.UUID, uuid.UUID | None],
        now: datetime,
        days: int,
        operator_id: uuid.UUID,
    ) -> dict[uuid.UUID, float]:
        """Per scope, the mean number pending at this time of day on past days.

        "Normal for that time slot" (§5) is read as: how many requests were waiting, in
        this scope, at this moment of the day over the previous `days` days. Days with no
        requests at all are left out of the mean - they are closures, not quiet mornings -
        and a scope with no history gets no baseline, so the condition cannot fire on it.
        """
        if not history:
            return {}
        left = await self._left_queue_at([request.id for request in history])
        samples: dict[uuid.UUID, list[int]] = defaultdict(list)
        for day in range(1, days + 1):
            moment = now - timedelta(days=day)
            day_requests = [
                request
                for request in history
                if moment - timedelta(hours=LOOKBACK_HOURS) <= request.queued_at <= moment
            ]
            if not day_requests:
                continue
            counts: dict[uuid.UUID, int] = defaultdict(int)
            for request in day_requests:
                gone = left.get(request.id)
                if gone is not None and gone <= moment:
                    continue
                scope_id = scope_of.get(request.id)
                if scope_id is not None:
                    counts[scope_id] += 1
            for scope_id in {scope_of.get(r.id) for r in history if scope_of.get(r.id)}:
                if scope_id is not None:
                    samples[scope_id].append(counts.get(scope_id, 0))
        del operator_id
        return {scope: sum(values) / len(values) for scope, values in samples.items() if values}

    async def _left_queue_at(self, request_ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime]:
        """When each request first stopped waiting: assigned, cancelled or expired."""
        left: dict[uuid.UUID, datetime] = {}
        if not request_ids:
            return left
        rows = await self.session.execute(
            select(RideRequestEvent.request_id, RideRequestEvent.at)
            .where(RideRequestEvent.request_id.in_(request_ids))
            .where(
                RideRequestEvent.to_status.in_(
                    [
                        str(RequestStatus.assigned),
                        str(RequestStatus.cancelled),
                        str(RequestStatus.expired),
                    ]
                )
            )
            .order_by(RideRequestEvent.at)
        )
        for request_id, at in rows:
            left.setdefault(request_id, at)
        return left

    async def _scopes_of(
        self,
        operator_id: uuid.UUID,
        request_ids: Iterable[uuid.UUID],
        scopes: list[ModeScope],
        timezone: str,
    ) -> dict[uuid.UUID, uuid.UUID | None]:
        """Which scope (mode setting) governs each request, by the platform's own resolver."""
        ids = set(request_ids)
        if not ids:
            return {}
        requests = list(
            (
                await self.session.execute(select(RideRequest).where(RideRequest.id.in_(ids)))
            ).scalars()
        )
        employees = {
            employee.id: employee
            for employee in (
                await self.session.execute(
                    select(Employee).where(Employee.id.in_({r.employee_id for r in requests}))
                )
            ).scalars()
        }
        default = await self.modes.operator_default(operator_id)
        mapping: dict[uuid.UUID, uuid.UUID | None] = {}
        for request in requests:
            employee = employees.get(request.employee_id)
            if employee is None:
                continue
            resolution = resolve_mode(
                scopes,
                RequestScope(
                    client_id=request.client_id,
                    direction=Direction(request.direction),
                    zone_id=employee.zone_id,
                    is_vip=bool(employee.is_vip),
                ),
                local(request.requested_time, timezone),
                automation_paused=False,
                operator_default=default,
            )
            mapping[request.id] = resolution.setting_id
        return mapping

    # --- the alerts ------------------------------------------------------------------

    async def _open_prompts(self, operator_id: uuid.UUID) -> dict[uuid.UUID, Alert]:
        rows = (
            (
                await self.session.execute(
                    select(Alert)
                    .where(Alert.operator_id == operator_id)
                    .where(Alert.type == str(AlertType.mode_prompt))
                    .where(Alert.status != "resolved")
                )
            )
            .scalars()
            .all()
        )
        found: dict[uuid.UUID, Alert] = {}
        for alert in rows:
            raw = (alert.data or {}).get("setting_id")
            if raw:
                found[uuid.UUID(str(raw))] = alert
        return found

    async def _raise(
        self,
        operator_id: uuid.UUID,
        scope: ModeScope,
        observed: list[Observation],
        thresholds: PromptThresholds,
    ) -> None:
        await self.alerts.raise_alert(
            operator_id, AlertType.mode_prompt, data=_payload(scope, observed, thresholds)
        )
        logger.info(
            "mode_prompt_raised",
            operator_id=str(operator_id),
            setting_id=str(scope.id),
            conditions=[str(item.condition) for item in observed],
        )

    async def _resolve(self, alert: Alert) -> None:
        """Resolve on the platform's own authority: nobody acted, the condition went away."""
        alert.status = "resolved"
        alert.resolved_at = self.clock.now()
        await self.alerts._announce_change(alert)  # noqa: SLF001 - same package of concerns


def _payload(
    scope: ModeScope, observed: list[Observation], thresholds: PromptThresholds
) -> dict[str, Any]:
    return {
        "setting_id": str(scope.id),
        "mode": str(scope.mode),
        "suggest": str(Mode.manual),
        "window_minutes": thresholds.window_minutes,
        "conditions": [item.as_dict() for item in observed],
    }


def _changed(alert: Alert, observed: list[Observation]) -> bool:
    now = {str(item.condition) for item in observed}
    before = {str(c.get("condition")) for c in (alert.data or {}).get("conditions", [])}
    return now != before
