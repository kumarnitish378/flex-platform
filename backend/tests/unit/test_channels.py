"""Channel names and who may read them (B13, `websocket-protocol.md` section 3).

The security-critical half of the realtime feature, and pure, so it is tested here rather
than through a socket: "may this employee watch this cab" is a rule, not a transport.
"""

from __future__ import annotations

import uuid

import pytest

from app.domain.enums import Role
from app.modules.auth.permissions import Permission, has_permission
from app.modules.realtime.channels import (
    OperatorChannel,
    Refusal,
    Subscriber,
    Topic,
    TripChannel,
    TripMembership,
    UserChannel,
    may_subscribe,
    parse,
    permission_for,
)

OPERATOR = uuid.UUID("11111111-1111-4111-8111-111111111111")
OTHER_OPERATOR = uuid.UUID("22222222-2222-4222-8222-222222222222")
TRIP = uuid.UUID("33333333-3333-4333-8333-333333333333")
USER = uuid.UUID("44444444-4444-4444-8444-444444444444")
CLIENT = uuid.UUID("55555555-5555-4555-8555-555555555555")


def supervisor(**overrides: object) -> Subscriber:
    base: dict[str, object] = {
        "user_id": USER,
        "role": str(Role.supervisor),
        "operator_id": OPERATOR,
        "client_id": None,
    }
    base.update(overrides)
    return Subscriber(**base)  # type: ignore[arg-type]


def allowed(subscriber: Subscriber, channel: object) -> bool:
    permission = permission_for(channel)  # type: ignore[arg-type]
    return permission is None or has_permission(Role(subscriber.role), permission)


def decide(channel: object, subscriber: Subscriber, membership: TripMembership | None = None):  # type: ignore[no-untyped-def]
    return may_subscribe(channel, subscriber, allowed(subscriber, channel), membership)  # type: ignore[arg-type]


# --- parsing ---------------------------------------------------------------------


def test_an_operator_channel_parses() -> None:
    channel = parse(f"operator.{OPERATOR}.vehicles")
    assert channel == OperatorChannel(OPERATOR, Topic.vehicles)


@pytest.mark.parametrize("topic", ["vehicles", "requests", "alerts"])
def test_every_documented_topic_parses(topic: str) -> None:
    assert parse(f"operator.{OPERATOR}.{topic}") is not None


def test_a_trip_channel_parses() -> None:
    assert parse(f"trip.{TRIP}") == TripChannel(TRIP)


def test_a_user_channel_parses() -> None:
    assert parse(f"user.{USER}") == UserChannel(USER)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "operator",
        "operator.not-a-uuid.vehicles",
        f"operator.{OPERATOR}",
        f"operator.{OPERATOR}.payroll",
        f"operator.{OPERATOR}.vehicles.extra",
        "trip.not-a-uuid",
        "user.",
        "admin.everything",
        f"OPERATOR.{OPERATOR}.vehicles",
    ],
)
def test_a_name_we_do_not_serve_is_refused(name: str) -> None:
    assert parse(name) is None


def test_the_round_trip_is_stable() -> None:
    """The name a client sends is the name the hub subscribes to in Redis."""
    for channel in (
        OperatorChannel(OPERATOR, Topic.requests),
        TripChannel(TRIP),
        UserChannel(USER),
    ):
        assert parse(channel.name) == channel


# --- operator channels -------------------------------------------------------------


def test_a_supervisor_reads_their_operators_feeds() -> None:
    for topic in Topic:
        assert decide(OperatorChannel(OPERATOR, topic), supervisor()) is None


def test_another_operators_feed_is_refused() -> None:
    assert (
        decide(OperatorChannel(OTHER_OPERATOR, Topic.vehicles), supervisor())
        is Refusal.wrong_operator
    )


def test_a_subscriber_with_no_operator_scope_is_refused() -> None:
    assert (
        decide(OperatorChannel(OPERATOR, Topic.vehicles), supervisor(operator_id=None))
        is Refusal.wrong_operator
    )


