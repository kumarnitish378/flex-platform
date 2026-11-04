"""Connection registry and Redis fan-out (B13).

The hub is where a slow phone on a train can hurt everyone else, so the interesting
cases here are the unhappy ones: a socket that never accepts, a socket that raises, and
a Redis that hiccups.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from app.modules.realtime.hub import Connection, Hub


def recorder() -> tuple[Connection, list[dict[str, Any]]]:
    received: list[dict[str, Any]] = []

    async def send(message: dict[str, Any]) -> None:
        received.append(message)

    return Connection(send), received


class FakePubSub:
    """Enough of redis-py's pubsub to drive the pump."""

    def __init__(self) -> None:
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []
        self.queue: asyncio.Queue[dict[str, Any] | Exception] = asyncio.Queue()
        self.closed = False

    async def subscribe(self, channel: str) -> None:
        self.subscribed.append(channel)

    async def unsubscribe(self, channel: str) -> None:
        self.unsubscribed.append(channel)

    async def get_message(self, **_: Any) -> dict[str, Any] | None:
        try:
            item = await asyncio.wait_for(self.queue.get(), timeout=0.05)
        except TimeoutError:
            return None
        if isinstance(item, Exception):
            raise item
        return item

    async def close(self) -> None:
        self.closed = True


class FakeRedisForHub:
    def __init__(self, pubsub: FakePubSub) -> None:
        self._pubsub = pubsub

    def pubsub(self) -> FakePubSub:
        return self._pubsub


# --- membership ---------------------------------------------------------------------


async def test_a_message_reaches_a_subscriber() -> None:
    hub = Hub()
    connection, received = recorder()
    await hub.subscribe(connection, "operator.x.vehicles")

    delivered = await hub.deliver("operator.x.vehicles", {"type": "event"})

    assert delivered == 1
    assert received == [{"type": "event"}]


async def test_a_message_on_another_channel_does_not() -> None:
    hub = Hub()
    connection, received = recorder()
    await hub.subscribe(connection, "trip.a")

    await hub.deliver("trip.b", {"type": "event"})
    assert received == []


async def test_every_subscriber_gets_it() -> None:
    hub = Hub()
    first, seen_by_first = recorder()
    second, seen_by_second = recorder()
    await hub.subscribe(first, "operator.x.vehicles")
    await hub.subscribe(second, "operator.x.vehicles")

    assert await hub.deliver("operator.x.vehicles", {"n": 1}) == 2
    assert seen_by_first == seen_by_second == [{"n": 1}]


async def test_unsubscribing_stops_delivery() -> None:
    hub = Hub()
    connection, received = recorder()
    await hub.subscribe(connection, "trip.a")
    await hub.unsubscribe(connection, "trip.a")

    await hub.deliver("trip.a", {"n": 1})
    assert received == []


async def test_disconnecting_drops_every_channel() -> None:
    hub = Hub()
    connection, _ = recorder()
    await hub.subscribe(connection, "trip.a")
    await hub.subscribe(connection, "user.b")

    await hub.disconnect(connection)
    assert hub.channels == set()


async def test_unsubscribing_from_an_unknown_channel_is_harmless() -> None:
    hub = Hub()
    connection, _ = recorder()
    await hub.unsubscribe(connection, "trip.never-subscribed")


async def test_delivering_to_nobody_is_not_an_error() -> None:
    assert await Hub().deliver("trip.a", {"n": 1}) == 0


# --- one bad socket ----------------------------------------------------------------------


async def test_a_socket_that_raises_does_not_stop_the_others() -> None:
    hub = Hub()

    async def explode(_: dict[str, Any]) -> None:
        raise RuntimeError("client went away")

    healthy, received = recorder()
    await hub.subscribe(Connection(explode), "operator.x.vehicles")
    await hub.subscribe(healthy, "operator.x.vehicles")

    delivered = await hub.deliver("operator.x.vehicles", {"n": 1})

    assert delivered == 1
    assert received == [{"n": 1}]


