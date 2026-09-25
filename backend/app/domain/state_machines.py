"""State machines for ride requests, trips, stops and vehicles.

Every status change in the system goes through this module (`trip-lifecycle.md`, CLAUDE.md
hard rule 5). Direct writes to a status column are forbidden.

The functions here are pure: they take the current status plus the facts a guard needs,
and return a `TransitionEvent` describing what happened and who must be told. The service
layer persists the new status and the event in one transaction. Nothing here reads a
clock, a database or configuration — "now" and config values arrive as arguments.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.domain.enums import ActorType
from app.domain.errors import InvalidTransition, ValidationFailed

# ---------------------------------------------------------------------------
# Statuses (trip-lifecycle.md §1-§4)
# ---------------------------------------------------------------------------


class RequestStatus(StrEnum):
    requested = "requested"
    queued = "queued"
    suggested = "suggested"
    assigned = "assigned"
    picked_up = "picked_up"
    dropped = "dropped"
    no_show = "no_show"
    cancelled = "cancelled"
    expired = "expired"


class TripStatus(StrEnum):
    planned = "planned"
    dispatched = "dispatched"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    aborted = "aborted"


class StopStatus(StrEnum):
    pending = "pending"
    en_route = "en_route"
    arrived = "arrived"
    done = "done"
    skipped = "skipped"


class VehicleStatus(StrEnum):
    off_duty = "off_duty"
    available = "available"
    on_trip = "on_trip"
    out_of_service = "out_of_service"
    # `stale` is derived from GPS age, never stored (trip-lifecycle.md §4).


class StopKind(StrEnum):
    pickup = "pickup"
    drop = "drop"


class Actor(StrEnum):
    """Who caused the transition. Roles from `roles-and-permissions.md`, plus `system`."""

    employee = "employee"
    driver = "driver"
    supervisor = "supervisor"
    operator_admin = "operator_admin"
    client_admin = "client_admin"
    platform_admin = "platform_admin"
    system = "system"


class Recipient(StrEnum):
    """Notification targets (trip-lifecycle.md §6)."""

    employee = "employee"
    driver = "driver"
    previous_driver = "previous_driver"
    supervisor = "supervisor"
    operator_admin = "operator_admin"


SUPERVISORY_ACTORS = frozenset(
    {Actor.supervisor, Actor.operator_admin, Actor.platform_admin, Actor.system}
)

TERMINAL_REQUEST_STATUSES = frozenset(
    {
        RequestStatus.dropped,
        RequestStatus.no_show,
        RequestStatus.cancelled,
        RequestStatus.expired,
    }
)

TERMINAL_TRIP_STATUSES = frozenset({TripStatus.completed, TripStatus.cancelled, TripStatus.aborted})

TERMINAL_STOP_STATUSES = frozenset({StopStatus.done, StopStatus.skipped})


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    """What the service must persist, and who must be notified."""

    entity: str
    from_status: str
    to_status: str
    actor: Actor
    reason: str | None = None
    notify: tuple[Recipient, ...] = ()


# ---------------------------------------------------------------------------
# Allowed edges, straight from the diagrams
# ---------------------------------------------------------------------------

REQUEST_TRANSITIONS: dict[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.requested: frozenset({RequestStatus.queued, RequestStatus.cancelled}),
    RequestStatus.queued: frozenset(
        {
            RequestStatus.suggested,
            RequestStatus.assigned,
            RequestStatus.cancelled,
            RequestStatus.expired,
        }
    ),
    RequestStatus.suggested: frozenset(
        {RequestStatus.queued, RequestStatus.assigned, RequestStatus.cancelled}
    ),
    RequestStatus.assigned: frozenset(
        {
            RequestStatus.queued,
            RequestStatus.picked_up,
            RequestStatus.no_show,
            RequestStatus.cancelled,
        }
    ),
    RequestStatus.picked_up: frozenset({RequestStatus.dropped}),
    RequestStatus.dropped: frozenset(),
    RequestStatus.no_show: frozenset(),
    RequestStatus.cancelled: frozenset(),
    RequestStatus.expired: frozenset(),
}

TRIP_TRANSITIONS: dict[TripStatus, frozenset[TripStatus]] = {
    TripStatus.planned: frozenset({TripStatus.dispatched, TripStatus.cancelled}),
    TripStatus.dispatched: frozenset({TripStatus.in_progress, TripStatus.cancelled}),
    TripStatus.in_progress: frozenset({TripStatus.completed, TripStatus.aborted}),
    TripStatus.completed: frozenset(),
    TripStatus.cancelled: frozenset(),
    TripStatus.aborted: frozenset(),
}

STOP_TRANSITIONS: dict[StopStatus, frozenset[StopStatus]] = {
    StopStatus.pending: frozenset({StopStatus.en_route, StopStatus.skipped}),
    StopStatus.en_route: frozenset({StopStatus.arrived, StopStatus.skipped}),
    StopStatus.arrived: frozenset({StopStatus.done, StopStatus.skipped}),
    StopStatus.done: frozenset(),
    StopStatus.skipped: frozenset(),
}

VEHICLE_TRANSITIONS: dict[VehicleStatus, frozenset[VehicleStatus]] = {
    VehicleStatus.off_duty: frozenset({VehicleStatus.available}),
    VehicleStatus.available: frozenset(
        {VehicleStatus.on_trip, VehicleStatus.off_duty, VehicleStatus.out_of_service}
    ),
    VehicleStatus.on_trip: frozenset({VehicleStatus.available, VehicleStatus.out_of_service}),
    VehicleStatus.out_of_service: frozenset({VehicleStatus.available, VehicleStatus.off_duty}),
}


# ---------------------------------------------------------------------------
# Context for the guards
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Facts the request guards need. All supplied by the caller — nothing is read here."""

    actor: Actor = Actor.system
    reason: str | None = None
    # no_show: the stop must have been `arrived` long enough (trip-lifecycle.md §1).
    stop_status: StopStatus | None = None
    stop_arrived_at: datetime | None = None
    now: datetime | None = None
    no_show_wait_minutes: int = 5
    # A locked request may only move to another vehicle via supervisor override.
    is_locked: bool = False
    changes_vehicle: bool = False
    is_override: bool = False


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------


