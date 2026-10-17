"""Semi-auto assignment and the failsafe sweep (`control-model.md` §1, §4 — B25).

Two halves of one piece of due work, run by one sweep:

1. **Offer.** A queued request in a `semi_auto` scope with no live offer gets the top
   suggestions and a timer.
2. **Fire.** An offer whose timer has run out is assigned, or escalated once and then
   assigned, per `failsafe_action`.

Both are **Clock-driven**, like every other sweep in this system: `/simctl/clock` runs
them when the simulator jumps time, and the Celery beat runs them in production. That is
ADR-0008's whole point, and the guard in `tests/unit/test_due_work_schedule.py` fails if
the two ever diverge - which is the B20 failure, where three sweeps had one caller
between them and none of it ran in production.

**Nothing here assigns a suggestion without re-checking the hard rules.** The world
moves between the offer and the timeout: the cab gets another rider, goes off duty, or
drifts out of range. Assigning a stale offer because it was the best answer four minutes
ago is exactly the failure a human would have caught.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.events import EventPublisher, NullEventPublisher
from app.core.logging import get_logger
from app.core.settings import Settings
from app.domain.enums import ActorType, AlertType, Urgency
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.failsafe import (
    FailsafeAction,
    FailsafeOutcome,
    SuggestionStatus,
    decide,
    timeout_for,
)
from app.domain.modes import Mode
from app.domain.state_machines import Actor, RequestStatus
from app.modules.config.service import ConfigService
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.modes.service import ModeService
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest

logger = get_logger(__name__)

#: How many of the ranked candidates become an offer. `control-model.md` §1: "the
#: system suggests top 3 with reasons".
OFFER_COUNT = 3

#: Statuses a request can be in and still want a suggestion.
OFFERABLE_STATUSES = (str(RequestStatus.requested), str(RequestStatus.queued))


class SupervisorDecision(StrEnum):
    """`control-model.md` §1: "one-tap approve or override"."""

    approve = "approve"
    choose_other = "choose_other"
    reject = "reject"


@dataclass(frozen=True, slots=True)
class DecisionResult:
    suggestion_id: uuid.UUID
    decision: SupervisorDecision
    status: SuggestionStatus
    trip_id: uuid.UUID | None


@dataclass(frozen=True, slots=True)
class SemiAutoSweep:
    """What one pass did. Every number is something an operator could ask about."""

    offered: int = 0
    assigned: int = 0
    escalated: int = 0
    #: Offers withdrawn because the hard rules stopped holding. Counted separately from
    #: rejections: the supervisor never turned these down, the world moved.
    superseded: int = 0
    no_candidate: int = 0


class SemiAutoService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        dispatch: DispatchService,
        settings: Settings | None = None,
        events: EventPublisher | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.dispatch = dispatch
        self.settings = settings
        self.events = events or NullEventPublisher()
        self.config = ConfigService(session, clock)
        self.modes = ModeService(session, clock)

    # --- the sweep ----------------------------------------------------------

    async def run_due_semi_auto(self, operator_id: uuid.UUID | None = None) -> SemiAutoSweep:
        """One pass: offer what needs offering, fire what has timed out.

        Named `run_due_*` so the schedule guard sees it: any sweep reachable from a
        clock jump must also be reachable from the beat.
        """
        offered, no_candidate = await self._offer_due(operator_id)
        fired = await self._fire_due(operator_id)

        sweep = SemiAutoSweep(
            offered=offered,
            no_candidate=no_candidate,
            assigned=fired.assigned,
            escalated=fired.escalated,
            superseded=fired.superseded,
        )
        if any((sweep.offered, sweep.assigned, sweep.escalated, sweep.superseded)):
            logger.info(
                "semi_auto_sweep",
                offered=sweep.offered,
                assigned=sweep.assigned,
                escalated=sweep.escalated,
                superseded=sweep.superseded,
            )
        return sweep

    async def _offer_due(self, operator_id: uuid.UUID | None) -> tuple[int, int]:
        """Suggest vehicles for queued requests in a `semi_auto` scope."""
        now = self.clock.now()
        query = (
            select(RideRequest)
            .where(RideRequest.status.in_(OFFERABLE_STATUSES))
            .where(
                # A held request waits where the supervisor put it (`control-model.md` §3,
                # B26). This is the automatic path the hold exists to stop: without it the
                # sweep offers a cab the next time it runs and the hold means nothing.
                (RideRequest.hold_until.is_(None)) | (RideRequest.hold_until <= now)
            )
        )
        if operator_id is not None:
            query = query.where(RideRequest.operator_id == operator_id)
        requests = list((await self.session.execute(query)).scalars().all())
        if not requests:
            return 0, 0

        with_offers = await self._requests_with_live_offers({request.id for request in requests})

        offered = 0
        no_candidate = 0
        for request in requests:
            if request.id in with_offers:
                continue
            resolution = await self.modes.resolve_for_request(request)
            if resolution.mode is not Mode.semi_auto:
                continue
            made = await self.offer(request)
            if made:
                offered += 1
            else:
                no_candidate += 1
        return offered, no_candidate

    async def offers(
        self,
        operator_id: uuid.UUID,
        status: str = str(SuggestionStatus.offered),
        request_id: uuid.UUID | None = None,
    ) -> list[Suggestion]:
        """The stored offers in one state, newest first (B25's record, read at last).

        The table has existed since B25 and nothing could read it, which made
        `/suggestions/{id}/decision` uncallable by any client: the id it needs was
        never returned anywhere. Found writing M09's supervisor, which has to answer
        offers rather than make assignments.
        """
        query = (
            select(Suggestion)
            .where(Suggestion.operator_id == operator_id)
            .where(Suggestion.status == status)
            .order_by(Suggestion.offered_at.desc(), Suggestion.rank)
        )
        if request_id is not None:
            query = query.where(Suggestion.request_id == request_id)
        return list((await self.session.execute(query)).scalars().all())

    async def offer(self, request: RideRequest) -> list[Suggestion]:
        """Record the top suggestions for this request and start the timer.

        Returns an empty list when nothing is permitted - which is not an error. §2's
        rules are filters here, and "no cab may take this" is a real answer that leaves
        the request queued for a human. The escalation ladder in B09/ADR-0019 is what
        notices a request nobody serves.
        """
        candidates = await self.dispatch.suggestions(
            request.operator_id, request.id, limit=OFFER_COUNT
        )
        if not candidates:
            return []

        now = self.clock.now()
        due_at = now + await self._timeout_for(request)
        made: list[Suggestion] = []
        for rank, candidate in enumerate(candidates, start=1):
            suggestion = Suggestion(
                id=uuid.uuid4(),
                operator_id=request.operator_id,
                request_id=request.id,
                vehicle_id=candidate.vehicle.id,
                trip_id=candidate.trip_id,
                rank=rank,
                cost=candidate.cost or 0.0,
                reasons=list(candidate.reasons),
                status=str(SuggestionStatus.offered),
                offered_at=now,
                failsafe_due_at=due_at,
            )
            self.session.add(suggestion)
            made.append(suggestion)
        await self.session.flush()

        logger.info(
            "suggestions_offered",
            request_id=str(request.id),
            count=len(made),
            due_at=due_at.isoformat(),
        )
        return made

    async def _fire_due(self, operator_id: uuid.UUID | None) -> SemiAutoSweep:
        """Act on every offer whose timer has run out."""
        now = self.clock.now()
        query = (
            select(Suggestion)
            .where(Suggestion.status == str(SuggestionStatus.offered))
            .where(Suggestion.rank == 1)
            .where(Suggestion.failsafe_due_at <= now)
        )
        if operator_id is not None:
            query = query.where(Suggestion.operator_id == operator_id)
        due = list((await self.session.execute(query)).scalars().all())

        assigned = escalated = superseded = 0
        for suggestion in due:
            request = await self.session.get(RideRequest, suggestion.request_id)
            if request is None or request.status not in OFFERABLE_STATUSES:
                # Somebody assigned or cancelled it by hand. Nothing to do, and the
                # offer should stop being listed as open.
                await self._close(suggestion, SuggestionStatus.superseded)
                superseded += 1
                continue

            action = FailsafeAction(
                str(await self.config.get(request.operator_id, "failsafe_action"))
            )
            decision = decide(
                offered_at=suggestion.offered_at,
                now=now,
                timeout=await self._timeout_for(request),
                action=action,
                already_escalated=suggestion.escalated_at is not None,
                supervisor_online=await self._supervisor_online(request.operator_id),
            )

            if decision.outcome is FailsafeOutcome.wait:
                continue
            if decision.outcome is FailsafeOutcome.escalate:
                await self._escalate(suggestion, request, decision.next_due_at)
                escalated += 1
                continue

            if await self._assign_from(suggestion, request):
                assigned += 1
            else:
                superseded += 1

        return SemiAutoSweep(assigned=assigned, escalated=escalated, superseded=superseded)

    # --- a supervisor answering ---------------------------------------------

    async def decide_on(
        self,
        operator_id: uuid.UUID,
        suggestion_id: uuid.UUID,
        decision: SupervisorDecision,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        vehicle_id: uuid.UUID | None = None,
        note: str | None = None,
    ) -> DecisionResult:
        """Answer one suggestion (`control-model.md` §1: approve, change, or reject).

        `choose_other` is recorded as a **rejection** of what was offered, with the
        chosen vehicle noted. It is a different ride, and counting it as acceptance
        would let the Phase 2 metric flatter itself: the supervisor looked at the
        system's answer and picked something else.
        """
        if decision is SupervisorDecision.reject:
            await self.reject(operator_id, suggestion_id, actor_user_id, note)
            return DecisionResult(suggestion_id, decision, SuggestionStatus.rejected, None)

        if decision is SupervisorDecision.choose_other:
            if vehicle_id is None:
                raise ValidationFailed(
                    "choose_other needs the vehicle_id you are choosing instead",
                    {"decision": str(decision)},
                )
            suggestion = await self._open_suggestion(operator_id, suggestion_id)
            request = await self.session.get(RideRequest, suggestion.request_id)
            if request is None:
                raise NotFound("Ride request not found")
            trip = await self.dispatch.assign(
                operator_id=operator_id,
                request_id=request.id,
                vehicle_id=vehicle_id,
                actor=actor,
                actor_user_id=actor_user_id,
            )
            await self._close(
                suggestion,
                SuggestionStatus.rejected,
                by=actor_user_id,
                at=self.clock.now(),
                note=note or f"chose vehicle {vehicle_id} instead",
            )
            await self._close_siblings(suggestion, SuggestionStatus.superseded)
            logger.info(
                "suggestion_overridden",
                suggestion_id=str(suggestion_id),
                chosen_vehicle_id=str(vehicle_id),
            )
            return DecisionResult(suggestion_id, decision, SuggestionStatus.rejected, trip.id)

        trip_id = await self.accept(operator_id, suggestion_id, actor, actor_user_id)
        return DecisionResult(suggestion_id, decision, SuggestionStatus.accepted, trip_id)

    async def accept(
        self,
        operator_id: uuid.UUID,
        suggestion_id: uuid.UUID,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
    ) -> uuid.UUID:
        """Take the system's recommendation. Returns the trip id.

        The hard rules are re-checked here too, not only in the failsafe: a supervisor
        reading a screen that is two minutes old is looking at the same stale offer the
        sweep would have refused.
        """
        suggestion = await self._open_suggestion(operator_id, suggestion_id)
        request = await self.session.get(RideRequest, suggestion.request_id)
        if request is None:
            raise NotFound("Ride request not found")

        trip = await self.dispatch.assign(
            operator_id=operator_id,
            request_id=request.id,
            vehicle_id=suggestion.vehicle_id,
            actor=actor,
            actor_user_id=actor_user_id,
            trip_id=suggestion.trip_id,
        )
        await self._close(
            suggestion, SuggestionStatus.accepted, by=actor_user_id, at=self.clock.now()
        )
        await self._close_siblings(suggestion, SuggestionStatus.superseded)
        logger.info("suggestion_accepted", suggestion_id=str(suggestion.id), trip_id=str(trip.id))
        return trip.id

    async def reject(
        self,
        operator_id: uuid.UUID,
        suggestion_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        note: str | None = None,
    ) -> None:
        """Turn one suggestion down.

        The request stays queued and the remaining offers stay open: rejecting the
        system's first choice is not the same as rejecting all three, and treating it
        that way would push a supervisor back to the manual board for no reason.
        """
        suggestion = await self._open_suggestion(operator_id, suggestion_id)
        await self._close(
            suggestion,
            SuggestionStatus.rejected,
            by=actor_user_id,
            at=self.clock.now(),
            note=note,
        )
        logger.info("suggestion_rejected", suggestion_id=str(suggestion.id), note=note)

    async def open_for(self, operator_id: uuid.UUID, request_id: uuid.UUID) -> list[Suggestion]:
        rows = (
            await self.session.execute(
                select(Suggestion)
                .where(Suggestion.operator_id == operator_id)
                .where(Suggestion.request_id == request_id)
                .where(Suggestion.status == str(SuggestionStatus.offered))
                .order_by(Suggestion.rank)
            )
        ).scalars()
        return list(rows)

    # --- helpers ------------------------------------------------------------

    async def _assign_from(self, suggestion: Suggestion, request: RideRequest) -> bool:
        """Assign the offered vehicle, if the rules still hold. True when it happened."""
        still_valid = [
            candidate
            for candidate in await self.dispatch.suggestions(
                request.operator_id, request.id, limit=OFFER_COUNT
            )
            if candidate.vehicle.id == suggestion.vehicle_id
        ]
        if not still_valid:
            # The world moved. Withdraw rather than assign: the next sweep offers again
            # from the cabs that are actually available now.
            await self._close(suggestion, SuggestionStatus.superseded)
            await self._close_siblings(suggestion, SuggestionStatus.superseded)
            logger.info(
                "suggestion_superseded",
                suggestion_id=str(suggestion.id),
                reason="hard rules no longer hold",
            )
            return False

        try:
            trip = await self.dispatch.assign(
                operator_id=request.operator_id,
                request_id=request.id,
                vehicle_id=suggestion.vehicle_id,
                actor=Actor(str(ActorType.system_failsafe)),
                actor_user_id=None,
                trip_id=suggestion.trip_id,
            )
        except (Conflict, NotFound) as exc:
            logger.info(
                "failsafe_assign_refused",
                suggestion_id=str(suggestion.id),
                error=type(exc).__name__,
            )
            await self._close(suggestion, SuggestionStatus.superseded)
            return False

        await self._close(suggestion, SuggestionStatus.failsafe_assigned, at=self.clock.now())
        await self._close_siblings(suggestion, SuggestionStatus.superseded)
        logger.info(
            "failsafe_assigned",
            suggestion_id=str(suggestion.id),
            trip_id=str(trip.id),
            actor=str(ActorType.system_failsafe),
        )
        return True

    async def _escalate(
        self, suggestion: Suggestion, request: RideRequest, next_due_at: datetime | None
    ) -> None:
        """Alert, keep the offer open, and give it one more timeout."""
        from app.modules.alerts.service import AlertService

        suggestion.escalated_at = self.clock.now()
        if next_due_at is not None:
            suggestion.failsafe_due_at = next_due_at
        await self.session.flush()

        # `AlertType.failsafe` already exists and already maps to `warning`; inventing
        # a `suggestion_unanswered` type would split the same event across two names.
        await AlertService(self.session, self.clock, self.events).raise_alert(
            request.operator_id,
            AlertType.failsafe,
            request_id=request.id,
            data={
                "suggestion_id": str(suggestion.id),
                "vehicle_id": str(suggestion.vehicle_id),
                # When it assigns itself if still nobody answers - the one fact a
                # supervisor reading this alert actually needs.
                "assigns_at": next_due_at.isoformat() if next_due_at else None,
            },
            dedupe=True,
        )
        logger.info("suggestion_escalated", suggestion_id=str(suggestion.id))

    async def _timeout_for(self, request: RideRequest) -> timedelta:
        employee = await self.session.get(Employee, request.employee_id)
        base = int(await self.config.get(request.operator_id, "failsafe_timeout_seconds"))
        return timeout_for(
            base,
            urgency=Urgency(request.urgency),
            is_vip=bool(employee.is_vip) if employee is not None else False,
        )

    async def _supervisor_online(self, operator_id: uuid.UUID) -> bool:
        """Is anyone watching this operator's board?

        **Always true for now (OQ-37).** `control-model.md` §4 shortcuts the timeout
        when no supervisor is logged in, and this platform has no presence tracking -
        the WebSocket hub knows its own connections but keeps nothing shared, so two
        API processes cannot answer the question between them.

        Answering "yes" is the safe wrong answer: the failsafe waits its full timeout
        rather than firing at once. Answering "no" by default would auto-assign
        instantly in every semi-auto scope, which is full-auto wearing semi-auto's name.
        """
        del operator_id
        return True

    async def _requests_with_live_offers(self, request_ids: set[uuid.UUID]) -> set[uuid.UUID]:
        if not request_ids:
            return set()
        rows = (
            await self.session.execute(
                select(Suggestion.request_id)
                .where(Suggestion.request_id.in_(request_ids))
                .where(Suggestion.status == str(SuggestionStatus.offered))
            )
        ).scalars()
        return set(rows)

    async def _open_suggestion(
        self, operator_id: uuid.UUID, suggestion_id: uuid.UUID
    ) -> Suggestion:
        suggestion = (
            (
                await self.session.execute(
                    select(Suggestion)
                    .where(Suggestion.operator_id == operator_id)
                    .where(Suggestion.id == suggestion_id)
                )
            )
            .scalars()
            .first()
        )
        if suggestion is None:
            raise NotFound("Suggestion not found")
        if suggestion.status != str(SuggestionStatus.offered):
            raise Conflict(f"This suggestion was already {suggestion.status}")
        return suggestion

    async def _close(
        self,
        suggestion: Suggestion,
        status: SuggestionStatus,
        *,
        by: uuid.UUID | None = None,
        at: datetime | None = None,
        note: str | None = None,
    ) -> None:
        suggestion.status = str(status)
        suggestion.decided_at = at
        suggestion.decided_by = by
        suggestion.decided_note = note
        await self.session.flush()

    async def _close_siblings(self, suggestion: Suggestion, status: SuggestionStatus) -> None:
        """The other ranks for the same request. One answer settles all of them."""
        siblings = (
            (
                await self.session.execute(
                    select(Suggestion)
                    .where(Suggestion.request_id == suggestion.request_id)
                    .where(Suggestion.id != suggestion.id)
                    .where(Suggestion.status == str(SuggestionStatus.offered))
                )
            )
            .scalars()
            .all()
        )
        for sibling in siblings:
            sibling.status = str(status)
        await self.session.flush()