async def test_a_socket_that_never_accepts_is_given_up_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """A phone in a tunnel must not hold the supervisor's map hostage."""
    monkeypatch.setattr("app.modules.realtime.hub.SEND_TIMEOUT_SECONDS", 0.05)
    hub = Hub()

    async def never(_: dict[str, Any]) -> None:
        await asyncio.sleep(10)

    healthy, received = recorder()
    await hub.subscribe(Connection(never), "trip.a")
    await hub.subscribe(healthy, "trip.a")

    delivered = await asyncio.wait_for(hub.deliver("trip.a", {"n": 1}), timeout=2)

    assert delivered == 1
    assert received == [{"n": 1}]


# --- Redis ----------------------------------------------------------------------------------


async def test_the_first_subscriber_opens_the_redis_subscription() -> None:
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    first, _ = recorder()
    second, _ = recorder()

    await hub.subscribe(first, "operator.x.vehicles")
    await hub.subscribe(second, "operator.x.vehicles")

    # Forty supervisors watching one map is still one Redis subscription.
    assert pubsub.subscribed == ["operator.x.vehicles"]
    await hub.close()


async def test_the_last_leaver_closes_it() -> None:
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    first, _ = recorder()
    second, _ = recorder()
    await hub.subscribe(first, "trip.a")
    await hub.subscribe(second, "trip.a")

    await hub.unsubscribe(first, "trip.a")
    assert pubsub.unsubscribed == []

    await hub.unsubscribe(second, "trip.a")
    assert pubsub.unsubscribed == ["trip.a"]
    await hub.close()


async def test_an_event_published_on_redis_reaches_the_socket() -> None:
    """The whole point: the worker that published is not this process."""
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    connection, received = recorder()
    await hub.subscribe(connection, "operator.x.vehicles")

    frame = {"type": "event", "event": "vehicle.location", "data": {"lat": 28.5}}
    await pubsub.queue.put({"channel": "operator.x.vehicles", "data": json.dumps(frame)})

    await _until(lambda: received != [])
    assert received == [frame]
    await hub.close()


async def test_bytes_from_redis_are_decoded() -> None:
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    connection, received = recorder()
    await hub.subscribe(connection, "trip.a")

    await pubsub.queue.put({"channel": b"trip.a", "data": b'{"type":"event"}'})

    await _until(lambda: received != [])
    assert received == [{"type": "event"}]
    await hub.close()


async def test_an_unparseable_payload_is_dropped_not_fatal() -> None:
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    connection, received = recorder()
    await hub.subscribe(connection, "trip.a")

    await pubsub.queue.put({"channel": "trip.a", "data": "not json"})
    await pubsub.queue.put({"channel": "trip.a", "data": '["not an object"]'})
    await pubsub.queue.put({"channel": "trip.a", "data": '{"type":"event"}'})

    await _until(lambda: received != [])
    assert received == [{"type": "event"}]
    await hub.close()


async def test_the_pump_survives_a_redis_error() -> None:
    """A broker hiccup must not silently end realtime for this whole process."""
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    connection, received = recorder()
    await hub.subscribe(connection, "trip.a")

    await pubsub.queue.put(ConnectionError("broker went away"))
    await asyncio.sleep(0.05)
    await pubsub.queue.put({"channel": "trip.a", "data": '{"type":"event"}'})

    await _until(lambda: received != [], wait_seconds=5.0)
    assert received == [{"type": "event"}]
    await hub.close()


async def test_closing_stops_the_pump() -> None:
    pubsub = FakePubSub()
    hub = Hub(FakeRedisForHub(pubsub))
    connection, _ = recorder()
    await hub.subscribe(connection, "trip.a")

    await hub.close()

    assert pubsub.closed is True
    assert hub.channels == set()


async def test_a_hub_without_redis_still_delivers_locally() -> None:
    """Unit tests and a single-process dev run must not need a broker."""
    hub = Hub(redis=None)
    connection, received = recorder()
    await hub.subscribe(connection, "trip.a")

    await hub.deliver("trip.a", {"n": 1})
    assert received == [{"n": 1}]


async def _until(condition: Any, wait_seconds: float = 2.0) -> None:
    deadline = asyncio.get_running_loop().time() + wait_seconds
    while asyncio.get_running_loop().time() < deadline:
        if condition():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition never became true")