def transition_request(
    current: RequestStatus,
    target: RequestStatus,
    context: RequestContext | None = None,
) -> TransitionEvent:
    """Move a ride request, or raise `InvalidTransition`."""
    ctx = context or RequestContext()
    _check_edge("ride_request", current, target, REQUEST_TRANSITIONS)

    if ctx.is_locked and ctx.changes_vehicle and not ctx.is_override:
        raise InvalidTransition(
            "A locked request can only change vehicle through a supervisor override",
            {"from": str(current), "to": str(target)},
        )

    if target is RequestStatus.cancelled:
        _guard_cancel(ctx)
    if target is RequestStatus.no_show:
        _guard_no_show(ctx)
    if current is RequestStatus.assigned and target is RequestStatus.queued:
        _guard_unassign(ctx)

    return TransitionEvent(
        entity="ride_request",
        from_status=str(current),
        to_status=str(target),
        actor=ctx.actor,
        reason=ctx.reason,
        notify=_request_notifications(current, target, ctx),
    )


def transition_trip(
    current: TripStatus,
    target: TripStatus,
    actor: Actor = Actor.system,
    reason: str | None = None,
) -> TransitionEvent:
    """Move a trip, or raise `InvalidTransition`."""
    _check_edge("trip", current, target, TRIP_TRANSITIONS)

    notify: tuple[Recipient, ...] = ()
    if target is TripStatus.aborted:
        # "trip aborted -> supervisor, operator admin (high priority)"
        notify = (Recipient.supervisor, Recipient.operator_admin)
    elif target is TripStatus.cancelled:
        notify = (Recipient.driver, Recipient.employee)
    elif target is TripStatus.dispatched:
        notify = (Recipient.driver,)

    return TransitionEvent(
        entity="trip",
        from_status=str(current),
        to_status=str(target),
        actor=actor,
        reason=reason,
        notify=notify,
    )


def transition_stop(
    current: StopStatus,
    target: StopStatus,
    actor: Actor = Actor.driver,
    reason: str | None = None,
) -> TransitionEvent:
    """Move a stop, or raise `InvalidTransition`."""
    _check_edge("stop", current, target, STOP_TRANSITIONS)

    # "stop -> arrived: notify employee" (trip-lifecycle.md §6).
    notify: tuple[Recipient, ...] = (Recipient.employee,) if target is StopStatus.arrived else ()

    return TransitionEvent(
        entity="stop",
        from_status=str(current),
        to_status=str(target),
        actor=actor,
        reason=reason,
        notify=notify,
    )


