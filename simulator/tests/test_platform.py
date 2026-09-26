"""The platform client and the MQTT sink (M04).

No backend and no broker here: the client is exercised against a mock transport and the
sink against a fake paho client, so these run in CI. The real thing is
`tests/test_closed_loop_live.py`, which is opt-in.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from sim.mqtt import MqttPingSink, MqttUnavailableError, TeeingPingSink
from sim.pings import MemoryPingSink, Ping
from sim.platform import DutyCredentials, PlatformClient, PlatformError

NOW = datetime(2026, 9, 25, 7, 30, tzinfo=UTC)
OPERATOR = "11111111-1111-4111-8111-111111111111"
VEHICLE = "22222222-2222-4222-8222-222222222222"


def client_with(handler: Any) -> PlatformClient:
    return PlatformClient(
        "http://backend:8000/api/v1", client=httpx.Client(transport=httpx.MockTransport(handler))
    )


def reset_body(**extra: Any) -> dict[str, Any]:
    body = {
        "operator_id": OPERATOR,
        "client_id": "33333333-3333-4333-8333-333333333333",
        "office_ids": [],
        "zone_ids": [],
        "employee_ids": [],
        "vehicle_ids": [VEHICLE],
        "driver_ids": [],
        "users": [
            {
                "role": "driver",
                "phone": "+919000000001",
                "user_id": "44444444-4444-4444-8444-444444444444",
                "access_token": "driver-token",
            },
            {
                "role": "supervisor",
                "phone": "+919000000002",
                "user_id": "55555555-5555-4555-8555-555555555555",
                "access_token": "supervisor-token",
            },
        ],
        "now": NOW.isoformat(),
    }
    body.update(extra)
    return body


def duty_body() -> dict[str, Any]:
    return {
        "on_duty": True,
        "vehicle_id": VEHICLE,
        "mqtt": {
            "host": "localhost",
            "port": 1883,
            "username": f"veh-{VEHICLE[:8]}",
            "password": "secret",
            "topic_prefix": f"sc/v1/op/{OPERATOR}/veh/{VEHICLE}",
        },
    }


# --- seeding a world ------------------------------------------------------------------


def test_reset_returns_the_seeded_world() -> None:
    platform = client_with(lambda request: httpx.Response(200, json=reset_body()))

    world = platform.reset()

    assert str(world.operator_id) == OPERATOR
    assert [str(v) for v in world.vehicle_ids] == [VEHICLE]
    assert world.now == NOW


def test_a_token_can_be_found_by_role() -> None:
    platform = client_with(lambda request: httpx.Response(200, json=reset_body()))
    world = platform.reset()

    assert world.token_for("driver") == "driver-token"
    assert world.token_for("supervisor") == "supervisor-token"


def test_a_missing_role_says_so_rather_than_returning_nothing() -> None:
    """A run that silently published as nobody would be very hard to debug."""
    platform = client_with(lambda request: httpx.Response(200, json=reset_body(users=[])))
    world = platform.reset()

    with pytest.raises(PlatformError, match="seeded no driver"):
        world.token_for("driver")


def test_a_refusal_is_reported_with_its_status() -> None:
    platform = client_with(lambda request: httpx.Response(404, text="Not Found"))

    with pytest.raises(PlatformError, match="404"):
        platform.reset()


def test_an_unreachable_backend_is_reported() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(PlatformError, match="failed"):
        client_with(refuse).reset()


def test_health_says_no_rather_than_raising() -> None:
    """The CLI checks this before doing anything destructive."""

    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    assert client_with(refuse).health() is False


# --- sharing the clock -----------------------------------------------------------------


def test_setting_the_clock_sends_the_simulated_time() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["method"] = request.method
        return httpx.Response(200, json={"now": NOW.isoformat()})

    assert client_with(handler).set_clock(NOW) == NOW
    assert seen["method"] == "PUT"
    assert seen["body"] == {"now": NOW.isoformat()}


def test_advancing_reports_what_the_jump_triggered() -> None:
    """A scenario asserts on these rather than sleeping and hoping."""
    body = {
        "now": NOW.isoformat(),
        "expired": 2,
        "near_expiry_alerts": 1,
        "stop_etas_refreshed": 4,
    }
    result = client_with(lambda request: httpx.Response(200, json=body)).advance_clock(600)

    assert result["expired"] == 2
    assert result["stop_etas_refreshed"] == 4


# --- going on duty -----------------------------------------------------------------------


def test_going_on_duty_returns_the_brokers_address_and_topic() -> None:
    platform = client_with(lambda request: httpx.Response(200, json=duty_body()))

    credentials = platform.go_on_duty("driver-token", uuid.UUID(VEHICLE))

    assert credentials.host == "localhost"
    assert credentials.port == 1883
    assert credentials.gps_topic.endswith("/gps")
    assert str(credentials.vehicle_id) == VEHICLE


def test_the_topic_comes_from_the_backend_not_from_a_format_string() -> None:
    """Rebuilding it here would drift the day `mqtt-topics.md` changes."""
    platform = client_with(lambda request: httpx.Response(200, json=duty_body()))

    credentials = platform.go_on_duty("driver-token", uuid.UUID(VEHICLE))
    assert credentials.gps_topic == f"sc/v1/op/{OPERATOR}/veh/{VEHICLE}/gps"


def test_the_driver_token_is_sent() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=duty_body())

    client_with(handler).go_on_duty("driver-token", uuid.UUID(VEHICLE))
    assert seen["auth"] == "Bearer driver-token"


def test_duty_without_credentials_is_fatal() -> None:
    """Publishing GPS is the whole point of going on duty here."""
    platform = client_with(
        lambda request: httpx.Response(200, json={"on_duty": True, "vehicle_id": VEHICLE})
    )

    with pytest.raises(PlatformError, match="MQTT credentials"):
        platform.go_on_duty("driver-token", uuid.UUID(VEHICLE))


def test_the_live_map_is_read_through_the_same_endpoint_the_app_uses() -> None:
    items = [{"id": VEHICLE, "position": {"lat": 28.5, "lng": 77.4}, "stale": False}]
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"items": items})

    result = client_with(handler).live_vehicles("supervisor-token")

    assert seen["path"].endswith("/dispatch/vehicles")
    assert result == items


# --- the MQTT sink -----------------------------------------------------------------------------


class FakePublishResult:
    def __init__(self, rc: int = 0) -> None:
        self.rc = rc


class FakeMqttClient:
    """Enough of paho to record what a vehicle would have published."""

    instances: list[FakeMqttClient] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.client_id = kwargs.get("client_id")
        self.credentials: tuple[str, str] | None = None
        self.will: tuple[str, str] | None = None
        self.connected_to: tuple[str, int] | None = None
        self.messages: list[tuple[str, str, int]] = []
        self.looping = False
        self.disconnected = False
        self.publish_rc = 0
        self.connect_error: OSError | None = None
        self.reconnected = False
        FakeMqttClient.instances.append(self)

    def username_pw_set(self, username: str, password: str) -> None:
        self.credentials = (username, password)

    def will_set(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> None:
        self.will = (topic, payload)

    def connect(self, host: str, port: int, keepalive: int = 60) -> None:
        if self.connect_error is not None:
            raise self.connect_error
        self.connected_to = (host, port)

    def loop_start(self) -> None:
        self.looping = True

    def loop_write(self) -> None:
        self.wants_write = False

    def want_write(self) -> bool:
        return getattr(self, "wants_write", False)

    def loop_stop(self) -> None:
        self.looping = False

    def disconnect(self) -> None:
        self.disconnected = True

    def is_connected(self) -> bool:
        return not self.disconnected

    def reconnect(self) -> None:
        self.reconnected = True
        self.disconnected = False

    def publish(self, topic: str, payload: str, qos: int = 0) -> FakePublishResult:
        if self.disconnected:
            # paho returns MQTT_ERR_NO_CONN (4) rather than queueing while offline.
            return FakePublishResult(4)
        self.messages.append((topic, payload, qos))
        return FakePublishResult(self.publish_rc)


class FakeCallbackApiVersion:
    VERSION2 = 2


@pytest.fixture
def fake_paho(monkeypatch: pytest.MonkeyPatch) -> type[FakeMqttClient]:
    import sys
    import types

    FakeMqttClient.instances = []
    client_module = types.ModuleType("paho.mqtt.client")
    client_module.Client = FakeMqttClient  # type: ignore[attr-defined]
    client_module.CallbackAPIVersion = FakeCallbackApiVersion  # type: ignore[attr-defined]

    # The whole chain, because `import paho.mqtt.client as paho` resolves the name by
    # attribute off the parent package, not only through sys.modules.
    mqtt_module = types.ModuleType("paho.mqtt")
    mqtt_module.client = client_module  # type: ignore[attr-defined]
    root = types.ModuleType("paho")
    root.mqtt = mqtt_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "paho", root)
    monkeypatch.setitem(sys.modules, "paho.mqtt", mqtt_module)
    monkeypatch.setitem(sys.modules, "paho.mqtt.client", client_module)
    return FakeMqttClient


def credentials(vehicle_id: str = VEHICLE) -> DutyCredentials:
    return DutyCredentials(
        vehicle_id=uuid.UUID(vehicle_id),
        host="localhost",
        port=1883,
        username=f"veh-{vehicle_id[:8]}",
        password="secret",
        topic_prefix=f"sc/v1/op/{OPERATOR}/veh/{vehicle_id}",
    )


def a_ping(vehicle_id: str = VEHICLE) -> Ping:
    return Ping(vehicle_id=vehicle_id, ts=NOW, lat=28.5, lng=77.4, spd=8.0)


def test_a_ping_is_published_on_the_vehicles_own_topic(fake_paho: Any) -> None:
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())

    sink.emit(a_ping())

    topic, payload, qos = FakeMqttClient.instances[0].messages[0]
    assert topic == f"sc/v1/op/{OPERATOR}/veh/{VEHICLE}/gps"
    assert json.loads(payload)["lat"] == 28.5
    assert qos == 0


def test_each_vehicle_gets_its_own_connection(fake_paho: Any) -> None:
    """The production ACL authorises a client to publish as one cab, not as the fleet."""
    other = "66666666-6666-4666-8666-666666666666"
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())
    sink.register(other, credentials(other))

    assert len(FakeMqttClient.instances) == 2
    assert FakeMqttClient.instances[0].credentials != FakeMqttClient.instances[1].credentials


def test_a_vehicle_publishes_as_itself(fake_paho: Any) -> None:
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())

    assert FakeMqttClient.instances[0].credentials == (f"veh-{VEHICLE[:8]}", "secret")


def test_a_last_will_is_registered(fake_paho: Any) -> None:
    """A cab that loses power must not leave a live-looking marker on the map."""
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())

    will = FakeMqttClient.instances[0].will
    assert will is not None
    assert will[0].endswith("/status")
    assert json.loads(will[1])["status"] == "offline"


def test_a_ping_from_a_vehicle_that_never_went_on_duty_is_counted_not_raised(
    fake_paho: Any,
) -> None:
    """It has no credentials and no business publishing, but must not kill the run."""
    sink = MqttPingSink()

    sink.emit(a_ping())

    assert sink.published == []
    assert sink.failed == 1


def test_a_rejected_publish_is_counted(fake_paho: Any) -> None:
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())
    FakeMqttClient.instances[0].publish_rc = 1

    sink.emit(a_ping())

    assert sink.failed == 1
    assert sink.published == []


def test_an_unreachable_broker_is_reported_at_registration(fake_paho: Any) -> None:
    """Fail when the cab signs in, not silently on every ping for the next hour."""
    sink = MqttPingSink()
    original = FakeMqttClient.connect

    def explode(self: Any, host: str, port: int, keepalive: int = 60) -> None:
        raise OSError("connection refused")

    FakeMqttClient.connect = explode  # type: ignore[method-assign]
    try:
        with pytest.raises(MqttUnavailableError, match="Could not reach the broker"):
            sink.register(VEHICLE, credentials())
    finally:
        FakeMqttClient.connect = original  # type: ignore[method-assign]


def test_closing_disconnects_every_vehicle(fake_paho: Any) -> None:
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())

    sink.close()

    assert FakeMqttClient.instances[0].disconnected is True
    assert sink.count_for(VEHICLE) == 0


def test_counting_is_per_vehicle(fake_paho: Any) -> None:
    other = "66666666-6666-4666-8666-666666666666"
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())
    sink.register(other, credentials(other))

    sink.emit(a_ping())
    sink.emit(a_ping())
    sink.emit(a_ping(other))

    assert sink.count_for(VEHICLE) == 2
    assert sink.count_for(other) == 1


# --- teeing ---------------------------------------------------------------------------------------


def test_a_platform_run_still_records_its_own_pings(fake_paho: Any) -> None:
    """Metrics must not depend on which sink was chosen, or two runs are incomparable."""
    memory = MemoryPingSink()
    mqtt = MqttPingSink()
    mqtt.register(VEHICLE, credentials())

    TeeingPingSink(memory, mqtt).emit(a_ping())

    assert len(memory.pings) == 1
    assert len(mqtt.published) == 1


# --- pacing (the fix that made the closed loop work) -----------------------------------


def paced_sink(fake_paho: Any) -> MqttPingSink:
    sink = MqttPingSink(paced=True)
    sink.register(VEHICLE, credentials())
    return sink


def test_a_paced_sink_holds_pings_until_the_clock_reaches_them(fake_paho: Any) -> None:
    """Without this a compressed run loses almost every ping.

    paho drains hundreds of messages in under a second while the backend's clock walks
    the same simulated hour through 60 HTTP calls, so the pings arrive minutes ahead of
    the backend's "now" and the ingestor rejects them as `too_far_future`.
    """
    sink = paced_sink(fake_paho)

    sink.emit(a_ping())

    assert sink.pending == 1
    assert sink.published == []


def test_releasing_publishes_only_what_the_clock_has_passed(fake_paho: Any) -> None:
    sink = paced_sink(fake_paho)
    early = Ping(vehicle_id=VEHICLE, ts=NOW, lat=28.5, lng=77.4)
    late = Ping(vehicle_id=VEHICLE, ts=NOW + timedelta(minutes=5), lat=28.6, lng=77.4)
    sink.emit(early)
    sink.emit(late)

    released = sink.release_up_to(NOW + timedelta(minutes=1))

    assert released == 1
    assert sink.pending == 1
    assert len(sink.published) == 1


def test_a_ping_exactly_at_the_clock_is_released(fake_paho: Any) -> None:
    sink = paced_sink(fake_paho)
    sink.emit(a_ping())

    assert sink.release_up_to(NOW) == 1


def test_releasing_everything_empties_the_queue(fake_paho: Any) -> None:
    """Whatever the last sync did not cover still belongs on the broker."""
    sink = paced_sink(fake_paho)
    sink.emit(a_ping())
    sink.emit(Ping(vehicle_id=VEHICLE, ts=NOW + timedelta(hours=2), lat=28.7, lng=77.4))

    assert sink.release_all() == 2
    assert sink.pending == 0
    assert len(sink.published) == 2


def test_an_unpaced_sink_publishes_straight_away(fake_paho: Any) -> None:
    """Pacing is for compressed runs; anything real-time keeps the direct path."""
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())

    sink.emit(a_ping())

    assert sink.pending == 0
    assert len(sink.published) == 1


def test_pacing_preserves_order(fake_paho: Any) -> None:
    """A cab's positions must reach the map in the order it drove them."""
    sink = paced_sink(fake_paho)
    for minute in range(5):
        sink.emit(Ping(vehicle_id=VEHICLE, ts=NOW + timedelta(minutes=minute), lat=28.5, lng=77.4))

    sink.release_all()

    sent = [
        json.loads(payload)["ts"] for _topic, payload, _qos in FakeMqttClient.instances[0].messages
    ]
    assert sent == sorted(sent)


def test_a_lapsed_connection_is_re_established(fake_paho: Any) -> None:
    """A paced run leaves long gaps; a cab must come back, not lose the rest of its shift."""
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())
    client = FakeMqttClient.instances[0]
    client.disconnected = True

    sink.emit(a_ping())

    assert client.reconnected is True
    assert len(sink.published) == 1
    assert sink.reconnects == 1


def test_a_publish_that_fails_while_connected_is_not_retried(fake_paho: Any) -> None:
    """Reconnecting would not help, and hiding a real rejection helps even less."""
    sink = MqttPingSink()
    sink.register(VEHICLE, credentials())
    FakeMqttClient.instances[0].publish_rc = 1

    sink.emit(a_ping())

    assert FakeMqttClient.instances[0].reconnected is False
    assert sink.failed == 1