def test_a_client_admin_cannot_read_the_operator_board() -> None:
    """`request_queue_view` scoped to one client is not the operator's whole queue.

    Without this the permission alone would hand a client admin every other client's
    requests - the exact cross-tenant leak the permission matrix exists to prevent.
    """
    client_admin = supervisor(role=str(Role.client_admin), client_id=CLIENT)

    for topic in Topic:
        assert decide(OperatorChannel(OPERATOR, topic), client_admin) is Refusal.client_scoped


def test_a_driver_cannot_read_the_operator_board() -> None:
    driver = supervisor(role=str(Role.driver))
    assert decide(OperatorChannel(OPERATOR, Topic.vehicles), driver) is Refusal.missing_permission


def test_an_employee_cannot_read_the_operator_board() -> None:
    employee = supervisor(role=str(Role.employee))
    assert decide(OperatorChannel(OPERATOR, Topic.requests), employee) is Refusal.missing_permission


def test_an_operator_admin_reads_the_board() -> None:
    admin = supervisor(role=str(Role.operator_admin))
    assert decide(OperatorChannel(OPERATOR, Topic.alerts), admin) is None


def test_the_vehicles_feed_needs_the_map_permission() -> None:
    assert permission_for(OperatorChannel(OPERATOR, Topic.vehicles)) is Permission.live_map_view


def test_the_wrong_operator_beats_a_missing_permission() -> None:
    """Tenancy is checked first, so a stranger learns nothing about their permissions."""
    driver = supervisor(role=str(Role.driver))
    assert decide(OperatorChannel(OTHER_OPERATOR, Topic.vehicles), driver) is Refusal.wrong_operator


# --- trip channels ---------------------------------------------------------------------


def test_the_assigned_driver_reads_the_trip() -> None:
    driver = supervisor(role=str(Role.driver))
    assert decide(TripChannel(TRIP), driver, TripMembership(is_assigned_driver=True)) is None


def test_another_driver_does_not() -> None:
    driver = supervisor(role=str(Role.driver))
    assert (
        decide(TripChannel(TRIP), driver, TripMembership(is_assigned_driver=False))
        is Refusal.not_on_this_trip
    )


def test_a_rider_reads_their_own_trip() -> None:
    employee = supervisor(role=str(Role.employee))
    assert decide(TripChannel(TRIP), employee, TripMembership(is_rider=True)) is None


def test_a_rider_loses_the_trip_once_their_ride_ends() -> None:
    """roles-and-permissions.md: employees see the cab "until pickup/drop", not after."""
    employee = supervisor(role=str(Role.employee))
    finished = TripMembership(is_rider=True, rider_finished=True)

    assert decide(TripChannel(TRIP), employee, finished) is Refusal.ride_finished


def test_an_employee_not_on_the_trip_is_refused() -> None:
    employee = supervisor(role=str(Role.employee))
    assert decide(TripChannel(TRIP), employee, TripMembership()) is Refusal.not_on_this_trip


def test_a_supervisor_reads_any_trip_of_their_operator() -> None:
    assert decide(TripChannel(TRIP), supervisor(), TripMembership(is_operator_staff=True)) is None


def test_an_unknown_trip_is_refused_like_one_you_are_not_on() -> None:
    """A trip of another operator must be indistinguishable from one that does not exist."""
    assert decide(TripChannel(TRIP), supervisor(), None) is Refusal.not_on_this_trip


# --- user channels -----------------------------------------------------------------------


def test_a_user_reads_their_own_channel() -> None:
    assert decide(UserChannel(USER), supervisor()) is None


def test_nobody_reads_another_users_channel() -> None:
    assert decide(UserChannel(uuid.uuid4()), supervisor()) is Refusal.not_your_user_channel


def test_not_even_an_operator_admin_reads_another_users_channel() -> None:
    """Personal notifications are personal; a role is not a reason to read someone's."""
    admin = supervisor(role=str(Role.operator_admin))
    assert decide(UserChannel(uuid.uuid4()), admin) is Refusal.not_your_user_channel


def test_a_user_channel_needs_no_permission() -> None:
    assert permission_for(UserChannel(USER)) is None


def test_a_trip_channel_needs_no_permission() -> None:
    """Trip access is membership, not a role: the rule is who is in the cab."""
    assert permission_for(TripChannel(TRIP)) is None
