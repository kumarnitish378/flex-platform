"""Realtime channel names and who may read them (B13, `websocket-protocol.md` section 3).

Pure: parsing a channel name and deciding a subscription are both decisions about facts
the caller already loaded, so they belong here rather than in the socket handler. That
keeps the interesting half - "may this employee watch this trip" - testable without a
WebSocket, a database or a clock. It lives beside the hub rather than in `app/domain/`
because it reads the permission table, and `app/domain/` imports no module.

The rules are deliberately narrower than the permission matrix alone. `client_admin`
holds `request_queue_view` for their own client, which is not permission to read an
operator-wide feed, so operator channels also require the caller not to be client-scoped.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

from app.modules.auth.permissions import Permission

OPERATOR_PREFIX = "operator."
TRIP_PREFIX = "trip."
USER_PREFIX = "user."


class Topic(StrEnum):
    """The per-operator feeds (`architecture.md` section 4)."""

    vehicles = "vehicles"
    requests = "requests"
    alerts = "alerts"


#: Which permission each operator feed needs. `alerts` has no permission of its own yet
#: (B17 adds the endpoints), so it rides on the board permission - see OQ-25.
TOPIC_PERMISSIONS: dict[Topic, Permission] = {
    Topic.vehicles: Permission.live_map_view,
    Topic.requests: Permission.request_queue_view,
    Topic.alerts: Permission.request_queue_view,
}


class Refusal(StrEnum):
    """Why a subscription was refused. Sent to the client and logged."""

    unknown_channel = "unknown_channel"
    wrong_operator = "wrong_operator"
    client_scoped = "client_scoped"
    missing_permission = "missing_permission"
    not_on_this_trip = "not_on_this_trip"
    ride_finished = "ride_finished"
    not_your_user_channel = "not_your_user_channel"


@dataclass(frozen=True, slots=True)
class OperatorChannel:
    operator_id: uuid.UUID
    topic: Topic

    @property
    def name(self) -> str:
        return f"{OPERATOR_PREFIX}{self.operator_id}.{self.topic}"


@dataclass(frozen=True, slots=True)
class TripChannel:
    trip_id: uuid.UUID

    @property
    def name(self) -> str:
        return f"{TRIP_PREFIX}{self.trip_id}"


@dataclass(frozen=True, slots=True)
class UserChannel:
    user_id: uuid.UUID

    @property
    def name(self) -> str:
        return f"{USER_PREFIX}{self.user_id}"


Channel = OperatorChannel | TripChannel | UserChannel


def parse(name: str) -> Channel | None:
    """A channel name, or `None` if it is not one we serve.

    Unparseable and unauthorised are answered the same way to the client, so a name is
    never a way to learn whether a trip exists.
    """
    if name.startswith(OPERATOR_PREFIX):
        parts = name[len(OPERATOR_PREFIX) :].split(".")
        if len(parts) != 2:
            return None
        operator_id, topic = parts
        if topic not in set(Topic):
            return None
        parsed = _as_uuid(operator_id)
        return None if parsed is None else OperatorChannel(parsed, Topic(topic))

    if name.startswith(TRIP_PREFIX):
        parsed = _as_uuid(name[len(TRIP_PREFIX) :])
        return None if parsed is None else TripChannel(parsed)

    if name.startswith(USER_PREFIX):
        parsed = _as_uuid(name[len(USER_PREFIX) :])
        return None if parsed is None else UserChannel(parsed)

    return None


@dataclass(frozen=True, slots=True)
class Subscriber:
    """Who is asking. Straight off the access token plus the active role."""

    user_id: uuid.UUID
    role: str
    operator_id: uuid.UUID | None
    client_id: uuid.UUID | None


@dataclass(frozen=True, slots=True)
class TripMembership:
    """How this subscriber relates to a trip. Loaded by the caller.

    `rider_finished` carries the time bound from `roles-and-permissions.md`: an employee
    watches the cab from assignment until their own pickup/drop, not for the rest of the
    trip's life.
    """

    is_assigned_driver: bool = False
    is_rider: bool = False
    rider_finished: bool = False
    is_operator_staff: bool = False


def may_subscribe(
    channel: Channel,
    subscriber: Subscriber,
    has_permission: bool,
    membership: TripMembership | None = None,
) -> Refusal | None:
    """`None` means allowed. Anything else is the reason, which the client is told."""
    if isinstance(channel, OperatorChannel):
        return _check_operator(channel, subscriber, has_permission)
    if isinstance(channel, UserChannel):
        return None if channel.user_id == subscriber.user_id else Refusal.not_your_user_channel
    return _check_trip(subscriber, membership)


def _check_operator(
    channel: OperatorChannel, subscriber: Subscriber, has_permission: bool
) -> Refusal | None:
    if subscriber.operator_id is None or channel.operator_id != subscriber.operator_id:
        return Refusal.wrong_operator
    if subscriber.client_id is not None:
        # A client admin sees their own client, never the operator's whole board.
        return Refusal.client_scoped
    return None if has_permission else Refusal.missing_permission


def _check_trip(subscriber: Subscriber, membership: TripMembership | None) -> Refusal | None:
    if membership is None:
        return Refusal.not_on_this_trip
    if membership.is_operator_staff or membership.is_assigned_driver:
        return None
    if not membership.is_rider:
        return Refusal.not_on_this_trip
    return Refusal.ride_finished if membership.rider_finished else None


def permission_for(channel: Channel) -> Permission | None:
    """The permission an operator channel needs; `None` for channels judged by membership."""
    return TOPIC_PERMISSIONS[channel.topic] if isinstance(channel, OperatorChannel) else None


def _as_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None
