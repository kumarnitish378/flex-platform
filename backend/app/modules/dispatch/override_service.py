"""Supervisor overrides: preview, apply, audit (`control-model.md` §3, B26).

The nine actions of §3 in one place, each one doing three things in the same order:

1. **work out what it would change** - the dry-run impact, which `/overrides/preview`
   returns on its own and `/overrides` computes anyway because rule 4 needs to know
   whether a hard rule is being waived before it can decide which reasons are allowed;
2. **apply it through the state machine**, never by writing a status (hard rule 5);
3. **write one `override_log` row** with the before and after values (rule 6).

Expiry (rule 5) is deliberately *not* a job. A sweep that flipped the columns back
would be a second source of truth, would need to be running for the platform to be
correct, and would leave a window after any restart where an expired lock still pinned
a rider to a cab. Instead the applied state carries its end date -
`ride_request.override_until`, `trip.override_until` - and every read asks
`still_applies`. Nothing runs, and the override stops.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.dispatch import Violation
from app.domain.enums import Role
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.overrides import (
    OverrideAction,
    OverrideCommand,
    check_reason,
    check_targets,
    default_expiry,
)
from app.domain.rules import RuleBreach, explain, waivable
from app.domain.state_machines import (
    Actor,
    RequestContext,
    RequestStatus,
    StopStatus,
    TripStatus,
    VehicleStatus,
    actor_type_for,
    transition_request,
    transition_stop,
    transition_trip,
    transition_vehicle,
)
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.override_models import OverrideLog
from app.modules.dispatch.service import (
    LIVE_TRIP_STATUSES,
    ON_BOARD_STATUSES,
    POSITION_LOOKBACK,
    DispatchService,
)
from app.modules.fleet.models import Vehicle
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest, RideRequestEvent
from app.modules.requests.service import RideRequestService
from app.modules.tenancy.models import Operator

logger = get_logger(__name__)

#: Request states a hold can still mean something in. Holding an assigned request would
#: be two decisions in one tap - take them off the cab, then hold them - and §3 has a
#: separate action for the first half.
HOLDABLE_STATUSES = (RequestStatus.requested, RequestStatus.queued, RequestStatus.suggested)


@dataclass(frozen=True, slots=True)
class AffectedRequest:
    """One rider this override would touch, and by how much."""

    request_id: uuid.UUID
    employee_name: str
    #: Extra minutes aboard for somebody already on the vehicle (`allocation-rules.md`
    #: §5's "+4 min for Rahul"). `None` when this rider is not being detoured.
    added_minutes: float | None = None
    #: How much later (positive) or sooner (negative) this rider would be collected.
    #: `None` when there is no before to compare with, or no after to promise.
    eta_change_minutes: float | None = None
    #: Back to the queue needing another cab. Their new ETA is genuinely unknown until
    #: somebody assigns them, and a number invented here would be a promise.
    requeued: bool = False


@dataclass(frozen=True, slots=True)
class Impact:
    """§3 rule 2's confirm screen, as data."""

    affected_requests: list[AffectedRequest] = field(default_factory=list)
    zones_without_available_vehicle: list[str] = field(default_factory=list)
    hard_rule_violations: list[RuleBreach] = field(default_factory=list)

    @property
    def waives_hard_rule(self) -> bool:
        return bool(self.hard_rule_violations)


@dataclass(frozen=True, slots=True)
class AppliedOverride:
    override_id: uuid.UUID
    impact: Impact
    expires_at: datetime | None = None
    trip_id: uuid.UUID | None = None


