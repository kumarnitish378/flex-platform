"""GPS ping generation and sinks.

Payload and interval rules come from `mqtt-topics.md`. M02 writes pings to a local log;
M04 swaps the sink for a real MQTT publisher without touching the vehicle agent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# mqtt-topics.md, "Ping intervals".
MOVING_INTERVAL_SECONDS = 5
STATIONARY_INTERVAL_SECONDS = 30
# A vehicle counts as stationary below this speed, after STATIONARY_AFTER_SECONDS.
STATIONARY_SPEED_MS = 1.0
STATIONARY_AFTER_SECONDS = 120

PAYLOAD_VERSION = 1


@dataclass(frozen=True, slots=True)
class Ping:
    """One GPS ping, exactly the payload in `mqtt-topics.md`."""

    vehicle_id: str
    ts: datetime
    lat: float
    lng: float
    spd: float | None = None
    hdg: float | None = None
    acc: float | None = None
    bat: int | None = None
    src: str = "sim"

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "v": PAYLOAD_VERSION,
            "ts": self.ts.isoformat().replace("+00:00", "Z"),
            "lat": round(self.lat, 6),
            "lng": round(self.lng, 6),
            "src": self.src,
        }
        for key, value in (
            ("spd", self.spd),
            ("hdg", self.hdg),
            ("acc", self.acc),
            ("bat", self.bat),
        ):
            if value is not None:
                payload[key] = round(value, 2) if isinstance(value, float) else value
        return payload


@runtime_checkable
class PingSink(Protocol):
    """Where pings go. M02 logs them; M04 publishes to MQTT."""

    def emit(self, ping: Ping) -> None: ...


class MemoryPingSink:
    """Collects pings in memory. Used by tests and by the recorder (M03)."""

    def __init__(self) -> None:
        self.pings: list[Ping] = []

    def emit(self, ping: Ping) -> None:
        self.pings.append(ping)

    def for_vehicle(self, vehicle_id: str) -> list[Ping]:
        return [ping for ping in self.pings if ping.vehicle_id == vehicle_id]


class JsonlPingSink:
    """Appends one JSON object per line, ready for `pings.csv` conversion in M03."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self._path.open("w", encoding="utf-8")

    def emit(self, ping: Ping) -> None:
        record = {"vehicle_id": ping.vehicle_id, **ping.to_payload()}
        self._handle.write(json.dumps(record) + "\n")

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> JsonlPingSink:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def ping_interval_seconds(speed_ms: float, stationary_for_seconds: float) -> int:
    """The interval the driver app would use right now (`mqtt-topics.md`).

    Stationary only counts after two minutes below 1 m/s: a cab waiting at a light must
    not drop to 30-second pings and make the map look frozen.
    """
    if speed_ms > STATIONARY_SPEED_MS:
        return MOVING_INTERVAL_SECONDS
    if stationary_for_seconds >= STATIONARY_AFTER_SECONDS:
        return STATIONARY_INTERVAL_SECONDS
    return MOVING_INTERVAL_SECONDS
