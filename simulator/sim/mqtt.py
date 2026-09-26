"""Publishing simulated GPS to the real broker (M04, `mqtt-topics.md`).

The `PingSink` seam M02 left: vehicle agents do not change at all, the sink underneath
them does. A simulated cab now looks to the backend exactly like a driver's phone -
same topic, same payload, same credentials, same QoS.

One connection per vehicle, because that is what the real fleet does: Mosquitto's ACL
authorises a *client* to publish to its own vehicle's topic, so a single shared
connection publishing for forty cabs would be a shape the production broker rejects.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sim.pings import Ping
from sim.platform import DutyCredentials

#: mqtt-topics.md: GPS is QoS 0 and not retained. Losing one ping of forty a minute does
#: not matter; a queue of stale positions delivered on reconnect does.
GPS_QOS = 0
CONNECT_TIMEOUT_SECONDS = 5.0


class MqttUnavailableError(RuntimeError):
    """The broker could not be reached. A run that wanted MQTT cannot continue."""


@dataclass(frozen=True, slots=True)
class Publication:
    """One published message, kept for assertions and the run log."""

    topic: str
    payload: dict[str, Any]


class MqttPingSink:
    """Publishes each vehicle's pings as that vehicle, over its own connection."""

    def __init__(self, keepalive_seconds: int = 120, paced: bool = False) -> None:
        self._keepalive = keepalive_seconds
        self._clients: dict[str, Any] = {}
        self._topics: dict[str, str] = {}
        self.published: list[Publication] = []
        self.failed = 0
        #: How often a cab had to re-establish its connection. Worth seeing in a run.
        self.reconnects = 0
        #: Pacing holds each ping until the shared clock has reached its timestamp.
        #: Without it a compressed run loses almost everything: paho drains 420 pings in
        #: under a second while the clock walks the same hour through 60 HTTP calls, so
        #: the pings arrive minutes ahead of the backend's "now" and the ingestor
        #: correctly rejects them as `too_far_future`. Real cabs cannot outrun the clock;
        #: a simulator can, and this is what stops it.
        self._paced = paced
        self._pending: list[tuple[datetime, Ping]] = []

    def register(self, vehicle_id: uuid.UUID | str, credentials: DutyCredentials) -> None:
        """Connect as one vehicle. Call once per cab, after it goes on duty."""
        try:
            import paho.mqtt.client as paho
        except ImportError as exc:  # pragma: no cover - dev dependency
            raise MqttUnavailableError(
                "paho-mqtt is not installed; install the simulator's dev extras"
            ) from exc

        key = str(vehicle_id)
        client = paho.Client(
            paho.CallbackAPIVersion.VERSION2, client_id=f"sim-{key[:8]}", clean_session=True
        )
        client.username_pw_set(credentials.username, credentials.password)
        # A cab that loses power stops reporting; the Last Will tells the backend so,
        # rather than leaving a stale marker on the map (mqtt-topics.md).
        client.will_set(
            f"{credentials.topic_prefix}/status",
            json.dumps({"v": 1, "status": "offline", "reason": "will"}),
            qos=1,
            retain=True,
        )
        try:
            client.connect(credentials.host, credentials.port, keepalive=self._keepalive)
        except OSError as exc:
            raise MqttUnavailableError(
                f"Could not reach the broker at {credentials.host}:{credentials.port}: {exc}"
            ) from exc
        client.loop_start()

        self._clients[key] = client
        self._topics[key] = credentials.gps_topic

    def emit(self, ping: Ping) -> None:
        """`PingSink`. Never raises: one cab's broker trouble is not the run's problem."""
        if self._paced:
            self._pending.append((ping.ts, ping))
            return
        self._publish(ping)

    def release_up_to(self, moment: datetime) -> int:
        """Publish everything the shared clock has caught up with."""
        ready = [(ts, ping) for ts, ping in self._pending if ts <= moment]
        self._pending = [(ts, ping) for ts, ping in self._pending if ts > moment]
        for _ts, ping in ready:
            self._publish(ping)
        return len(ready)

    def release_all(self) -> int:
        """Publish whatever is left, at the end of a run."""
        remaining = self._pending
        self._pending = []
        for _ts, ping in remaining:
            self._publish(ping)
        return len(remaining)

    @property
    def pending(self) -> int:
        return len(self._pending)

    def _publish(self, ping: Ping) -> None:
        topic = self._topics.get(ping.vehicle_id)
        client = self._clients.get(ping.vehicle_id)
        if topic is None or client is None:
            # A vehicle that never went on duty has no credentials and no business
            # publishing. Counted rather than raised, so the count can be asserted.
            self.failed += 1
            return

        payload = ping.to_payload()
        body = json.dumps(payload)
        result = client.publish(topic, body, qos=GPS_QOS)

        if result.rc != 0 and not client.is_connected():
            # A paced run leaves long real-time gaps between bursts, and a cab whose
            # connection lapsed must come back rather than drop the rest of its shift -
            # which is exactly what the driver app does on a flaky mobile network.
            self.reconnects += 1
            try:
                client.reconnect()
                result = client.publish(topic, body, qos=GPS_QOS)
            except OSError:
                pass

        if result.rc != 0:
            self.failed += 1
            return
        self.published.append(Publication(topic=topic, payload=payload))

    def flush(self, timeout_seconds: float = 30.0) -> None:
        """Wait until every queued message has actually gone out on the wire.

        This matters far more in a simulator than on a phone. A cab emits one ping every
        five seconds; a simulated hour compresses to milliseconds, so a run hands paho
        hundreds of messages at once and then exits. `publish()` returning 0 only means
        "queued", so without waiting here the disconnect throws the queue away and the
        run reports pings that the broker never saw - which is exactly the bug this
        method was written to fix.

        QoS 0 offers no acknowledgement (`mqtt-topics.md`), so "written to the socket" is
        the strongest guarantee available, and it is the same one a real phone gets.
        """
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            pending = [client for client in self._clients.values() if client.want_write()]
            if not pending:
                break
            for client in pending:
                client.loop_write()
            time.sleep(0.01)
        # The network thread may still be mid-write; give it a moment to finish.
        time.sleep(0.2)

    def close(self) -> None:
        for client in self._clients.values():
            client.loop_stop()
            client.disconnect()
        self._clients.clear()
        self._topics.clear()

    def __enter__(self) -> MqttPingSink:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # --- for tests and the run log ------------------------------------------------

    def count_for(self, vehicle_id: uuid.UUID | str) -> int:
        topic = self._topics.get(str(vehicle_id))
        return sum(1 for item in self.published if item.topic == topic)


class TeeingPingSink:
    """Sends every ping to several sinks.

    A platform run still wants its `pings.csv`: the recorder's metrics and the broker are
    not alternatives, and a run whose output depends on which sink was chosen would make
    two runs incomparable.
    """

    def __init__(self, *sinks: Any) -> None:
        self._sinks = sinks

    def emit(self, ping: Ping) -> None:
        for sink in self._sinks:
            sink.emit(ping)
