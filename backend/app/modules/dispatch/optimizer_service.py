"""The batch optimizer's database side: load a problem, run it, record the run (B30-B32).

The solver in `app/domain/optimizer` is pure. Everything that touches the world lives here:
which requests are ready, which cabs and trips exist, one routing-matrix call, and - from
B32 - turning the plan into assignments, suggestions or hints.

**Micro-batching** (`allocation-rules.md` §6, first bullet) is driven by the injected
`Clock`, exactly like every other sweep, and runs from the same two places: `/simctl/clock`
for the simulator and the Celery beat in production (the B20 guard fails if they diverge).
A window opens when the oldest ready request became ready and closes `batch_window_seconds`
later; two requests that arrive inside one window are therefore solved in **one** call,
which is the point - a pooling decision made one request at a time cannot pool.
"""

from __future__ import annotations

import time as wallclock
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.geo import coords as _coords
from app.core.logging import get_logger
from app.domain.cost import CostWeights, effective_rider
from app.domain.dispatch import DetourLimits, Place, widened_candidate_eta_minutes
from app.domain.enums import AlertType, Direction, Urgency
from app.domain.errors import Conflict, InvalidTransition, NotFound
from app.domain.failsafe import SuggestionStatus
from app.domain.geo import LatLng
from app.domain.modes import Mode
from app.domain.optimizer import (
    NightPolicy,
    OptimizerParams,
    Placement,
    Plan,
    Problem,
    Req,
    Seated,
    TripState,
    Veh,
    solve,
)
from app.domain.optimizer_health import Health, HealthThresholds, RunFact, assess
from app.domain.overrides import still_applies
from app.domain.policy import EffectivePolicy
from app.domain.state_machines import Actor, RequestStatus, StopKind, StopStatus, TripStatus
from app.domain.suggestions import SuggestionFacts, named_riders
from app.domain.suggestions import reasons as render_reasons
from app.modules.alerts.models import Alert
from app.modules.alerts.service import AlertService
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.optimizer_models import OptimizerHint, OptimizerRun
from app.modules.dispatch.semi_auto import SemiAutoService
from app.modules.dispatch.service import (
    DispatchService,
    PlannedAssignment,
    haversine_seconds,
    rider_of,
)
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Vehicle
from app.modules.modes.service import ModeService
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Office

logger = get_logger(__name__)

Solver = Callable[[Problem], Plan]

#: `alert.data.kind` of the alert raised while the optimizer is unavailable.
OPTIMIZER_DOWN = "optimizer_down"

#: Vehicles worth offering the optimizer. An `off_duty` or `out_of_service` cab has no
#: driver to send (`allocation-rules.md` §2 rule 1).
DISPATCHABLE_VEHICLE_STATUSES = ("available", "on_trip")


@dataclass(frozen=True, slots=True)
class BatchSweep:
    """What one pass did. Every number is something an operator could ask about."""

    runs: int = 0
    requests: int = 0
    placed: int = 0
    unplaced: int = 0
    applied: int = 0
    suggested: int = 0
    hinted: int = 0
    failed: int = 0

    def __add__(self, other: BatchSweep) -> BatchSweep:
        return BatchSweep(
            runs=self.runs + other.runs,
            requests=self.requests + other.requests,
            placed=self.placed + other.placed,
            unplaced=self.unplaced + other.unplaced,
            applied=self.applied + other.applied,
            suggested=self.suggested + other.suggested,
            hinted=self.hinted + other.hinted,
            failed=self.failed + other.failed,
        )


