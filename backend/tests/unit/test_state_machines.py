"""Table-driven tests for every allowed and disallowed transition (`trip-lifecycle.md`).

The allowed sets here are written out independently of the implementation tables, so a
typo in `state_machines.py` fails a test instead of being copied into it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.enums import ActorType
from app.domain.errors import InvalidTransition, ValidationFailed
from app.domain.state_machines import (
    _ACTOR_TYPES,
    Actor,
    Recipient,
    RequestContext,
    RequestStatus,
    StopKind,
    StopStatus,
    TripStatus,
    VehicleStatus,
    actor_type_for,
    is_terminal_request,
    is_terminal_stop,
    is_terminal_trip,
    request_status_for_stop_done,
    transition_request,
    transition_stop,
    transition_trip,
    transition_vehicle,
)

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)

R = RequestStatus
T = TripStatus
S = StopStatus
V = VehicleStatus

# --- expected edges, transcribed from the spec diagrams ----------------------

EXPECTED_REQUEST_EDGES: dict[RequestStatus, set[RequestStatus]] = {
    R.requested: {R.queued, R.cancelled},
    R.queued: {R.suggested, R.assigned, R.cancelled, R.expired},
    R.suggested: {R.queued, R.assigned, R.cancelled},
    R.assigned: {R.queued, R.picked_up, R.no_show, R.cancelled},
    R.picked_up: {R.dropped},
    R.dropped: set(),
    R.no_show: set(),
    R.cancelled: set(),
    R.expired: set(),
}

EXPECTED_TRIP_EDGES: dict[TripStatus, set[TripStatus]] = {
    T.planned: {T.dispatched, T.cancelled},
    T.dispatched: {T.in_progress, T.cancelled},
    T.in_progress: {T.completed, T.aborted},
    T.completed: set(),
    T.cancelled: set(),
    T.aborted: set(),
}

EXPECTED_STOP_EDGES: dict[StopStatus, set[StopStatus]] = {
    S.pending: {S.en_route, S.skipped},
    S.en_route: {S.arrived, S.skipped},
    S.arrived: {S.done, S.skipped},
    S.done: set(),
    S.skipped: set(),
}

EXPECTED_VEHICLE_EDGES: dict[VehicleStatus, set[VehicleStatus]] = {
    V.off_duty: {V.available},
    V.available: {V.on_trip, V.off_duty, V.out_of_service},
    V.on_trip: {V.available, V.out_of_service},
    V.out_of_service: {V.available, V.off_duty},
}


def satisfying_context(current: RequestStatus, target: RequestStatus) -> RequestContext:
    """A context that satisfies whichever guard applies to this edge."""
    if target is R.cancelled:
        return RequestContext(actor=Actor.supervisor, reason="no longer needed")
    if target is R.no_show:
        return RequestContext(
            actor=Actor.driver,
            stop_status=S.arrived,
            stop_arrived_at=NOW - timedelta(minutes=6),
            now=NOW,
        )
    if current is R.assigned and target is R.queued:
        return RequestContext(actor=Actor.supervisor)
    return RequestContext(actor=Actor.system)


# --- request: every cell of the matrix ---------------------------------------


@pytest.mark.parametrize("current", list(R))
@pytest.mark.parametrize("target", list(R))
def test_request_matrix(current: RequestStatus, target: RequestStatus) -> None:
    allowed = target in EXPECTED_REQUEST_EDGES[current]
    if allowed:
        event = transition_request(current, target, satisfying_context(current, target))
        assert event.from_status == str(current)
        assert event.to_status == str(target)
        assert event.entity == "ride_request"
    else:
        with pytest.raises(InvalidTransition):
            transition_request(current, target, satisfying_context(current, target))


@pytest.mark.parametrize("current", list(T))
@pytest.mark.parametrize("target", list(T))
def test_trip_matrix(current: TripStatus, target: TripStatus) -> None:
    if target in EXPECTED_TRIP_EDGES[current]:
        event = transition_trip(current, target)
        assert event.entity == "trip"
        assert event.to_status == str(target)
    else:
        with pytest.raises(InvalidTransition):
            transition_trip(current, target)


@pytest.mark.parametrize("current", list(S))
@pytest.mark.parametrize("target", list(S))
def test_stop_matrix(current: StopStatus, target: StopStatus) -> None:
    if target in EXPECTED_STOP_EDGES[current]:
        event = transition_stop(current, target)
        assert event.entity == "stop"
    else:
        with pytest.raises(InvalidTransition):
            transition_stop(current, target)


@pytest.mark.parametrize("current", list(V))
@pytest.mark.parametrize("target", list(V))
def test_vehicle_matrix(current: VehicleStatus, target: VehicleStatus) -> None:
    if target in EXPECTED_VEHICLE_EDGES[current]:
        event = transition_vehicle(current, target)
        assert event.entity == "vehicle"
    else:
        with pytest.raises(InvalidTransition):
            transition_vehicle(current, target)


def test_rejection_names_the_allowed_targets() -> None:
    with pytest.raises(InvalidTransition) as raised:
        transition_request(R.dropped, R.queued)
    details = raised.value.details
    assert details["from"] == "dropped"
    assert details["to"] == "queued"
    assert details["allowed"] == []


# --- cancellation ------------------------------------------------------------


def test_cancel_requires_a_reason() -> None:
    with pytest.raises(ValidationFailed, match="cancel_reason"):
        transition_request(R.queued, R.cancelled, RequestContext(actor=Actor.employee))


def test_cancel_with_a_reason_is_recorded() -> None:
    event = transition_request(
        R.queued, R.cancelled, RequestContext(actor=Actor.employee, reason="took the metro")
    )
    assert event.reason == "took the metro"
    assert event.actor is Actor.employee


def test_employee_cancel_notifies_driver_and_supervisor() -> None:
    event = transition_request(
        R.assigned, R.cancelled, RequestContext(actor=Actor.employee, reason="plans changed")
    )
    assert event.notify == (Recipient.driver, Recipient.supervisor)


def test_operator_cancel_notifies_the_employee() -> None:
    event = transition_request(
        R.assigned, R.cancelled, RequestContext(actor=Actor.supervisor, reason="no vehicle")
    )
    assert event.notify == (Recipient.employee,)


def test_cancel_after_pickup_is_impossible() -> None:
    """The spec allows employee cancel only until picked_up; the table enforces it."""
    with pytest.raises(InvalidTransition):
        transition_request(
            R.picked_up, R.cancelled, RequestContext(actor=Actor.employee, reason="changed mind")
        )


# --- no-show -----------------------------------------------------------------


def test_no_show_requires_an_arrived_stop() -> None:
    with pytest.raises(InvalidTransition, match="arrived"):
        transition_request(
            R.assigned,
            R.no_show,
            RequestContext(actor=Actor.driver, stop_status=S.en_route, now=NOW),
        )


def test_no_show_without_a_stop_status_is_rejected() -> None:
    with pytest.raises(InvalidTransition, match="arrived"):
        transition_request(R.assigned, R.no_show, RequestContext(actor=Actor.driver))


def test_no_show_needs_the_arrival_time() -> None:
    with pytest.raises(ValidationFailed, match="arrival time"):
        transition_request(
            R.assigned,
            R.no_show,
            RequestContext(actor=Actor.driver, stop_status=S.arrived, now=NOW),
        )


def test_no_show_needs_the_current_time() -> None:
    with pytest.raises(ValidationFailed, match="arrival time"):
        transition_request(
            R.assigned,
            R.no_show,
            RequestContext(
                actor=Actor.driver,
                stop_status=S.arrived,
                stop_arrived_at=NOW - timedelta(minutes=9),
            ),
        )


def test_no_show_is_blocked_before_the_wait_elapses() -> None:
    with pytest.raises(InvalidTransition, match="waited long enough") as raised:
        transition_request(
            R.assigned,
            R.no_show,
            RequestContext(
                actor=Actor.driver,
                stop_status=S.arrived,
                stop_arrived_at=NOW - timedelta(minutes=4),
                now=NOW,
                no_show_wait_minutes=5,
            ),
        )
    assert raised.value.details["waited_seconds"] == 240
    assert raised.value.details["required_seconds"] == 300


def test_no_show_allowed_exactly_at_the_wait_boundary() -> None:
    event = transition_request(
        R.assigned,
        R.no_show,
        RequestContext(
            actor=Actor.driver,
            stop_status=S.arrived,
            stop_arrived_at=NOW - timedelta(minutes=5),
            now=NOW,
            no_show_wait_minutes=5,
        ),
    )
    assert event.to_status == "no_show"
    assert event.notify == (Recipient.employee, Recipient.supervisor)


def test_no_show_wait_is_configurable() -> None:
    """`no_show_wait_minutes` is a config key, never a constant in the logic."""
    context = RequestContext(
        actor=Actor.driver,
        stop_status=S.arrived,
        stop_arrived_at=NOW - timedelta(minutes=2),
        now=NOW,
        no_show_wait_minutes=1,
    )
    assert transition_request(R.assigned, R.no_show, context).to_status == "no_show"


# --- unassign and locks ------------------------------------------------------


def test_only_a_supervisor_can_unassign() -> None:
    with pytest.raises(InvalidTransition, match="supervisor"):
        transition_request(R.assigned, R.queued, RequestContext(actor=Actor.driver))


def test_employee_cannot_unassign() -> None:
    with pytest.raises(InvalidTransition):
        transition_request(R.assigned, R.queued, RequestContext(actor=Actor.employee))


def test_system_can_unassign_on_trip_cancellation() -> None:
    event = transition_request(R.assigned, R.queued, RequestContext(actor=Actor.system))
    assert event.notify == (Recipient.employee, Recipient.previous_driver, Recipient.supervisor)


def test_locked_request_cannot_change_vehicle() -> None:
    with pytest.raises(InvalidTransition, match="locked"):
        transition_request(
            R.assigned,
            R.queued,
            RequestContext(actor=Actor.supervisor, is_locked=True, changes_vehicle=True),
        )


def test_locked_request_changes_vehicle_with_an_override() -> None:
    event = transition_request(
        R.assigned,
        R.queued,
        RequestContext(
            actor=Actor.supervisor, is_locked=True, changes_vehicle=True, is_override=True
        ),
    )
    assert event.to_status == "queued"


def test_locked_request_without_a_vehicle_change_is_fine() -> None:
    event = transition_request(
        R.assigned, R.picked_up, RequestContext(actor=Actor.driver, is_locked=True)
    )
    assert event.to_status == "picked_up"


# --- notifications (trip-lifecycle.md §6) ------------------------------------


def test_assignment_notifies_employee_and_driver() -> None:
    event = transition_request(R.queued, R.assigned)
    assert event.notify == (Recipient.employee, Recipient.driver)


def test_expiry_notifies_the_supervisor() -> None:
    assert transition_request(R.queued, R.expired).notify == (Recipient.supervisor,)


def test_pickup_notifies_nobody_extra() -> None:
    assert transition_request(R.assigned, R.picked_up).notify == ()


def test_arrived_stop_notifies_the_employee() -> None:
    assert transition_stop(S.en_route, S.arrived).notify == (Recipient.employee,)


def test_other_stop_changes_notify_nobody() -> None:
    assert transition_stop(S.pending, S.en_route).notify == ()


def test_abort_is_high_priority() -> None:
    event = transition_trip(T.in_progress, T.aborted, actor=Actor.driver, reason="breakdown")
    assert event.notify == (Recipient.supervisor, Recipient.operator_admin)
    assert event.reason == "breakdown"


def test_trip_cancellation_notifies_both_sides() -> None:
    assert transition_trip(T.planned, T.cancelled).notify == (
        Recipient.driver,
        Recipient.employee,
    )


def test_dispatch_notifies_the_driver() -> None:
    assert transition_trip(T.planned, T.dispatched).notify == (Recipient.driver,)


def test_trip_completion_notifies_nobody_extra() -> None:
    assert transition_trip(T.in_progress, T.completed).notify == ()


def test_vehicle_transitions_carry_no_notifications() -> None:
    event = transition_vehicle(V.available, V.out_of_service, reason="puncture")
    assert event.notify == ()
    assert event.reason == "puncture"


# --- stop/request coupling and terminals -------------------------------------


def test_pickup_stop_done_makes_the_rider_picked_up() -> None:
    assert request_status_for_stop_done(StopKind.pickup) is R.picked_up


def test_drop_stop_done_makes_the_rider_dropped() -> None:
    assert request_status_for_stop_done(StopKind.drop) is R.dropped


@pytest.mark.parametrize(
    ("status", "terminal"),
    [
        (R.dropped, True),
        (R.no_show, True),
        (R.cancelled, True),
        (R.expired, True),
        (R.queued, False),
        (R.assigned, False),
    ],
)
def test_request_terminal_states(status: RequestStatus, terminal: bool) -> None:
    assert is_terminal_request(status) is terminal


@pytest.mark.parametrize(
    ("status", "terminal"),
    [(T.completed, True), (T.cancelled, True), (T.aborted, True), (T.planned, False)],
)
def test_trip_terminal_states(status: TripStatus, terminal: bool) -> None:
    assert is_terminal_trip(status) is terminal


@pytest.mark.parametrize(
    ("status", "terminal"),
    [(S.done, True), (S.skipped, True), (S.arrived, False), (S.pending, False)],
)
def test_stop_terminal_states(status: StopStatus, terminal: bool) -> None:
    assert is_terminal_stop(status) is terminal


def test_no_status_may_transition_to_itself() -> None:
    for status in R:
        with pytest.raises(InvalidTransition):
            transition_request(status, status, satisfying_context(status, status))


def test_default_context_is_the_system_actor() -> None:
    assert transition_request(R.requested, R.queued).actor is Actor.system


def test_stale_is_not_a_stored_vehicle_status() -> None:
    """trip-lifecycle.md §4: `stale` is derived from GPS age, never written."""
    assert "stale" not in {str(status) for status in V}


# --- actors -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("actor", "expected"),
    [
        (Actor.employee, ActorType.employee),
        (Actor.driver, ActorType.driver),
        (Actor.supervisor, ActorType.supervisor),
        (Actor.system, ActorType.system),
    ],
)
def test_the_actor_maps_onto_what_the_event_table_stores(actor: Actor, expected: ActorType) -> None:
    assert actor_type_for(actor) is expected


@pytest.mark.parametrize("actor", [Actor.operator_admin, Actor.client_admin, Actor.platform_admin])
def test_every_supervisory_role_is_logged_as_supervisor(actor: Actor) -> None:
    """The event log answers "was a human overriding this"; `actor_user_id` says who."""
    assert actor_type_for(actor) is ActorType.supervisor


def test_every_actor_has_a_mapping() -> None:
    """A new Actor must not silently become `system` in the audit trail."""
    for actor in Actor:
        assert actor in _ACTOR_TYPES, f"{actor} has no ActorType mapping"
