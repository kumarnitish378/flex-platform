"""Ride request use cases (B09).

Every status change goes through `app/domain/state_machines.py` and writes an event
(CLAUDE.md hard rule 5); nothing here assigns to `request.status` directly except through
`_apply`.

Time comes from the injected `Clock` throughout — `requested_time` validation, `expires_at`
and the expiry sweep alike — so the simulator can drive a request from created to expired
in one step.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.geo import to_point as _point
from app.core.logging import get_logger
from app.domain.enums import (
    ActorType,
    AlertSeverity,
    AlertStatus,
    AlertType,
    Direction,
    RequestChannel,
    Role,
    Urgency,
)
from app.domain.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.domain.state_machines import (
    Actor,
    RequestContext,
    RequestStatus,
    TransitionEvent,
    actor_type_for,
    is_terminal_request,
    transition_request,
)
from app.modules.alerts.models import Alert
from app.modules.config.service import ConfigService
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest, RideRequestEvent

logger = get_logger(__name__)

# EMP-02: "a time up to 7 days ahead".
MAX_LEAD_TIME = timedelta(days=7)
# EMP-02: "two active requests with the same direction whose times are within 60 minutes".
DUPLICATE_WINDOW = timedelta(minutes=60)
# trip-lifecycle.md §6: "request near expiry (15 min before) -> Supervisor".
NEAR_EXPIRY_WARNING = timedelta(minutes=15)
# A little slack so a clock skew or a slow client does not reject a legitimate "now".
PAST_TOLERANCE = timedelta(minutes=5)

#: Statuses that still occupy a rider — used for the duplicate check.
ACTIVE_STATUSES = (
    RequestStatus.requested,
    RequestStatus.queued,
    RequestStatus.suggested,
    RequestStatus.assigned,
    RequestStatus.picked_up,
)


@dataclass(frozen=True, slots=True)
class ExpirySweep:
    """What one run of the scheduler did."""

    expired: int = 0
    warned: int = 0


class RideRequestService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock
        self.config = ConfigService(session, clock)

    # --- creation -----------------------------------------------------------

    async def create(
        self,
        operator_id: uuid.UUID,
        actor_role: Role,
        actor_user_id: uuid.UUID,
        direction: Direction,
        requested_time: datetime,
        employee_id: uuid.UUID | None = None,
        location: tuple[float, float] | None = None,
        landmark: str | None = None,
        urgency: Urgency = Urgency.medium,
        no_sharing: bool = False,
        caller_client_id: uuid.UUID | None = None,
    ) -> RideRequest:
        """Create a request, for oneself or on behalf of an employee."""
        employee = await self._resolve_employee(
            operator_id, actor_role, employee_id, actor_user_id, caller_client_id
        )
        self._validate_requested_time(requested_time)
        await self._reject_duplicate(employee, direction, requested_time)

        point = location or await self._home_of(employee)
        expiry_minutes = await self.config.get(operator_id, "request_expiry_minutes")

        request = RideRequest(
            operator_id=operator_id,
            client_id=employee.client_id,
            employee_id=employee.id,
            direction=direction,
            office_id=employee.office_id,
            location=_point(point[0], point[1]),
            landmark=landmark,
            requested_time=requested_time,
            urgency=urgency,
            no_sharing=no_sharing,
            status=RequestStatus.requested,
            channel=(
                RequestChannel.app if actor_role is Role.employee else RequestChannel.supervisor
            ),
            created_by_user_id=actor_user_id,
            # From the Clock, not the database: the simulator must be able to age this.
            expires_at=self.clock.now() + timedelta(minutes=int(expiry_minutes)),
        )
        self.session.add(request)
        await self.session.flush()

        self._record(request, None, RequestStatus.requested, _actor_for(actor_role), actor_user_id)

        # A request is only useful once validated, and validation just succeeded.
        self._apply(
            request,
            transition_request(
                RequestStatus.requested,
                RequestStatus.queued,
                RequestContext(actor=_actor_for(actor_role)),
            ),
            actor_user_id,
        )
        await self.session.flush()

        logger.info(
            "ride_request_created",
            request_id=str(request.id),
            employee_id=str(employee.id),
            direction=str(direction),
        )
        return request

    async def employee_for_user(
        self, operator_id: uuid.UUID, user_id: uuid.UUID
    ) -> Employee | None:
        """The employee record linked to a login, if there is one.

        The access token carries the user, not the employee: one person may be an
        employee at one client and a supervisor elsewhere, so the link is resolved per
        operator rather than baked into the token.
        """
        result = await self.session.execute(
            select(Employee)
            .where(Employee.operator_id == operator_id)
            .where(Employee.user_id == user_id)
        )
        return result.scalars().first()

    async def _resolve_employee(
        self,
        operator_id: uuid.UUID,
        actor_role: Role,
        employee_id: uuid.UUID | None,
        caller_user_id: uuid.UUID,
        caller_client_id: uuid.UUID | None,
    ) -> Employee:
        """Work out whose request this is, and whether the caller may make it."""
        if actor_role is Role.employee:
            # "employee_id ... ignored for employee role" (api-spec): a rider can only
            # ever request for themselves, whatever they put in the body.
            own = await self.employee_for_user(operator_id, caller_user_id)
            if own is None:
                raise Forbidden("This account is not linked to an employee record")
            target_id = own.id
        else:
            if employee_id is None:
                raise ValidationFailed("employee_id is required when creating on behalf")
            target_id = employee_id

        employee = (
            (
                await self.session.execute(
                    select(Employee)
                    .where(Employee.operator_id == operator_id)
                    .where(Employee.id == target_id)
                )
            )
            .scalars()
            .one_or_none()
        )

        if employee is None:
            raise NotFound("Employee not found", {"id": str(target_id)})
        if not employee.active:
            raise ValidationFailed("That employee is not active")
        if caller_client_id is not None and employee.client_id != caller_client_id:
            raise Forbidden("This role may only act for its own client's employees")
        return employee

    def _validate_requested_time(self, requested_time: datetime) -> None:
        if requested_time.tzinfo is None:
            raise ValidationFailed("requested_time must include a timezone")

        now = self.clock.now()
        if requested_time < now - PAST_TOLERANCE:
            raise ValidationFailed("requested_time is in the past", {"now": now.isoformat()})
        if requested_time > now + MAX_LEAD_TIME:
            raise ValidationFailed(
                "requested_time is more than 7 days ahead",
                {"max": (now + MAX_LEAD_TIME).isoformat()},
            )

    async def _reject_duplicate(
        self, employee: Employee, direction: Direction, requested_time: datetime
    ) -> None:
        """EMP-02: no two active same-direction requests within 60 minutes."""
        window_start = requested_time - DUPLICATE_WINDOW
        window_end = requested_time + DUPLICATE_WINDOW

        clash = (
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.employee_id == employee.id)
                    .where(RideRequest.direction == direction)
                    .where(RideRequest.status.in_(ACTIVE_STATUSES))
                    .where(RideRequest.requested_time > window_start)
                    .where(RideRequest.requested_time < window_end)
                )
            )
            .scalars()
            .first()
        )

        if clash is not None:
            raise Conflict(
                "You already have a request in that direction within an hour of this time",
                {
                    "existing_request_id": str(clash.id),
                    "existing_requested_time": clash.requested_time.isoformat(),
                },
            )

    async def _home_of(self, employee: Employee) -> tuple[float, float]:
        """The saved home pin, as (lat, lng)."""
        from geoalchemy2.elements import WKBElement
        from geoalchemy2.shape import to_shape

        stored = employee.home_location
        if not isinstance(stored, WKBElement):
            # Null for an employee imported without a home pin (B07 allows that).
            raise ValidationFailed("No location given and this employee has no home location saved")
        shape = to_shape(stored)
        return (shape.y, shape.x)

    # --- reads --------------------------------------------------------------

    async def get(
        self,
        operator_id: uuid.UUID,
        request_id: uuid.UUID,
        caller_employee_id: uuid.UUID | None = None,
        caller_client_id: uuid.UUID | None = None,
    ) -> RideRequest:
        request = (
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.operator_id == operator_id)
                    .where(RideRequest.id == request_id)
                )
            )
            .scalars()
            .one_or_none()
        )
        if request is None:
            raise NotFound("Ride request not found", {"id": str(request_id)})

        # "employee sees only their own requests" (roles-and-permissions.md).
        if caller_employee_id is not None and request.employee_id != caller_employee_id:
            raise NotFound("Ride request not found", {"id": str(request_id)})
        if caller_client_id is not None and request.client_id != caller_client_id:
            raise NotFound("Ride request not found", {"id": str(request_id)})
        return request

    async def list_mine(
        self, operator_id: uuid.UUID, employee_id: uuid.UUID, limit: int = 50
    ) -> list[RideRequest]:
        result = await self.session.execute(
            select(RideRequest)
            .where(RideRequest.operator_id == operator_id)
            .where(RideRequest.employee_id == employee_id)
            .order_by(RideRequest.requested_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # --- cancellation -------------------------------------------------------

    async def cancel(
        self,
        operator_id: uuid.UUID,
        request_id: uuid.UUID,
        actor_role: Role,
        actor_user_id: uuid.UUID,
        reason: str | None,
        caller_employee_id: uuid.UUID | None = None,
        caller_client_id: uuid.UUID | None = None,
    ) -> RideRequest:
        request = await self.get(operator_id, request_id, caller_employee_id, caller_client_id)

        # The state machine requires a reason for every cancellation. An employee
        # cancelling their own pending request should not have to invent one, so supply
        # a truthful default rather than forcing the client to send filler.
        effective_reason = reason or (
            "Cancelled by employee" if actor_role is Role.employee else "Cancelled by operator"
        )

        event = transition_request(
            RequestStatus(request.status),
            RequestStatus.cancelled,
            RequestContext(
                actor=_actor_for(actor_role),
                reason=effective_reason,
                is_locked=request.is_locked,
            ),
        )
        request.cancel_reason = effective_reason
        self._apply(request, event, actor_user_id)
        await self.session.flush()

        logger.info("ride_request_cancelled", request_id=str(request.id), actor=str(actor_role))
        return request

    # --- expiry (Clock-driven, no wall-clock sleep) -------------------------

    async def run_due_expiries(self, operator_id: uuid.UUID | None = None) -> ExpirySweep:
        """Expire what is due and warn about what is nearly due.

        Called by the Celery beat loop in production and by `/simctl/clock` in sim
        (`architecture.md` §3.3), so advancing a simulated clock really does expire
        requests. It checks due items rather than sleeping.
        """
        now = self.clock.now()
        expired = await self._expire_due(now, operator_id)
        warned = await self._warn_near_expiry(now, operator_id)
        if expired or warned:
            logger.info("expiry_sweep", expired=expired, warned=warned, at=now.isoformat())
        return ExpirySweep(expired=expired, warned=warned)

    async def _expire_due(self, now: datetime, operator_id: uuid.UUID | None) -> int:
        query = (
            select(RideRequest)
            .where(RideRequest.status == RequestStatus.queued)
            .where(RideRequest.expires_at <= now)
        )
        if operator_id is not None:
            query = query.where(RideRequest.operator_id == operator_id)

        count = 0
        for request in (await self.session.execute(query)).scalars().all():
            self._apply(
                request,
                transition_request(
                    RequestStatus.queued,
                    RequestStatus.expired,
                    RequestContext(actor=Actor.system, reason="Not assigned before expiry"),
                ),
                actor_user_id=None,
            )
            count += 1

        if count:
            await self.session.flush()
        return count

    async def _warn_near_expiry(self, now: datetime, operator_id: uuid.UUID | None) -> int:
        """Raise one alert per request, 15 minutes before it expires."""
        query = (
            select(RideRequest)
            .where(RideRequest.status == RequestStatus.queued)
            .where(RideRequest.near_expiry_alerted_at.is_(None))
            .where(RideRequest.expires_at > now)
            .where(RideRequest.expires_at <= now + NEAR_EXPIRY_WARNING)
        )
        if operator_id is not None:
            query = query.where(RideRequest.operator_id == operator_id)

        count = 0
        for request in (await self.session.execute(query)).scalars().all():
            self.session.add(
                Alert(
                    operator_id=request.operator_id,
                    type=AlertType.request_near_expiry,
                    severity=AlertSeverity.warning,
                    request_id=request.id,
                    status=AlertStatus.open,
                    data={
                        "expires_at": request.expires_at.isoformat(),
                        "employee_id": str(request.employee_id),
                    },
                )
            )
            request.near_expiry_alerted_at = now
            count += 1

        if count:
            await self.session.flush()
        return count

    # --- internals ----------------------------------------------------------

    def _apply(
        self, request: RideRequest, event: TransitionEvent, actor_user_id: uuid.UUID | None
    ) -> None:
        """Persist a transition and its event together. The only writer of `status`."""
        request.status = event.to_status
        self._record(
            request,
            event.from_status,
            RequestStatus(event.to_status),
            event.actor,
            actor_user_id,
            reason=event.reason,
            notify=[str(recipient) for recipient in event.notify],
        )

    def _record(
        self,
        request: RideRequest,
        from_status: str | None,
        to_status: RequestStatus,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        reason: str | None = None,
        notify: list[str] | None = None,
    ) -> None:
        self.session.add(
            RideRequestEvent(
                operator_id=request.operator_id,
                request_id=request.id,
                from_status=from_status,
                to_status=str(to_status),
                actor_type=_actor_type(actor),
                actor_user_id=actor_user_id,
                reason=reason,
                at=self.clock.now(),
                data={"notify": notify} if notify else None,
            )
        )

    async def events_for(self, request_id: uuid.UUID) -> list[RideRequestEvent]:
        result = await self.session.execute(
            select(RideRequestEvent)
            .where(RideRequestEvent.request_id == request_id)
            .order_by(RideRequestEvent.at, RideRequestEvent.created_at)
        )
        return list(result.scalars().all())


def is_terminal(status: str) -> bool:
    return is_terminal_request(RequestStatus(status))


def _actor_for(role: Role) -> Actor:
    return Actor(str(role))


def _actor_type(actor: Actor) -> ActorType:
    return actor_type_for(actor)
