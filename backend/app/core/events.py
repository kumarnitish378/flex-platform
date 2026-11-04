"""Realtime events (`architecture.md` section 4).

An API worker that assigns a trip is almost never the process holding the supervisor's
WebSocket, so notification is a publish, not a direct send: the worker publishes to Redis
and the hub (B13) fans out to whoever is connected. This module is only the publishing
half, so B14 can emit `request.assigned` and `trip.assigned` before the hub exists.

Publishing is **best-effort**. A Redis outage must not fail an assignment that is already
written to the database: the supervisor's screen goes stale and recovers on the next poll,
which is a far smaller problem than a trip that could not be created.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.core.logging import get_logger
from app.core.redis import RedisLike

logger = get_logger(__name__)


def operator_channel(operator_id: uuid.UUID, topic: str) -> str:
    """`operator.{id}.vehicles` / `.requests` / `.alerts` (supervisor and admin)."""
    return f"operator.{operator_id}.{topic}"


def trip_channel(trip_id: uuid.UUID) -> str:
    """`trip.{id}` - the riders on it and the assigned driver."""
    return f"trip.{trip_id}"


def user_channel(user_id: uuid.UUID) -> str:
    """`user.{id}` - personal notifications."""
    return f"user.{user_id}"


@dataclass(frozen=True, slots=True)
class Event:
    """One realtime message. `name` is the event type clients switch on."""

    name: str
    channel: str
    payload: dict[str, Any] = field(default_factory=dict)

    def encode(self) -> str:
        """The exact frame a client receives.

        The hub relays what it reads from Redis straight to the socket, so what is
        published here must already be a valid server frame (`websocket-protocol.md`
        section 2) rather than something the hub has to reshape.
        """
        return json.dumps(
            {"type": "event", "event": self.name, "channel": self.channel, "data": self.payload}
        )


@runtime_checkable
class EventPublisher(Protocol):
    """Where realtime events go. Swapped for a recorder in tests."""

    async def publish(self, event: Event) -> None: ...


class RedisEventPublisher:
    """Publishes onto Redis pub/sub for the WebSocket hub to pick up."""

    def __init__(self, redis: RedisLike) -> None:
        self._redis = redis

    async def publish(self, event: Event) -> None:
        publish = getattr(self._redis, "publish", None)
        if publish is None:
            return
        try:
            await publish(event.channel, event.encode())
        except Exception as exc:  # noqa: BLE001 - a stale screen beats a failed assignment
            logger.warning("event_publish_failed", event=event.name, error=type(exc).__name__)


class NullEventPublisher:
    """Drops everything. The default, so a module without Redis still runs."""

    async def publish(self, event: Event) -> None:
        return None


class DeferredEvents:
    """One request's events, held until the data they announce is committed.

    A client that receives `request.assigned` fetches the request at once; if the event left before
    the commit it reads the old state (found by the load test, 2026-11-03). Handlers publish into
    this; the session dependency flushes it after `commit()` and discards it on a rollback.
    `has_session` tells the events dependency whether a commit is coming (so it need not flush).
    """

    def __init__(self, target: EventPublisher) -> None:
        self._target = target
        self._pending: list[Event] = []
        self.has_session = False

    async def publish(self, event: Event) -> None:
        self._pending.append(event)

    async def flush(self) -> None:
        """Send what is held, in order. Safe to call again: it only ever sends each event once."""
        pending, self._pending = self._pending, []
        for event in pending:
            await self._target.publish(event)

    def discard(self) -> None:
        self._pending.clear()


class RecordingEventPublisher:
    """Keeps events in a list. For tests that assert who was notified."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)

    def names(self) -> list[str]:
        return [event.name for event in self.events]

    def channels_for(self, name: str) -> list[str]:
        return [event.channel for event in self.events if event.name == name]
