"""GPS ping parsing and validation (`mqtt-topics.md`, Ingestor validation).

Pure: takes a payload dict and the facts needed to judge it, returns either a ping or a
reason for dropping it. No broker, no database, no clock of its own — "now" is passed in,
so the simulator's accelerated time works and the rules are testable in microseconds.

The rules exist because a phone in a pocket lies: it reports 2 km jumps when the GNSS
fix drifts indoors, replays a buffer with yesterday's timestamps, and occasionally hands
back a position from the wrong hemisphere. Every one of those, unfiltered, becomes a cab
teleporting across a supervisor's map.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from math import asin, cos, radians, sin, sqrt
from typing import Any

PAYLOAD_VERSION = 1

# mqtt-topics.md: drop acc > 100 m, implied speed > 50 m/s, ts older than 24 h or more
# than 2 min in the future.
MAX_ACCURACY_M = 100.0
MAX_IMPLIED_SPEED_MS = 50.0
MAX_AGE = timedelta(hours=24)
MAX_FUTURE = timedelta(minutes=2)

#: Max pings in one batch payload (mqtt-topics.md).
MAX_BATCH = 500

EARTH_RADIUS_M = 6_371_008.8


class DropReason(StrEnum):
    """Why a ping was discarded. Recorded as a metric, never silently swallowed."""

    malformed = "malformed"
    wrong_version = "wrong_version"
    bad_coordinates = "bad_coordinates"
    inaccurate = "inaccurate"
    too_old = "too_old"
    too_far_future = "too_far_future"
    impossible_jump = "impossible_jump"
    batch_too_large = "batch_too_large"


@dataclass(frozen=True, slots=True)
class Ping:
    recorded_at: datetime
    lat: float
    lng: float
    speed_mps: float | None = None
    heading_deg: float | None = None
    accuracy_m: float | None = None
    battery_pct: int | None = None
    source: str = "app"


@dataclass(frozen=True, slots=True)
class Rejected:
    reason: DropReason
    detail: str


@dataclass(frozen=True, slots=True)
class ParsedBatch:
    """What one MQTT message yielded."""

    pings: list[Ping]
    rejected: list[Rejected]


def parse_payload(payload: Any) -> ParsedBatch:
    """Turn one MQTT message into pings, keeping per-ping rejections.

    One bad ping in a 500-ping reconnect batch must not lose the other 499 — a driver
    coming back from a tunnel is exactly when the data matters most.
    """
    if not isinstance(payload, dict):
        return ParsedBatch([], [Rejected(DropReason.malformed, "payload is not an object")])

    if "batch" in payload:
        raw_items = payload.get("batch")
        if not isinstance(raw_items, list):
            return ParsedBatch([], [Rejected(DropReason.malformed, "batch is not a list")])
        if len(raw_items) > MAX_BATCH:
            return ParsedBatch(
                [], [Rejected(DropReason.batch_too_large, f"{len(raw_items)} > {MAX_BATCH}")]
            )
        items = raw_items
    else:
        items = [payload]

    pings: list[Ping] = []
    rejected: list[Rejected] = []
    for item in items:
        result = _parse_one(item)
        (pings if isinstance(result, Ping) else rejected).append(result)  # type: ignore[arg-type]
    return ParsedBatch(pings, rejected)


def _parse_one(item: Any) -> Ping | Rejected:
    if not isinstance(item, dict):
        return Rejected(DropReason.malformed, "ping is not an object")

    version = item.get("v")
    if version != PAYLOAD_VERSION:
        return Rejected(DropReason.wrong_version, f"v={version!r}")

    recorded_at = _parse_time(item.get("ts"))
    if recorded_at is None:
        return Rejected(DropReason.malformed, f"ts={item.get('ts')!r}")

    lat, lng = _number(item.get("lat")), _number(item.get("lng"))
    if lat is None or lng is None:
        return Rejected(DropReason.malformed, "lat/lng missing or not numeric")
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        return Rejected(DropReason.bad_coordinates, f"lat={lat}, lng={lng}")

    battery = _number(item.get("bat"))
    return Ping(
        recorded_at=recorded_at,
        lat=lat,
        lng=lng,
        speed_mps=_number(item.get("spd")),
        heading_deg=_number(item.get("hdg")),
        accuracy_m=_number(item.get("acc")),
        battery_pct=int(battery) if battery is not None else None,
        source=str(item.get("src") or "app"),
    )


def check_ping(ping: Ping, now: datetime, previous: Ping | None = None) -> Rejected | None:
    """Apply the drop rules. `None` means keep it."""
    if ping.accuracy_m is not None and ping.accuracy_m > MAX_ACCURACY_M:
        return Rejected(DropReason.inaccurate, f"acc={ping.accuracy_m}")

    age = now - ping.recorded_at
    if age > MAX_AGE:
        return Rejected(DropReason.too_old, f"age={age}")
    if -age > MAX_FUTURE:
        return Rejected(DropReason.too_far_future, f"ahead={-age}")

    if previous is not None:
        seconds = (ping.recorded_at - previous.recorded_at).total_seconds()
        if seconds > 0:
            implied = distance_m(previous.lat, previous.lng, ping.lat, ping.lng) / seconds
            if implied > MAX_IMPLIED_SPEED_MS:
                return Rejected(
                    DropReason.impossible_jump, f"{implied:.0f} m/s over {seconds:.0f}s"
                )
    return None


def is_newer(ping: Ping, latest: Ping | None) -> bool:
    """Whether this ping should become the vehicle's "latest position".

    Out-of-order pings are stored but must not move the marker backwards
    (`mqtt-topics.md`): a buffered batch arriving after a live ping would otherwise drag
    the cab back down the road on the supervisor's map.
    """
    return latest is None or ping.recorded_at > latest.recorded_at


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    inner = (
        sin((phi2 - phi1) / 2) ** 2
        + cos(phi1) * cos(phi2) * sin((radians(lng2) - radians(lng1)) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * asin(sqrt(inner))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    # A naive timestamp is ambiguous, and guessing a zone silently shifts the whole track.
    return parsed if parsed.tzinfo is not None else None


def _number(value: Any) -> float | None:
    """A numeric field as a float, or None if absent or not a number.

    `bool` is excluded deliberately: `True == 1` in Python, so an unchecked `lat: true`
    would silently become latitude 1.0 somewhere off the coast of Africa.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
