"""GPS payload parsing and the drop rules (B12, `mqtt-topics.md`).

Pure and fast, because these rules run tens of times a second forever and every one of
them exists to stop a cab teleporting across a supervisor's map.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.domain.gps import (
    MAX_BATCH,
    DropReason,
    Ping,
    check_ping,
    distance_m,
    is_newer,
    parse_payload,
)

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)


def payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "v": 1,
        "ts": NOW.isoformat().replace("+00:00", "Z"),
        "lat": 28.5123,
        "lng": 77.3910,
        "spd": 8.4,
        "hdg": 132,
        "acc": 6.5,
        "bat": 71,
        "src": "app",
    }
    body.update(overrides)
    return body


def ping_at(offset_seconds: float = 0, lat: float = 28.5, lng: float = 77.3, **kwargs: Any) -> Ping:
    return Ping(recorded_at=NOW + timedelta(seconds=offset_seconds), lat=lat, lng=lng, **kwargs)


# --- parsing --------------------------------------------------------------------------


def test_a_single_ping_parses() -> None:
    result = parse_payload(payload())
    assert len(result.pings) == 1
    assert result.rejected == []

    ping = result.pings[0]
    assert ping.lat == 28.5123
    assert ping.speed_mps == 8.4
    assert ping.battery_pct == 71
    assert ping.source == "app"


def test_optional_fields_may_be_absent() -> None:
    result = parse_payload({"v": 1, "ts": NOW.isoformat(), "lat": 28.5, "lng": 77.3})
    assert len(result.pings) == 1
    assert result.pings[0].speed_mps is None
    assert result.pings[0].source == "app"


def test_a_batch_parses() -> None:
    result = parse_payload({"v": 1, "batch": [payload(), payload(lat=28.6)]})
    assert len(result.pings) == 2


def test_one_bad_ping_does_not_lose_the_batch() -> None:
    """A driver coming out of a tunnel is exactly when the data matters most."""
    result = parse_payload({"batch": [payload(), {"v": 1, "ts": "nonsense"}, payload(lat=28.6)]})
    assert len(result.pings) == 2
    assert len(result.rejected) == 1


def test_an_oversized_batch_is_refused() -> None:
    result = parse_payload({"batch": [payload()] * (MAX_BATCH + 1)})
    assert result.pings == []
    assert result.rejected[0].reason is DropReason.batch_too_large


def test_a_batch_at_the_limit_is_accepted() -> None:
    result = parse_payload({"batch": [payload()] * MAX_BATCH})
    assert len(result.pings) == MAX_BATCH


@pytest.mark.parametrize("bad", [None, [], "string", 42])
def test_a_non_object_payload_is_rejected(bad: object) -> None:
    result = parse_payload(bad)
    assert result.pings == []
    assert result.rejected[0].reason is DropReason.malformed


def test_a_wrong_payload_version_is_rejected() -> None:
    """The topic is versioned so payloads can change; an unknown version is not guessed."""
    result = parse_payload(payload(v=2))
    assert result.rejected[0].reason is DropReason.wrong_version


@pytest.mark.parametrize("ts", ["", "yesterday", "2026-13-45T00:00:00Z", 12345])
def test_an_unparseable_timestamp_is_rejected(ts: object) -> None:
    assert parse_payload(payload(ts=ts)).rejected[0].reason is DropReason.malformed


def test_a_naive_timestamp_is_rejected() -> None:
    """Guessing a timezone would silently shift an entire track."""
    result = parse_payload(payload(ts="2026-09-24T04:30:00"))
    assert result.rejected[0].reason is DropReason.malformed


@pytest.mark.parametrize(
    ("lat", "lng"), [(91.0, 77.0), (-91.0, 77.0), (28.0, 181.0), (28.0, -181.0)]
)
def test_out_of_range_coordinates_are_rejected(lat: float, lng: float) -> None:
    result = parse_payload(payload(lat=lat, lng=lng))
    assert result.rejected[0].reason is DropReason.bad_coordinates


def test_missing_coordinates_are_rejected() -> None:
    assert parse_payload({"v": 1, "ts": NOW.isoformat()}).rejected[0].reason is DropReason.malformed


def test_a_boolean_is_not_a_coordinate() -> None:
    """`True == 1` in Python; lat=True must not become latitude 1."""
    result = parse_payload(payload(lat=True))
    assert result.rejected[0].reason is DropReason.malformed


# --- the drop rules -------------------------------------------------------------------


def test_a_good_ping_is_kept() -> None:
    assert check_ping(ping_at(), NOW) is None


def test_an_inaccurate_fix_is_dropped() -> None:
    """mqtt-topics.md: acc > 100 m. An indoor fix drifts by kilometres."""
    assert check_ping(ping_at(accuracy_m=101.0), NOW) is not None
    assert check_ping(ping_at(accuracy_m=100.0), NOW) is None


def test_a_ping_older_than_a_day_is_dropped() -> None:
    assert check_ping(ping_at(offset_seconds=-24 * 3600 - 1), NOW) is not None
    assert check_ping(ping_at(offset_seconds=-24 * 3600 + 60), NOW) is None


def test_a_ping_from_the_future_is_dropped() -> None:
    """A phone with a wrong clock would otherwise pin itself at the top of every sort."""
    assert check_ping(ping_at(offset_seconds=121), NOW) is not None
    assert check_ping(ping_at(offset_seconds=119), NOW) is None


def test_the_drop_reason_is_specific() -> None:
    assert check_ping(ping_at(accuracy_m=500), NOW).reason is DropReason.inaccurate  # type: ignore[union-attr]
    assert check_ping(ping_at(offset_seconds=-90000), NOW).reason is DropReason.too_old  # type: ignore[union-attr]
    assert check_ping(ping_at(offset_seconds=600), NOW).reason is DropReason.too_far_future  # type: ignore[union-attr]


def test_an_impossible_jump_is_dropped() -> None:
    """50 m/s is 180 km/h; anything faster is a bad fix, not a cab."""
    previous = ping_at(0, lat=28.50, lng=77.30)
    # ~10 km in 10 seconds.
    teleported = ping_at(10, lat=28.59, lng=77.30)
    rejection = check_ping(teleported, NOW + timedelta(seconds=10), previous)
    assert rejection is not None
    assert rejection.reason is DropReason.impossible_jump


def test_a_plausible_move_is_kept() -> None:
    previous = ping_at(0, lat=28.5000, lng=77.3000)
    # ~110 m in 10 s = 11 m/s, about 40 km/h.
    moved = ping_at(10, lat=28.5010, lng=77.3000)
    assert check_ping(moved, NOW + timedelta(seconds=10), previous) is None


def test_the_jump_check_needs_elapsed_time() -> None:
    """Two pings with the same timestamp imply infinite speed; do not divide by zero."""
    previous = ping_at(0, lat=28.50, lng=77.30)
    same_instant = ping_at(0, lat=28.90, lng=77.30)
    assert check_ping(same_instant, NOW, previous) is None


def test_the_first_ping_has_nothing_to_jump_from() -> None:
    assert check_ping(ping_at(lat=28.9, lng=77.9), NOW, None) is None


# --- ordering -------------------------------------------------------------------------


def test_a_newer_ping_moves_the_marker() -> None:
    assert is_newer(ping_at(10), ping_at(0)) is True


def test_an_older_ping_does_not_move_the_marker() -> None:
    """Out-of-order pings are stored but must not drag the cab back down the road."""
    assert is_newer(ping_at(0), ping_at(10)) is False


def test_the_same_timestamp_does_not_move_the_marker() -> None:
    assert is_newer(ping_at(5), ping_at(5)) is False


def test_the_first_ping_always_moves_the_marker() -> None:
    assert is_newer(ping_at(), None) is True


# --- distance -------------------------------------------------------------------------


def test_distance_between_the_fixture_points() -> None:
    # Sector 62 to Sector 135, Noida: about 9 km.
    metres = distance_m(28.5703, 77.3218, 28.5123, 77.3910)
    assert 8_000 < metres < 11_000


def test_distance_to_the_same_point_is_zero() -> None:
    assert distance_m(28.5, 77.3, 28.5, 77.3) == pytest.approx(0.0)