class OverrideService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        dispatch: DispatchService,
        requests: RideRequestService | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.dispatch = dispatch
        self.requests = requests or RideRequestService(session, clock)

    # --- the two entry points ---------------------------------------------------

    async def preview(self, operator_id: uuid.UUID, command: OverrideCommand) -> Impact:
        """What this override would do, without doing it (§3 rule 2).

        Reads only. The same computation `apply` runs, so the screen a supervisor
        confirms is not a different answer from the one they get.
        """
        check_targets(command)
        return await self._impact(operator_id, command)

    async def apply(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
    ) -> AppliedOverride:
        check_targets(command)
        impact = await self._impact(operator_id, command)

        breaches = impact.hard_rule_violations
        if not waivable([breach.rule for breach in self._unwaivable(command, breaches)]):
            # §3 rule 1 and B21's `NEVER_WAIVABLE`: no reason code unlocks these. A cab
            # with no driver cannot be sent, and bravery is not the missing ingredient.
            raise Conflict(
                "That override breaks a rule nobody may waive",
                {
                    "action": str(command.action),
                    "violations": [breach.summary for breach in breaches],
                },
            )
        check_reason(command, waives_hard_rule=impact.waives_hard_rule)

        expires_at = await self._expiry(operator_id, command)
        before, after, trip_id = await self._perform(
            operator_id, command, actor, actor_user_id, expires_at
        )

        row = OverrideLog(
            id=uuid.uuid4(),
            operator_id=operator_id,
            action=str(command.action),
            request_id=command.request_id,
            trip_id=trip_id if trip_id is not None else command.trip_id,
            vehicle_id=command.vehicle_id or command.target_vehicle_id,
            before=before,
            after=after,
            reason_code=str(command.reason_code),
            note=command.note,
            waived_violations=[breach.summary for breach in breaches],
            expires_at=expires_at,
            user_id=actor_user_id,
            at=self.clock.now(),
        )
        self.session.add(row)
        await self.session.flush()

        logger.info(
            "override_applied",
            override_id=str(row.id),
            action=str(command.action),
            reason_code=str(command.reason_code),
            waived=[breach.summary for breach in breaches],
            expires_at=expires_at.isoformat() if expires_at else None,
        )
        return AppliedOverride(
            override_id=row.id, impact=impact, expires_at=expires_at, trip_id=trip_id
        )

    @staticmethod
    def _unwaivable(command: OverrideCommand, breaches: list[RuleBreach]) -> list[RuleBreach]:
        """The breaches `waivable()` must still judge for this particular action.

        One exception, and it is the whole reason B21 wrote the rule the way it did.
        `locked_to_other_vehicle` is never waivable because waiving it would **silently**
        undo another supervisor's override - a rider quietly moved off the cab somebody
        pinned them to. A `reassign` is the opposite of silent: it is a human naming
        this request, this cab and a reason, and `control-model.md` §3 lists it as an
        action available in every mode. The state machine has required `is_override`
        for exactly this since Phase 1.

        So the lock is waivable here and nowhere else, it still needs rule 4's narrowed
        reason and a note, it is flagged in the report like any other hard-rule
        override, and the lock **moves with the rider** rather than being left pointing
        at a cab they are no longer on.
        """
        if command.action is not OverrideAction.reassign:
            return breaches
        return [
            breach for breach in breaches if breach.rule is not Violation.locked_to_other_vehicle
        ]

    # --- expiry -------------------------------------------------------------------

    async def _expiry(self, operator_id: uuid.UUID, command: OverrideCommand) -> datetime | None:
        """§3 rule 5, in the operator's own local time.

        An explicit value from the caller wins, **including an explicit null** - that is
        the "until the trip ends" form the rule allows, and it is the only reason the
        command carries `expiry_specified` rather than inferring from `None`.
        """
        if command.expiry_specified:
            return command.expires_at
        operator = await self.session.get(Operator, operator_id)
        if operator is None:
            raise NotFound("Operator not found")
        return default_expiry(command.action, self.clock.now(), operator.timezone)

    def _merge_until(
        self, current: datetime | None, new: datetime | None, *, already_standing: bool
    ) -> datetime | None:
        """One expiry column, two standing overrides: the later one wins.

        `ride_request.override_until` is a single column (`data-model.md`), so a request
        that is both locked and forced to priority 1 has one end date between them. The
        **latest** is the safe reading: ending early would silently drop an override
        whose own expiry had not come, and `None` - open-ended - beats any date.

        The per-action truth is still exact in `override_log`, which is what the audit
        and Phase 3's training data read.
        """
        if not already_standing:
            return new
        if current is None or new is None:
            return None
        return max(current, new)

    # --- dispatching to the nine actions -------------------------------------------

    async def _perform(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        handlers = {
            OverrideAction.reassign: self._do_reassign,
            OverrideAction.lock: self._do_lock,
            OverrideAction.unlock: self._do_unlock,
            OverrideAction.force_priority: self._do_force_priority,
            OverrideAction.block_pooling: self._do_block_pooling,
            OverrideAction.hold: self._do_hold,
            OverrideAction.cancel: self._do_cancel,
            OverrideAction.vehicle_out_of_service: self._do_out_of_service,
        }
        return await handlers[command.action](
            operator_id, command, actor, actor_user_id, expires_at
        )

    async def _do_reassign(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del expires_at  # a reassignment is done when it is done; there is nothing to lapse
        request = await self._request(operator_id, command.request_id)
        assert command.target_vehicle_id is not None

        previous_trip_id = request.trip_id
        previous_vehicle_id: uuid.UUID | None = None
        if previous_trip_id is not None:
            previous = await self.session.get(Trip, previous_trip_id)
            if previous is not None:
                previous_vehicle_id = previous.vehicle_id
                if previous.vehicle_id == command.target_vehicle_id:
                    raise Conflict(
                        "The request is already on that vehicle",
                        {"vehicle_id": str(command.target_vehicle_id)},
                    )

        before: dict[str, Any] = {
            "trip_id": _or_none(previous_trip_id),
            "vehicle_id": _or_none(previous_vehicle_id),
            "status": request.status,
        }
        await self._release_rider(request, actor, actor_user_id, reason="reassigned")
        trip = await self.dispatch.assign(
            operator_id=operator_id,
            request_id=request.id,
            vehicle_id=command.target_vehicle_id,
            actor=actor,
            actor_user_id=actor_user_id,
            trip_id=command.trip_id,
            reason_code=str(command.reason_code),
            note=command.note,
            # The one caller allowed to move a locked request (state machine, Phase 1).
            is_override=True,
        )
        after: dict[str, Any] = {
            "trip_id": str(trip.id),
            "vehicle_id": str(trip.vehicle_id),
            "status": request.status,
        }
        if request.lock_vehicle_id is not None:
            # The lock follows the rider. Left behind it would point at a cab they are
            # not on, and every read from here on would report
            # `locked_to_other_vehicle` against the vehicle actually carrying them.
            before["lock_vehicle_id"] = _or_none(request.lock_vehicle_id)
            request.lock_vehicle_id = trip.vehicle_id
            after["lock_vehicle_id"] = str(trip.vehicle_id)
        return before, after, trip.id

    async def _do_lock(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del actor, actor_user_id
        request = await self._request(operator_id, command.request_id)
        vehicle_id = command.vehicle_id or await self._current_vehicle_of(request)
        if vehicle_id is None:
            raise ValidationFailed(
                "Locking an unassigned request needs the vehicle to pin it to",
                {"request_id": str(request.id)},
            )
        await self._vehicle(operator_id, vehicle_id)

        before = {
            "lock_vehicle_id": _or_none(request.lock_vehicle_id),
            "override_until": _iso(request.override_until),
        }
        request.override_until = self._merge_until(
            request.override_until, expires_at, already_standing=self._standing(request)
        )
        request.lock_vehicle_id = vehicle_id
        after = {
            "lock_vehicle_id": str(vehicle_id),
            "override_until": _iso(request.override_until),
        }
        return before, after, request.trip_id

    async def _do_unlock(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del actor, actor_user_id, expires_at
        request = await self._request(operator_id, command.request_id)
        if request.lock_vehicle_id is None:
            raise Conflict("That request is not locked", {"request_id": str(request.id)})

        before = {"lock_vehicle_id": str(request.lock_vehicle_id)}
        request.lock_vehicle_id = None
        if not request.forced_priority:
            request.override_until = None

        # Close the lock's own row rather than leaving it open and contradicted: "is
        # this request locked?" must have one answer, and the audit should show when
        # the lock ended, not only when it would have.
        now = self.clock.now()
        await self.session.execute(
            update(OverrideLog)
            .where(OverrideLog.operator_id == operator_id)
            .where(OverrideLog.request_id == request.id)
            .where(OverrideLog.action == str(OverrideAction.lock))
            .where((OverrideLog.expires_at.is_(None)) | (OverrideLog.expires_at > now))
            .values(expires_at=now)
        )
        return before, {"lock_vehicle_id": None}, request.trip_id

    async def _do_force_priority(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del actor, actor_user_id
        request = await self._request(operator_id, command.request_id)
        before = {
            "forced_priority": request.forced_priority,
            "override_until": _iso(request.override_until),
        }
        request.override_until = self._merge_until(
            request.override_until, expires_at, already_standing=self._standing(request)
        )
        # ADR-0021: the rider's own `urgency` is never rewritten. `forced_priority` is
        # applied at scoring time by `effective_rider`, so when it lapses the request
        # goes back to the answer the rider actually gave.
        request.forced_priority = True
        after = {"forced_priority": True, "override_until": _iso(request.override_until)}
        return before, after, request.trip_id

    async def _do_block_pooling(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del actor, actor_user_id
        trip = await self._trip(operator_id, command.trip_id)
        before = {
            "pooling_blocked": trip.pooling_blocked,
            "override_until": _iso(trip.override_until),
        }
        trip.override_until = self._merge_until(
            trip.override_until, expires_at, already_standing=trip.pooling_blocked
        )
        trip.pooling_blocked = True
        after = {"pooling_blocked": True, "override_until": _iso(trip.override_until)}
        return before, after, trip.id

    async def _do_hold(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del actor, actor_user_id
        request = await self._request(operator_id, command.request_id)
        if request.status not in [str(status) for status in HOLDABLE_STATUSES]:
            raise Conflict(
                f"A request that is {request.status} cannot be held",
                {"request_id": str(request.id), "status": request.status},
            )
        before = {
            "hold_until": _iso(request.hold_until),
            "override_until": _iso(request.override_until),
        }
        request.override_until = self._merge_until(
            request.override_until, expires_at, already_standing=self._standing(request)
        )
        request.hold_until = command.hold_until
        after = {
            "hold_until": _iso(request.hold_until),
            "override_until": _iso(request.override_until),
        }
        return before, after, None

    async def _do_cancel(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        del expires_at
        if command.request_id is not None:
            request = await self._request(operator_id, command.request_id)
            before: dict[str, Any] = {
                "status": request.status,
                "trip_id": _or_none(request.trip_id),
            }
            # Through the request service, which skips the rider's stops and sends the
            # §6 notifications. A second cancel path here would be a second set of
            # bugs: S02 found the first one by stranding every assigned cab.
            await self.requests.cancel(
                operator_id=operator_id,
                request_id=request.id,
                actor_role=_role_of(actor),
                actor_user_id=actor_user_id or uuid.UUID(int=0),
                reason=command.note or f"Cancelled by supervisor ({command.reason_code})",
            )
            return before, {"status": request.status}, request.trip_id

        trip = await self._trip(operator_id, command.trip_id)
        before = {"status": trip.status, "riders": len(await self._riders_on(trip))}
        # Cancelling a trip does not cancel its riders: they still need a cab, and the
        # queue is where that is arranged.
        await self._requeue_trip(trip, actor, actor_user_id, reason="trip_cancelled")
        await self._close_trip(trip, actor, actor_user_id, reason="cancelled by supervisor")
        return before, {"status": trip.status}, trip.id

    async def _do_out_of_service(
        self,
        operator_id: uuid.UUID,
        command: OverrideCommand,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        expires_at: datetime | None,
    ) -> tuple[dict[str, Any], dict[str, Any], uuid.UUID | None]:
        assert command.vehicle_id is not None
        vehicle = await self._vehicle(operator_id, command.vehicle_id)
        before = {"status": vehicle.status}

        for trip in await self._live_trips_of(vehicle):
            await self._requeue_trip(trip, actor, actor_user_id, reason="vehicle_out_of_service")
            await self._close_trip(trip, actor, actor_user_id, reason="vehicle out of service")

        event = transition_vehicle(
            VehicleStatus(vehicle.status),
            VehicleStatus.out_of_service,
            actor=actor,
            reason=str(command.reason_code),
        )
        vehicle.status = event.to_status
        await self.session.flush()
        # `expires_at` is recorded and shown ("out until 14:00") but **nothing flips a
        # vehicle back**, unlike every other standing override. A lock that lapses
        # frees a decision; a cab that comes back by itself at 14:00 because a
        # timestamp passed is a cab in a workshop being sent to a rider. Somebody says
        # when it is back on the road.
        after = {"status": vehicle.status, "expires_at": _iso(expires_at)}
        return before, after, None

    # --- the moving parts the actions share ------------------------------------------

    async def _release_rider(
        self,
        request: RideRequest,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        reason: str,
    ) -> None:
        """Take a rider off the trip they are on and put them back in the queue."""
        if request.trip_id is None:
            return
        trip = await self.session.get(Trip, request.trip_id)
        await self._skip_stops_of(request)

        if request.status == str(RequestStatus.assigned):
            event = transition_request(
                RequestStatus.assigned,
                RequestStatus.queued,
                RequestContext(actor=actor, reason=reason, is_locked=request.is_locked),
            )
            request.status = event.to_status
            self.session.add(
                RideRequestEvent(
                    operator_id=request.operator_id,
                    request_id=request.id,
                    from_status=event.from_status,
                    to_status=event.to_status,
                    actor_type=actor_type_for(actor),
                    actor_user_id=actor_user_id,
                    reason=reason,
                    at=self.clock.now(),
                    data={"trip_id": str(request.trip_id)},
                )
            )
        request.trip_id = None
        await self.session.flush()

        if trip is not None and not await self._riders_on(trip):
            await self._close_trip(trip, actor, actor_user_id, reason="no riders left")

    async def _requeue_trip(
        self, trip: Trip, actor: Actor, actor_user_id: uuid.UUID | None, reason: str
    ) -> None:
        riders = await self._riders_on(trip)
        picked_up = [rider for rider in riders if rider.status == str(RequestStatus.picked_up)]
        if picked_up:
            # A rider in the cab cannot be put back in the queue by a supervisor: the
            # only edge out of `picked_up` towards `queued` exists for a breakdown,
            # where `abort` is the action (trip-lifecycle.md §2, `_guard_restrand`).
            raise Conflict(
                "That trip has riders on board; abort it rather than cancelling it",
                {"trip_id": str(trip.id), "on_board": len(picked_up)},
            )
        for rider in riders:
            await self._release_rider(rider, actor, actor_user_id, reason=reason)

    async def _close_trip(
        self, trip: Trip, actor: Actor, actor_user_id: uuid.UUID | None, reason: str
    ) -> None:
        """Cancel an emptied or abandoned trip and free its cab.

        Without this a trip keeps a vehicle `on_trip` with nobody aboard and no stop
        anybody will ever mark done, so the cab never becomes a candidate again.
        """
        if trip.status not in [str(TripStatus.planned), str(TripStatus.dispatched)]:
            return
        event = transition_trip(
            TripStatus(trip.status), TripStatus.cancelled, actor=actor, reason=reason
        )
        from_status = trip.status
        trip.status = event.to_status
        self.dispatch.record_trip_event(
            trip,
            from_status=from_status,
            to_status=trip.status,
            actor=actor,
            actor_user_id=actor_user_id,
            now=self.clock.now(),
            reason=reason,
            data={"action": "trip_cancelled"},
        )

        vehicle = await self.session.get(Vehicle, trip.vehicle_id)
        if vehicle is not None and vehicle.status == str(VehicleStatus.on_trip):
            vehicle.status = transition_vehicle(
                VehicleStatus.on_trip, VehicleStatus.available, actor=actor, reason=reason
            ).to_status
        await self.session.flush()

    async def _skip_stops_of(self, request: RideRequest) -> None:
        stops = (
            (
                await self.session.execute(
                    select(TripStop)
                    .where(TripStop.trip_id == request.trip_id)
                    .where(TripStop.request_id == request.id)
                )
            )
            .scalars()
            .all()
        )
        for stop in stops:
            if stop.status in {str(StopStatus.done), str(StopStatus.skipped)}:
                continue
            stop.status = transition_stop(
                StopStatus(stop.status), StopStatus.skipped, actor=Actor.system
            ).to_status

    # --- impact ------------------------------------------------------------------------

    async def _impact(self, operator_id: uuid.UUID, command: OverrideCommand) -> Impact:
        if command.action is OverrideAction.reassign:
            return await self._impact_of_reassign(operator_id, command)
        if command.action is OverrideAction.vehicle_out_of_service:
            return await self._impact_of_out_of_service(operator_id, command)
        if command.action is OverrideAction.cancel and command.trip_id is not None:
            trip = await self._trip(operator_id, command.trip_id)
            return Impact(affected_requests=await self._requeued(await self._riders_on(trip)))
        if command.action is OverrideAction.cancel:
            request = await self._request(operator_id, command.request_id)
            return Impact(
                affected_requests=[
                    AffectedRequest(
                        request_id=request.id,
                        employee_name=await self._name_of(request.employee_id),
                    )
                ]
            )
        # lock, unlock, force_priority, block_pooling and hold change what the platform
        # is allowed to do next, not where any cab is going now. An empty impact is the
        # honest answer, and a confirm screen that invents one teaches supervisors to
        # tap through it.
        return Impact()

    async def _impact_of_reassign(self, operator_id: uuid.UUID, command: OverrideCommand) -> Impact:
        request = await self._request(operator_id, command.request_id)
        assert command.target_vehicle_id is not None

        candidates = await self.dispatch.candidates(operator_id, request.id)
        target = next(
            (
                candidate
                for candidate in candidates
                if candidate.vehicle.id == command.target_vehicle_id
            ),
            None,
        )
        if target is None:
            # Not a candidate at all: either the cab is off duty or out of service, or
            # it has not reported a position recently enough for an honest ETA.
            vehicle = await self._vehicle(operator_id, command.target_vehicle_id)
            missing = (
                Violation.vehicle_unavailable
                if vehicle.status not in {str(VehicleStatus.available), str(VehicleStatus.on_trip)}
                else Violation.gps_stale
            )
            return Impact(hard_rule_violations=explain([missing]))

        names = await self._names_of(list(target.added_minutes) + [request.id])
        affected = [
            AffectedRequest(
                request_id=rider_id,
                employee_name=names.get(rider_id, ""),
                added_minutes=round(minutes, 1),
            )
            for rider_id, minutes in sorted(target.added_minutes.items(), key=lambda item: -item[1])
        ]
        affected.append(
            AffectedRequest(
                request_id=request.id,
                employee_name=names.get(request.id, ""),
                eta_change_minutes=await self._eta_change(request, target.eta_to_pickup_seconds),
            )
        )
        return Impact(affected_requests=affected, hard_rule_violations=explain(target.violations))

    async def _impact_of_out_of_service(
        self, operator_id: uuid.UUID, command: OverrideCommand
    ) -> Impact:
        vehicle = await self._vehicle(operator_id, command.vehicle_id)
        riders: list[RideRequest] = []
        for trip in await self._live_trips_of(vehicle):
            riders.extend(await self._riders_on(trip))
        return Impact(
            affected_requests=await self._requeued(riders),
            zones_without_available_vehicle=await self._zones_emptied_by(operator_id, vehicle.id),
        )

    async def _eta_change(self, request: RideRequest, new_eta_seconds: float) -> float | None:
        """Minutes later (or sooner) this rider would be collected.

        `None` when they are not on a cab yet: there is no before to subtract, and
        reporting the whole new ETA as a "change" would read as a delay.
        """
        if request.trip_id is None:
            return None
        stop = await self.session.scalar(
            select(TripStop)
            .where(TripStop.trip_id == request.trip_id)
            .where(TripStop.request_id == request.id)
            .where(TripStop.stop_type == "pickup")
        )
        current = stop.latest_eta or stop.planned_eta if stop is not None else None
        if current is None:
            return None
        now = self.clock.now()
        return round((new_eta_seconds - (current - now).total_seconds()) / 60.0, 1)

    async def _zones_emptied_by(self, operator_id: uuid.UUID, vehicle_id: uuid.UUID) -> list[str]:
        """Zones whose only available cab is the one being taken off the road (§3 rule 2).

        Only zones that have cover **now** are reported: a zone that was already empty
        is not something this override did, and listing it would bury the one that is.
        """
        rows = await self.session.execute(
            text(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (vehicle_id) vehicle_id, location
                    FROM location_ping
                    WHERE operator_id = :operator_id AND recorded_at >= :since
                    ORDER BY vehicle_id, recorded_at DESC
                )
                SELECT z.name AS zone_name, l.vehicle_id AS vehicle_id
                FROM zone z
                JOIN latest l ON ST_Contains(z.area::geometry, l.location::geometry)
                JOIN vehicle v ON v.id = l.vehicle_id
                WHERE z.operator_id = :operator_id
                  AND z.active
                  AND v.operator_id = :operator_id
                  AND v.status = :available
                """
            ).bindparams(
                operator_id=operator_id,
                since=self.clock.now() - POSITION_LOOKBACK,
                available=str(VehicleStatus.available),
            )
        )
        covered: dict[str, set[uuid.UUID]] = {}
        for row in rows:
            covered.setdefault(row.zone_name, set()).add(row.vehicle_id)
        return sorted(name for name, ids in covered.items() if ids == {vehicle_id})

    async def _requeued(self, riders: list[RideRequest]) -> list[AffectedRequest]:
        names = await self._names_of([rider.id for rider in riders])
        return [
            AffectedRequest(
                request_id=rider.id, employee_name=names.get(rider.id, ""), requeued=True
            )
            for rider in riders
        ]

    # --- loading ------------------------------------------------------------------------

    async def _request(self, operator_id: uuid.UUID, request_id: uuid.UUID | None) -> RideRequest:
        assert request_id is not None
        request = await self.session.scalar(
            select(RideRequest)
            .where(RideRequest.id == request_id)
            .where(RideRequest.operator_id == operator_id)
        )
        if request is None:
            raise NotFound("Request not found")
        return request

    async def _trip(self, operator_id: uuid.UUID, trip_id: uuid.UUID | None) -> Trip:
        assert trip_id is not None
        trip = await self.session.scalar(
            select(Trip).where(Trip.id == trip_id).where(Trip.operator_id == operator_id)
        )
        if trip is None:
            raise NotFound("Trip not found")
        return trip

    async def _vehicle(self, operator_id: uuid.UUID, vehicle_id: uuid.UUID | None) -> Vehicle:
        assert vehicle_id is not None
        vehicle = await self.session.scalar(
            select(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .where(Vehicle.operator_id == operator_id)
        )
        if vehicle is None:
            raise NotFound("Vehicle not found")
        return vehicle

    async def _live_trips_of(self, vehicle: Vehicle) -> list[Trip]:
        rows = (
            (
                await self.session.execute(
                    select(Trip)
                    .where(Trip.vehicle_id == vehicle.id)
                    .where(Trip.status.in_([str(status) for status in LIVE_TRIP_STATUSES]))
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def _riders_on(self, trip: Trip) -> list[RideRequest]:
        rows = (
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.trip_id == trip.id)
                    .where(RideRequest.status.in_([str(status) for status in ON_BOARD_STATUSES]))
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def _current_vehicle_of(self, request: RideRequest) -> uuid.UUID | None:
        if request.trip_id is None:
            return None
        trip = await self.session.get(Trip, request.trip_id)
        return trip.vehicle_id if trip is not None else None

    async def _names_of(self, request_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not request_ids:
            return {}
        rows = await self.session.execute(
            select(RideRequest.id, Employee.name)
            .join(Employee, Employee.id == RideRequest.employee_id)
            .where(RideRequest.id.in_(request_ids))
        )
        return {row[0]: row[1] for row in rows}

    async def _name_of(self, employee_id: uuid.UUID) -> str:
        employee = await self.session.get(Employee, employee_id)
        return employee.name if employee is not None else ""

    @staticmethod
    def _standing(request: RideRequest) -> bool:
        """Is some override already holding this request's `override_until`?"""
        return request.lock_vehicle_id is not None or request.forced_priority


def _role_of(actor: Actor) -> Role:
    """Overrides are a human action; the permission check has already proved which."""
    try:
        return Role(str(actor))
    except ValueError as exc:  # pragma: no cover - unreachable behind `require(...)`
        raise ValidationFailed(f"{actor} cannot apply an override") from exc


def _or_none(value: uuid.UUID | None) -> str | None:
    return str(value) if value is not None else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