class OptimizerService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        dispatch: DispatchService,
        solver: Solver | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.dispatch = dispatch
        self.config = ConfigService(session, clock)
        self.solver: Solver = solver or solve

    # --- the sweep ----------------------------------------------------------

    async def run_due_batches(self, operator_id: uuid.UUID | None = None) -> BatchSweep:
        """Run a batch for every operator whose window has closed.

        Named `run_due_*` so the schedule guard sees it: a sweep reachable from a clock
        jump must also be reachable from the beat.
        """
        total = BatchSweep()
        for operator in await self._operators_with_ready_requests(operator_id):
            total = total + await self._run_if_due(operator)
            # After the run, so a batch that has just failed for the third time is noticed
            # in the same sweep and not a minute later.
            await self.sync_health_alert(operator)
        return total

    async def _operators_with_ready_requests(
        self, operator_id: uuid.UUID | None
    ) -> list[uuid.UUID]:
        query = select(RideRequest.operator_id).where(
            RideRequest.status == str(RequestStatus.queued)
        )
        if operator_id is not None:
            query = query.where(RideRequest.operator_id == operator_id)
        rows = await self.session.execute(query.distinct())
        return sorted(rows.scalars().all(), key=str)

    async def _run_if_due(self, operator_id: uuid.UUID) -> BatchSweep:
        ready = await self.ready_requests(operator_id)
        if not ready:
            return BatchSweep()

        now = self.clock.now()
        if await self.dispatch.automation_paused(operator_id):
            # `control-model.md` §3: the emergency pause stops every automatic path, and
            # the optimizer is the most automatic one there is. It says so in the run log,
            # at most once a window: the first sweep after a long pause must be able to tell
            # "idle on purpose" from "dead" (B36).
            window = timedelta(
                seconds=int(await self.config.get(operator_id, "batch_window_seconds"))
            )
            last = await self.last_run(operator_id)
            if last is None or now >= last.started_at + window:
                self.session.add(
                    OptimizerRun(
                        id=uuid.uuid4(),
                        operator_id=operator_id,
                        started_at=now,
                        status="paused",
                        requests=len(ready),
                        request_ids=[],
                    )
                )
                await self.session.flush()
            return BatchSweep()

        # `allocation-rules.md` §2 rule 4: a VIP is "assigned immediately". The micro-batch
        # window exists so that riders can be pooled, and a VIP is never pooled, so there is
        # nothing for them to wait for. The rest of the ready queue rides along: the batch
        # is run now, and everything ready is in it.
        if not await self._any_vip([request for request, _ in ready]):
            window = timedelta(
                seconds=int(await self.config.get(operator_id, "batch_window_seconds"))
            )
            oldest_ready = min(ready_at for _, ready_at in ready)
            if now < oldest_ready + window:
                return BatchSweep()
            last = await self.last_run(operator_id, solved_only=True)
            if last is not None and now < last.started_at + window:
                return BatchSweep()

        return await self.run_batch(operator_id, [request for request, _ in ready])

    async def _any_vip(self, requests: list[RideRequest]) -> bool:
        if not requests:
            return False
        count = await self.session.scalar(
            select(func.count())
            .select_from(Employee)
            .where(Employee.id.in_({request.employee_id for request in requests}))
            .where(Employee.is_vip.is_(True))
        )
        return bool(count)

    async def ready_requests(self, operator_id: uuid.UUID) -> list[tuple[RideRequest, datetime]]:
        """Queued requests the optimizer may act on, each with when it became ready.

        Ready means: not held by a supervisor's `hold` (B26), and past its evening hold
        window (B29). A request that is not ready is not "unplaced" - it has not been
        asked about yet.
        """
        now = self.clock.now()
        rows = (
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.operator_id == operator_id)
                    .where(RideRequest.status == str(RequestStatus.queued))
                    .order_by(RideRequest.queued_at, RideRequest.id)
                )
            )
            .scalars()
            .all()
        )
        # A request a supervisor has been asked about is waiting for an answer, not for
        # the optimizer: re-planning it every window would pile up offers and restart the
        # failsafe timer under the person reading them.
        offered = await self._with_live_offers({request.id for request in rows})
        ready: list[tuple[RideRequest, datetime]] = []
        for request in rows:
            if request.id in offered:
                continue
            if request.hold_until is not None and request.hold_until > now:
                continue
            released = await self.dispatch.hold_release(request)
            if released is not None and now < released:
                continue
            became_ready = request.queued_at
            if released is not None:
                became_ready = max(became_ready, released)
            if request.hold_until is not None:
                became_ready = max(became_ready, request.hold_until)
            ready.append((request, became_ready))
        return ready

    # --- degradation (control-model.md section 6, B36) -------------------------------

    async def health(self, operator_id: uuid.UUID) -> Health:
        """Is the optimizer usable for this operator right now?

        When it is not, `full_auto` and `semi_auto` scopes behave as `manual`: nothing is
        applied and nothing is offered, and the queue is for the supervisors. Derived from
        the run log and the queue on every call, never stored, so recovery needs no one to
        flip a switch: the first run that does not fail is the recovery.
        """
        now = self.clock.now()
        settings = await self.config.all_values(operator_id)
        window = int(settings["batch_window_seconds"])
        runs = await self._recent_runs(operator_id, int(settings["optimizer_failure_threshold"]))
        ready = await self.ready_requests(operator_id)
        oldest = min((at for _, at in ready), default=None)
        return assess(
            runs,
            oldest,
            now,
            HealthThresholds(
                failure_threshold=int(settings["optimizer_failure_threshold"]),
                failure_memory=timedelta(minutes=int(settings["optimizer_failure_memory_minutes"])),
                # Never tighter than the batch cadence itself: a request legitimately waits up
                # to about two windows for its run.
                stall=timedelta(seconds=max(int(settings["optimizer_stall_seconds"]), 3 * window)),
            ),
            paused=await self.dispatch.automation_paused(operator_id),
        )

    async def sync_health_alert(self, operator_id: uuid.UUID) -> Health:
        """Raise one `system` alert while the optimizer is down, and clear it on recovery."""
        health = await self.health(operator_id)
        alerts = AlertService(self.session, self.clock)
        open_alerts = [
            alert
            for alert in (
                await self.session.execute(
                    select(Alert)
                    .where(Alert.operator_id == operator_id)
                    .where(Alert.type == str(AlertType.system))
                    .where(Alert.status != "resolved")
                )
            ).scalars()
            if (alert.data or {}).get("kind") == OPTIMIZER_DOWN
        ]
        if not health.available and not open_alerts:
            await alerts.raise_alert(
                operator_id,
                AlertType.system,
                data={
                    "kind": OPTIMIZER_DOWN,
                    "reason": str(health.reason),
                    "since": health.since.isoformat() if health.since else None,
                    "behaves_as": str(Mode.manual),
                },
            )
            logger.warning("optimizer_down", operator_id=str(operator_id), reason=health.reason)
        elif health.available:
            for alert in open_alerts:
                alert.status = "resolved"
                alert.resolved_at = self.clock.now()
                await alerts.announce_change(alert)
            if open_alerts:
                logger.info("optimizer_recovered", operator_id=str(operator_id))
        return health

    async def effective_mode(self, request: RideRequest, health: Health | None = None) -> Mode:
        """The mode a request is actually served under: its own, unless the optimizer is down."""
        modes = ModeService(self.session, self.clock)
        resolution = await modes.resolve_for_request(request)
        if resolution.mode is Mode.manual:
            return Mode.manual
        health = health or await self.health(request.operator_id)
        return resolution.mode if health.available else Mode.manual

    async def _recent_runs(self, operator_id: uuid.UUID, count: int) -> list[RunFact]:
        rows = await self.session.execute(
            select(OptimizerRun.started_at, OptimizerRun.status)
            .where(OptimizerRun.operator_id == operator_id)
            .order_by(OptimizerRun.started_at.desc(), OptimizerRun.created_at.desc())
            .limit(max(count, 1))
        )
        return [RunFact(row[0], row[1] == "failed") for row in rows]

    async def last_run(
        self, operator_id: uuid.UUID, *, solved_only: bool = False
    ) -> OptimizerRun | None:
        """The newest run. `solved_only` skips the `paused` markers, which say the optimizer
        was alive but are not a batch and must not delay the first real one after a resume."""
        query = select(OptimizerRun).where(OptimizerRun.operator_id == operator_id)
        if solved_only:
            query = query.where(OptimizerRun.status != "paused")
        run: OptimizerRun | None = await self.session.scalar(
            query.order_by(OptimizerRun.started_at.desc(), OptimizerRun.created_at.desc()).limit(1)
        )
        return run

    # --- one batch -----------------------------------------------------------

    async def run_batch(self, operator_id: uuid.UUID, requests: list[RideRequest]) -> BatchSweep:
        """Solve these requests, once per control mode, and deliver each plan its own way.

        `allocation-rules.md` §6: "In `full_auto` scopes they are applied; in `semi_auto`
        they become suggestions; in `manual` they are shown as hints only." Which of the
        three a request gets is `resolve_mode`'s answer for that request, so the requests
        are partitioned by it and each partition is **one solver call**. `full_auto` goes
        first: what it commits is visible to the next partition's problem, so an offer or
        a hint is never made for a cab the batch has just taken.
        """
        # While the optimizer is down every scope behaves as `manual` (control-model.md
        # section 6): the run is still attempted - it is the probe that notices recovery -
        # but its plan is only ever a hint.
        health = await self.health(operator_id)
        partitions: dict[Mode, list[RideRequest]] = {}
        for request in requests:
            partitions.setdefault(await self.effective_mode(request, health), []).append(request)

        total = BatchSweep()
        for mode in (Mode.full_auto, Mode.semi_auto, Mode.manual):
            subset = partitions.get(mode)
            if subset:
                total = total + await self._run_partition(operator_id, mode, subset)
        return total

    async def _run_partition(
        self, operator_id: uuid.UUID, mode: Mode, requests: list[RideRequest]
    ) -> BatchSweep:
        """One solver call, one `optimizer_run` row, one delivery.

        A solver that raises, or one that places nothing, leaves **every request exactly
        as it was**: nothing below the `solve` call runs unless there is a plan to deliver,
        and the run row is the only thing written.
        """
        started = self.clock.now()
        timer = wallclock.perf_counter()
        problem = await self.build_problem(operator_id, requests)

        error: str | None = None
        plan = Plan()
        try:
            plan = self.solver(problem)
        except Exception as exc:  # noqa: BLE001 - a solver fault must not stall dispatch
            error = f"{type(exc).__name__}: {exc}"[:500]
            logger.exception("optimizer_failed", operator_id=str(operator_id))
        elapsed = wallclock.perf_counter() - timer

        status = "failed" if error else ("solved" if plan.placements else "no_solution")
        run = OptimizerRun(
            id=uuid.uuid4(),
            operator_id=operator_id,
            started_at=started,
            status=status,
            solver=plan.solver if not error else None,
            requests=len(requests),
            placed=len(plan.placed_ids),
            unplaced=len(plan.unplaced),
            solve_seconds=elapsed,
            plan_cost=plan.cost if not error else None,
            request_ids=[str(request.id) for request in requests],
            plan=_plan_summary(plan),
            error=error,
            mode=str(mode),
        )
        self.session.add(run)
        await self.session.flush()

        outcome = await self.deliver(operator_id, run, mode, plan, requests)
        run.applied, run.suggested, run.hinted = outcome.applied, outcome.suggested, outcome.hinted
        await self.session.flush()
        logger.info(
            "optimizer_run",
            operator_id=str(operator_id),
            mode=str(mode),
            status=status,
            requests=len(requests),
            placed=run.placed,
            solver=run.solver,
        )
        return BatchSweep(
            runs=1,
            requests=len(requests),
            placed=run.placed,
            unplaced=run.unplaced,
            applied=outcome.applied,
            suggested=outcome.suggested,
            hinted=outcome.hinted,
            failed=1 if error else 0,
        )

    async def deliver(
        self,
        operator_id: uuid.UUID,
        run: OptimizerRun,
        mode: Mode,
        plan: Plan,
        requests: list[RideRequest],
    ) -> BatchSweep:
        """One solver, three destinations (B32): applied, offered, or hinted."""
        by_id = {request.id: request for request in requests}
        if mode is Mode.full_auto:
            return BatchSweep(applied=await self._apply(operator_id, plan, by_id))
        if mode is Mode.semi_auto:
            return BatchSweep(suggested=await self._suggest(plan, by_id))
        return BatchSweep(hinted=await self._hint(operator_id, run, plan, by_id))

    async def _apply(
        self, operator_id: uuid.UUID, plan: Plan, requests: dict[uuid.UUID, RideRequest]
    ) -> int:
        """`full_auto`: assign, one state-machine transition per rider.

        **Never a bulk write.** Each rider goes through `DispatchService.assign`, which
        runs the request through `transition_request`, honours a lock's guard, checks the
        driver and the seats, and records the event with actor `optimizer`. Each is
        wrapped in a savepoint, so one refusal rolls back that rider's partial writes and
        nothing else; if a placement's first rider is refused, the riders who were to
        share with them are left queued for the next batch rather than put on a route
        the solver did not plan.
        """
        applied = 0
        await self._alert_unserved_vips(operator_id, plan, requests)
        alerts = AlertService(self.session, self.clock)
        for placement in plan.placements:
            planned = PlannedAssignment(
                order=placement.order,
                pickup_eta_seconds=placement.pickup_eta_seconds,
                excess_minutes=placement.excess_minutes,
                mode_used=str(Mode.full_auto),
            )
            trip_id = placement.trip_id
            for request_id in placement.order:
                if request_id not in placement.new_request_ids or request_id not in requests:
                    continue
                try:
                    async with self.session.begin_nested():
                        trip = await self.dispatch.assign(
                            operator_id,
                            request_id,
                            placement.vehicle_id,
                            Actor.optimizer,
                            None,
                            trip_id=trip_id,
                            plan=planned,
                        )
                except (Conflict, NotFound, InvalidTransition) as exc:
                    logger.info(
                        "optimizer_assignment_refused",
                        request_id=str(request_id),
                        vehicle_id=str(placement.vehicle_id),
                        reason=type(exc).__name__,
                        detail=str(exc),
                    )
                    break
                trip_id = trip.id
                applied += 1
                # A VIP who has a cab no longer needs the alert that said they had none.
                await alerts.clear_for_request(operator_id, AlertType.vip_no_vehicle, request_id)
        return applied

    async def _alert_unserved_vips(
        self, operator_id: uuid.UUID, plan: Plan, requests: dict[uuid.UUID, RideRequest]
    ) -> None:
        """`allocation-rules.md` §2 rule 4: no VIP vehicle means an alert, never a substitute.

        The solver already refuses to put a VIP in an ordinary cab (`vip_needs_vip_vehicle`),
        so the request simply stays queued. Staying queued silently is the failure: the VIP
        is standing at a kerb and nobody has been told. Before Phase 3 no VIP was assigned
        automatically at all (OQ-38), so this branch could not be reached; it can now.
        """
        unserved = {item.request_id: item for item in plan.unplaced if item.request_id in requests}
        if not unserved:
            return
        vips = set(
            (
                await self.session.execute(
                    select(Employee.id)
                    .where(Employee.id.in_({requests[rid].employee_id for rid in unserved}))
                    .where(Employee.is_vip.is_(True))
                )
            ).scalars()
        )
        alerts = AlertService(self.session, self.clock)
        for request_id, item in unserved.items():
            if requests[request_id].employee_id in vips:
                await alerts.vip_without_vehicle(operator_id, request_id, list(item.reasons))

    async def _suggest(self, plan: Plan, requests: dict[uuid.UUID, RideRequest]) -> int:
        """`semi_auto`: each placed rider becomes an offer a supervisor answers."""
        semi = SemiAutoService(self.session, self.clock, self.dispatch)
        offered = 0
        for placement in plan.placements:
            for request_id in placement.new_request_ids:
                request = requests.get(request_id)
                if request is None:
                    continue
                reasons = await self._reasons(placement, request_id)
                made = await semi.offer_planned(request, placement, reasons)
                offered += 1 if made else 0
        return offered

    async def _hint(
        self,
        operator_id: uuid.UUID,
        run: OptimizerRun,
        plan: Plan,
        requests: dict[uuid.UUID, RideRequest],
    ) -> int:
        """`manual`: record what the optimizer would do and change nothing."""
        now = self.clock.now()
        await self.session.execute(
            update(OptimizerHint)
            .where(OptimizerHint.request_id.in_(list(requests)))
            .where(OptimizerHint.superseded_at.is_(None))
            .values(superseded_at=now)
        )
        hinted = 0
        for placement in plan.placements:
            for request_id in placement.new_request_ids:
                if request_id not in requests:
                    continue
                self.session.add(
                    OptimizerHint(
                        id=uuid.uuid4(),
                        operator_id=operator_id,
                        run_id=run.id,
                        request_id=request_id,
                        vehicle_id=placement.vehicle_id,
                        trip_id=placement.trip_id,
                        rider_order=[str(rid) for rid in placement.order],
                        pickup_eta_seconds=placement.pickup_eta_seconds.get(request_id, 0.0),
                        cost=placement.cost,
                        reasons=await self._reasons(placement, request_id),
                    )
                )
                hinted += 1
        await self.session.flush()
        return hinted

    async def hints(self, operator_id: uuid.UUID) -> list[OptimizerHint]:
        """The live hints: not replaced, and for a request still waiting in the queue."""
        rows = await self.session.execute(
            select(OptimizerHint)
            .join(RideRequest, RideRequest.id == OptimizerHint.request_id)
            .where(OptimizerHint.operator_id == operator_id)
            .where(OptimizerHint.superseded_at.is_(None))
            .where(RideRequest.status == str(RequestStatus.queued))
            .order_by(OptimizerHint.created_at, OptimizerHint.id)
        )
        return list(rows.scalars())

    async def _reasons(self, placement: Placement, request_id: uuid.UUID) -> list[str]:
        """The §5 phrases for a planned placement, e.g. "8 min away, +4 min for Rahul"."""
        vehicle = await self.session.get(Vehicle, placement.vehicle_id)
        seats_after = (vehicle.seat_capacity if vehicle else 0) - len(placement.order)
        ids = [rid for rid in placement.order if rid != request_id]
        names: dict[str, str] = {}
        if ids:
            rows = await self.session.execute(
                select(RideRequest.id, Employee.name)
                .join(Employee, Employee.id == RideRequest.employee_id)
                .where(RideRequest.id.in_(ids))
            )
            names = {str(row[0]): row[1] for row in rows}
        added = {
            str(rid): minutes
            for rid, minutes in placement.added_minutes.items()
            if rid != request_id and rid not in placement.new_request_ids
        }
        return render_reasons(
            SuggestionFacts(
                eta_to_pickup_seconds=placement.pickup_eta_seconds.get(request_id, 0.0),
                seats_free_after=max(seats_after, 0),
                empty_km_added=0.0,
                new_trip=placement.trip_id is None,
                riders=tuple(named_riders(added, names)),
                trip_label=f"T-{placement.trip_id.hex[-4:].upper()}" if placement.trip_id else None,
                eta_approximate=False,
            )
        )

    async def _with_live_offers(self, request_ids: set[uuid.UUID]) -> set[uuid.UUID]:
        if not request_ids:
            return set()
        rows = await self.session.execute(
            select(Suggestion.request_id)
            .where(Suggestion.request_id.in_(request_ids))
            .where(Suggestion.status == str(SuggestionStatus.offered))
        )
        return set(rows.scalars())

    # --- loading the problem ---------------------------------------------------

    async def build_problem(self, operator_id: uuid.UUID, requests: list[RideRequest]) -> Problem:
        """Everything the solver needs, from the database and **one** routing call."""
        now = self.clock.now()
        settings = await self.config.all_values(operator_id)
        timezone = await self.dispatch.operator_timezone(operator_id)

        offices = {
            office.id: office
            for office in (
                await self.session.execute(select(Office).where(Office.operator_id == operator_id))
            ).scalars()
        }
        trips = await self._live_trips_with_riders(operator_id)
        seated_requests: list[RideRequest] = [
            request for riders in trips.values() for request in riders
        ]

        client_ids = {request.client_id for request in requests} | {
            request.client_id for request in seated_requests
        }
        policies = await self.dispatch.client_policies(operator_id, client_ids, settings)

        employee_ids = {request.employee_id for request in [*requests, *seated_requests]}
        employees = {
            employee.id: employee
            for employee in (
                await self.session.execute(select(Employee).where(Employee.id.in_(employee_ids)))
            ).scalars()
        }

        reqs = tuple(
            self._req_of(
                request,
                employees[request.employee_id],
                policies[request.client_id],
                offices,
                settings,
                now,
            )
            for request in requests
        )
        vehicles = await self._vehicles(operator_id, trips, employees, policies, offices, now)

        office_places = {office_id: Place(*_coords(o.location)) for office_id, o in offices.items()}
        duration, distance = await self._matrices(reqs, vehicles, office_places)
        return Problem(
            now=now,
            timezone=timezone,
            offices=office_places,
            requests=reqs,
            vehicles=tuple(vehicles),
            duration=duration,
            distance=distance,
            params=OptimizerParams(
                weights=CostWeights(
                    weight_wait=float(settings["weight_wait"]),
                    weight_empty_km=float(settings["weight_empty_km"]),
                    cost_new_vehicle=float(settings["cost_new_vehicle"]),
                    urgency_factor_high=float(settings["urgency_factor_high"]),
                    urgency_factor_medium=float(settings["urgency_factor_medium"]),
                    urgency_factor_low=float(settings["urgency_factor_low"]),
                ),
                stale_gps_seconds=int(settings["stale_gps_seconds"]),
                enroute_reuse_max_eta_minutes=int(settings["enroute_reuse_max_eta_minutes"]),
                time_limit_seconds=float(settings["optimizer_time_limit_seconds"]),
            ),
        )

    def _req_of(
        self,
        request: RideRequest,
        employee: Employee,
        policy: EffectivePolicy,
        offices: dict[uuid.UUID, Office],
        settings: dict[str, Any],
        now: datetime,
    ) -> Req:
        priority, urgency = effective_rider(
            employee.priority,
            request.urgency,
            forced_priority=request.forced_priority and still_applies(request.override_until, now),
        )
        return Req(
            request_id=request.id,
            rider=rider_of(request),
            direction=Direction(request.direction),
            office_id=request.office_id,
            priority=priority,
            urgency=urgency,
            requested_time=request.requested_time,
            queued_at=request.queued_at,
            is_vip=bool(employee.is_vip),
            no_sharing=request.no_sharing or not policy.pooling_allowed,
            limits=DetourLimits(policy.max_detour_factor, policy.max_detour_minutes),
            pickup_window_minutes=policy.pickup_window_minutes,
            candidate_max_eta_minutes=widened_candidate_eta_minutes(
                base_minutes=int(settings["candidate_max_eta_minutes"]),
                waited_minutes=(now - request.queued_at).total_seconds() / 60.0,
                escalate_after_minutes=int(settings["alert_wait_minutes"]),
                retry_after_minutes=int(settings["retry_after_minutes"]),
                widen_minutes=int(settings["retry_eta_widen_minutes"]),
                ceiling_minutes=int(settings["retry_eta_max_minutes"]),
            ),
            lock_vehicle_id=(
                request.lock_vehicle_id if still_applies(request.override_until, now) else None
            ),
            night_escort_required=bool(employee.night_escort_required),
            night=NightPolicy(
                enabled=policy.night_safety_enabled,
                start=policy.night_start,
                end=policy.night_end,
                positions=policy.night_safety_positions,
            ),
        )

    async def _live_trips_with_riders(
        self, operator_id: uuid.UUID
    ) -> dict[uuid.UUID, list[RideRequest]]:
        """Riders still occupying a seat, grouped by the live trip they are on."""
        live = [
            str(TripStatus.planned),
            str(TripStatus.dispatched),
            str(TripStatus.in_progress),
        ]
        trip_ids = set(
            (
                await self.session.execute(
                    select(Trip.id)
                    .where(Trip.operator_id == operator_id)
                    .where(Trip.status.in_(live))
                )
            ).scalars()
        )
        grouped: dict[uuid.UUID, list[RideRequest]] = {trip_id: [] for trip_id in trip_ids}
        if not trip_ids:
            return grouped
        rows = (
            await self.session.execute(
                select(RideRequest)
                .where(RideRequest.trip_id.in_(trip_ids))
                .where(
                    RideRequest.status.in_(
                        [str(RequestStatus.assigned), str(RequestStatus.picked_up)]
                    )
                )
            )
        ).scalars()
        for request in rows:
            assert request.trip_id is not None
            grouped[request.trip_id].append(request)
        return grouped

    async def _vehicles(
        self,
        operator_id: uuid.UUID,
        riders_by_trip: dict[uuid.UUID, list[RideRequest]],
        employees: dict[uuid.UUID, Employee],
        policies: dict[uuid.UUID, EffectivePolicy],
        offices: dict[uuid.UUID, Office],
        now: datetime,
    ) -> list[Veh]:
        del offices
        vehicle_rows = list(
            (
                await self.session.execute(
                    select(Vehicle)
                    .where(Vehicle.operator_id == operator_id)
                    .where(Vehicle.status.in_(DISPATCHABLE_VEHICLE_STATUSES))
                    .order_by(Vehicle.id)
                )
            ).scalars()
        )
        on_duty = set(
            (
                await self.session.execute(
                    select(DutySession.vehicle_id).where(DutySession.ended_at.is_(None))
                )
            ).scalars()
        )
        positions = await self.dispatch.latest_positions(operator_id)
        live_trips = await self.dispatch.live_trips(operator_id)
        stops = await self.dispatch.stops_by_trip([trip.id for trip in live_trips.values()])

        vehicles: list[Veh] = []
        for vehicle in vehicle_rows:
            position = positions.get(vehicle.id)
            if position is None or vehicle.id not in on_duty:
                continue
            trip = live_trips.get(vehicle.id)
            state = (
                self._trip_state(
                    trip,
                    riders_by_trip.get(trip.id, []),
                    stops.get(trip.id, []),
                    employees,
                    policies,
                    now,
                )
                if trip is not None
                else None
            )
            vehicles.append(
                Veh(
                    vehicle_id=vehicle.id,
                    position=position.place,
                    gps_age_seconds=(now - position.recorded_at).total_seconds(),
                    status=vehicle.status,
                    vehicle_type=vehicle.vehicle_type,
                    seat_capacity=vehicle.seat_capacity,
                    trip=state,
                )
            )
        return vehicles

    def _trip_state(
        self,
        trip: Trip,
        riders: list[RideRequest],
        stops: list[TripStop],
        employees: dict[uuid.UUID, Employee],
        policies: dict[uuid.UUID, EffectivePolicy],
        now: datetime,
    ) -> TripState:
        direction = Direction(trip.direction)
        # Rider order is the order of their own stop: pickups going in, drops coming home.
        own_kind = StopKind.pickup if direction is Direction.to_office else StopKind.drop
        sequence = {
            stop.request_id: stop.sequence for stop in stops if stop.stop_type == str(own_kind)
        }
        pickups_done_by = {
            stop.request_id: stop.done_at
            for stop in stops
            if stop.stop_type == str(StopKind.pickup) and stop.status == str(StopStatus.done)
        }
        seated: list[Seated] = []
        any_locked = False
        for request in sorted(riders, key=lambda r: (sequence.get(r.id, 10_000), str(r.id))):
            employee = employees[request.employee_id]
            policy = policies[request.client_id]
            priority, urgency = effective_rider(
                employee.priority,
                request.urgency,
                forced_priority=request.forced_priority
                and still_applies(request.override_until, now),
            )
            locked = request.lock_vehicle_id is not None and still_applies(
                request.override_until, now
            )
            any_locked = any_locked or locked
            picked_at = pickups_done_by.get(request.id)
            seated.append(
                Seated(
                    request_id=request.id,
                    rider=rider_of(request),
                    picked_up=request.status == str(RequestStatus.picked_up),
                    ridden_seconds=(
                        max((now - picked_at).total_seconds(), 0.0) if picked_at else 0.0
                    ),
                    priority=priority,
                    urgency=Urgency(urgency),
                    limits=DetourLimits(policy.max_detour_factor, policy.max_detour_minutes),
                    no_sharing=request.no_sharing or not policy.pooling_allowed,
                    is_vip=bool(employee.is_vip),
                    locked=locked,
                    night_escort_required=bool(employee.night_escort_required),
                )
            )
        pickups_done = bool(pickups_done_by)
        under_way = trip.status == str(TripStatus.in_progress)
        return TripState(
            trip_id=trip.id,
            direction=direction,
            office_id=trip.office_id,
            riders=tuple(seated),
            pooling_blocked=trip.pooling_blocked and still_applies(trip.override_until, now),
            # A trip may be rearranged only while nobody has been collected and nobody on
            # it is pinned there (`allocation-rules.md` §6, last bullet).
            order_fixed=under_way or pickups_done or any_locked,
            pickups_done=pickups_done,
        )

    async def _matrices(
        self,
        requests: tuple[Req, ...],
        vehicles: list[Veh],
        offices: dict[uuid.UUID, Place],
    ) -> tuple[Callable[[Place, Place], float], Callable[[Place, Place], float]]:
        """One table call covering every place the solver can ask about."""
        places: dict[Place, None] = {}
        for place in offices.values():
            places[place] = None
        for veh in vehicles:
            places[veh.position] = None
            if veh.trip:
                for seat in veh.trip.riders:
                    places[seat.rider.place] = None
                    if seat.rider.pickup is not None:
                        places[seat.rider.pickup] = None
        for req in requests:
            places[req.rider.place] = None
            if req.rider.pickup is not None:
                places[req.rider.pickup] = None
        ordered = list(places)
        points = [LatLng(place.lat, place.lng) for place in ordered]
        table = await self.dispatch.eta.eta_matrix(points, points)
        index = {place: i for i, place in enumerate(ordered)}

        def duration(a: Place, b: Place) -> float:
            if a == b:
                return 0.0
            i, j = index.get(a), index.get(b)
            if i is None or j is None:
                return float(haversine_seconds(a, b))
            return float(table[i][j].seconds)

        def distance(a: Place, b: Place) -> float:
            if a == b:
                return 0.0
            i, j = index.get(a), index.get(b)
            if i is None or j is None:
                return float(haversine_seconds(a, b)) * 6.6
            return float(table[i][j].distance_meters)

        return duration, distance


def _plan_summary(plan: Plan) -> dict[str, Any]:
    return {
        "solver": plan.solver,
        "cost": plan.cost,
        "placements": [_placement_summary(placement) for placement in plan.placements],
        "unplaced": [
            {"request_id": str(item.request_id), "reasons": list(item.reasons)}
            for item in plan.unplaced
        ],
    }


def _placement_summary(placement: Placement) -> dict[str, Any]:
    return {
        "vehicle_id": str(placement.vehicle_id),
        "trip_id": str(placement.trip_id) if placement.trip_id else None,
        "order": [str(rid) for rid in placement.order],
        "new": [str(rid) for rid in placement.new_request_ids],
        "cost": placement.cost,
        "reorders_existing": placement.reorders_existing,
    }
