"""Measuring what a cab really drove, from GPS pings (B38, B39)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.gps import distance_m
from app.domain.trip_distance import JITTER_METRES, Fix, path_length_m

T0 = datetime(2026, 10, 5, 4, 0, tzinfo=UTC)
LAT, LNG = 28.50, 77.30
#: A degree of latitude is about 111.2 km.
DEG_PER_100M = 100.0 / 111_195.0


def fix(seconds: float, north_m: float = 0.0, east_m: float = 0.0) -> Fix:
    return Fix(
        T0 + timedelta(seconds=seconds),
        LAT + north_m / 111_195.0,
        LNG + east_m / (111_195.0 * 0.8776),
    )


def test_a_straight_drive_is_its_length() -> None:
    fixes = [fix(i * 10, north_m=i * 100) for i in range(11)]  # 1 km at 36 km/h

    assert path_length_m(fixes) == pytest.approx(1000.0, rel=0.01)


def test_a_corner_counts_both_sides_of_it() -> None:
    fixes = [fix(0), fix(20, north_m=300), fix(40, north_m=300, east_m=400)]

    assert path_length_m(fixes) == pytest.approx(700.0, rel=0.01)


def test_the_order_in_time_decides_not_the_order_given() -> None:
    forward = [fix(i * 10, north_m=i * 100) for i in range(6)]

    assert path_length_m(list(reversed(forward))) == path_length_m(forward)


def test_a_cab_standing_still_is_not_credited_with_a_walk() -> None:
    """Five minutes parked, a ping every thirty seconds, each a few metres off."""
    wobble = [3, -4, 5, -2, 4, -5, 3, -3, 4, -4]
    fixes = [fix(i * 30, north_m=offset, east_m=-offset) for i, offset in enumerate(wobble)]

    assert path_length_m(fixes) == 0.0
    assert max(distance_m(a.lat, a.lng, b.lat, b.lng) for a in fixes for b in fixes) < 20


def test_a_crawl_in_traffic_is_not_rounded_down_to_nothing() -> None:
    """Walking pace, a ping every five seconds: every hop is under the jitter radius."""
    metres_per_ping = JITTER_METRES / 3
    fixes = [fix(i * 5, north_m=i * metres_per_ping) for i in range(61)]  # 60 hops, ~160 m

    assert path_length_m(fixes) == pytest.approx(60 * metres_per_ping, rel=0.1)


def test_a_bad_fix_is_skipped_and_the_path_continues_from_where_the_cab_was() -> None:
    good = [fix(0), fix(10, north_m=100), fix(30, north_m=300), fix(40, north_m=400)]
    with_a_leap = [good[0], good[1], fix(20, north_m=50_000), good[2], good[3]]

    assert path_length_m(with_a_leap) == pytest.approx(path_length_m(good), rel=0.01)


def test_a_leap_after_a_long_stop_is_still_a_bad_fix() -> None:
    """Ten parked minutes make a 2 km jump look like 12 km/h unless judged by the last fix."""
    parked = [fix(i * 30) for i in range(20)]
    leap = fix(600 + 5, north_m=2000)
    back = fix(600 + 10, north_m=1)

    assert path_length_m([*parked, leap, back]) == 0.0


def test_one_fix_or_none_is_no_distance() -> None:
    assert path_length_m([]) == 0.0
    assert path_length_m([fix(0)]) == 0.0


def test_two_fixes_at_the_same_instant_are_not_a_drive() -> None:
    assert path_length_m([fix(0), fix(0, north_m=500)]) == 0.0