def transition_vehicle(
    current: VehicleStatus,
    target: VehicleStatus,
    actor: Actor = Actor.driver,
    reason: str | None = None,
) -> TransitionEvent:
    """Move a vehicle, or raise `InvalidTransition`."""
    _check_edge("vehicle", current, target, VEHICLE_TRANSITIONS)
    return TransitionEvent(
        entity="vehicle",
        from_status=str(current),
        to_status=str(target),
        actor=actor,
        reason=reason,
    )


def request_status_for_stop_done(kind: StopKind) -> RequestStatus:
    """A pickup stop's `done` sets its request to `picked_up`; a drop's to `dropped`."""
    return RequestStatus.picked_up if kind is StopKind.pickup else RequestStatus.dropped


#: Every supervisory role is logged as `supervisor`; `actor_user_id` says which person.
_ACTOR_TYPES: dict[Actor, ActorType] = {
    Actor.employee: ActorType.employee,
    Actor.driver: ActorType.driver,
    Actor.supervisor: ActorType.supervisor,
    Actor.operator_admin: ActorType.supervisor,
    Actor.client_admin: ActorType.supervisor,
    Actor.platform_admin: ActorType.supervisor,
    Actor.system: ActorType.system,
}


def actor_type_for(actor: Actor) -> ActorType:
    """Map the domain actor onto the narrower set the event tables store."""
    return _ACTOR_TYPES.get(actor, ActorType.system)


def is_terminal_request(status: RequestStatus) -> bool:
    return status in TERMINAL_REQUEST_STATUSES


def is_terminal_trip(status: TripStatus) -> bool:
    return status in TERMINAL_TRIP_STATUSES


def is_terminal_stop(status: StopStatus) -> bool:
    return status in TERMINAL_STOP_STATUSES


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def _check_edge[StatusT: StrEnum](
    entity: str,
    current: StatusT,
    target: StatusT,
    table: Mapping[StatusT, frozenset[StatusT]],
) -> None:
    allowed = table[current]
    if target not in allowed:
        raise InvalidTransition(
            f"{entity} cannot go from {current} to {target}",
            {
                "entity": entity,
                "from": str(current),
                "to": str(target),
                "allowed": sorted(str(state) for state in allowed),
            },
        )


def _guard_cancel(ctx: RequestContext) -> None:
    """`cancel_reason` is required (trip-lifecycle.md §1).

    "Employee cancel is allowed until picked_up" needs no check here: the transition
    table has no `picked_up -> cancelled` edge, so it is already impossible.
    """
    if not ctx.reason:
        raise ValidationFailed("cancel_reason is required", {"to": "cancelled"})


def _guard_no_show(ctx: RequestContext) -> None:
    """A no-show needs the driver to have waited at an arrived stop."""
    if ctx.stop_status is not StopStatus.arrived:
        raise InvalidTransition(
            "no_show requires the pickup stop to be arrived",
            {"stop_status": str(ctx.stop_status) if ctx.stop_status else None},
        )
    if ctx.stop_arrived_at is None or ctx.now is None:
        raise ValidationFailed(
            "no_show needs the arrival time and the current time to check the wait"
        )

    waited = ctx.now - ctx.stop_arrived_at
    required = timedelta(minutes=ctx.no_show_wait_minutes)
    if waited < required:
        raise InvalidTransition(
            "no_show is not allowed before the driver has waited long enough",
            {
                "waited_seconds": int(waited.total_seconds()),
                "required_seconds": int(required.total_seconds()),
            },
        )


def _guard_unassign(ctx: RequestContext) -> None:
    """`assigned -> queued` only via supervisor reassign/unassign or trip cancellation."""
    if ctx.actor not in SUPERVISORY_ACTORS:
        raise InvalidTransition(
            "only a supervisor (or the system, on trip cancellation) can unassign a request",
            {"actor": str(ctx.actor)},
        )


def _request_notifications(
    current: RequestStatus, target: RequestStatus, ctx: RequestContext
) -> tuple[Recipient, ...]:
    """Notification targets from `trip-lifecycle.md` §6."""
    if target is RequestStatus.assigned:
        return (Recipient.employee, Recipient.driver)
    if current is RequestStatus.assigned and target is RequestStatus.queued:
        # Reassignment: the rider, the driver losing the trip, and whoever takes it.
        return (Recipient.employee, Recipient.previous_driver, Recipient.supervisor)
    if target is RequestStatus.cancelled:
        if ctx.actor is Actor.employee:
            return (Recipient.driver, Recipient.supervisor)
        return (Recipient.employee,)
    if target is RequestStatus.expired:
        return (Recipient.supervisor,)
    if target is RequestStatus.no_show:
        return (Recipient.employee, Recipient.supervisor)
    return ()
