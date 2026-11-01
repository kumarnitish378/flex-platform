"""Learned speeds (B37, OQ-22): the arithmetic, and `approx` listening to it."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.clock import FakeClock
from app.domain.geo import LatLng
from app.domain.speed_profile import (
    MAX_PLAUSIBLE_KPH,
    SLOTS,
    Leg,
    SlotStat,
    accumulate,
    slot_of,
    speeds,
    usable,
)
from app.modules.routing.approx import ApproxConfig, ApproxRoutingProvider
from app.modules.routing.speed_profile import LearnedSpeeds

TZ = "Asia/Kolkata"
# Monday 2026-10-05 09:00 IST is hour 9 of the week.
MONDAY_9AM = datetime(2026, 10, 5, 3, 30, tzinfo=UTC)
FROM, TO = LatLng(28.50, 77.30), LatLng(28.56, 77.32)


def leg(minutes: float, metres: float, at: datetime = MONDAY_9AM) -> Leg:
    return Leg(at, at + timedelta(minutes=minutes), metres)


def test_slots_count_the_hours_of_the_week_in_local_time() -> None:
    assert slot_of(MONDAY_9AM, TZ) == 9
    assert slot_of(datetime(2026, 10, 4, 18, 29, tzinfo=UTC), TZ) == 6 * 24 + 23  # Sun 23:59 IST
    assert slot_of(datetime(2026, 10, 4, 18, 30, tzinfo=UTC), TZ) == 0  # Mon 00:00 IST
    assert SLOTS == 168


def test_a_leg_is_usable_only_if_it_says_something_about_speed() -> None:
    assert usable(leg(10, 3000))
    assert not usable(leg(10, 50)), "barely moved: parking, not driving"
    assert not usable(leg(0, 3000)), "no time at all"
    assert not usable(leg(-5, 3000))
    assert not usable(leg(4 * 60, 3000)), "stopped for tea"
    fast = MAX_PLAUSIBLE_KPH / 3.6 * 600 * 1.1
    assert not usable(leg(10, fast)), "a mis-timed stop, not a cab that flew"


def test_a_slots_speed_is_total_distance_over_total_time() -> None:
    """Not the mean of the speeds: a short fast leg must not outvote a long slow one."""
    legs = [leg(10, 1000), leg(60, 6000)]  # 6 km/h, 6 km/h ... then a fast short one
    legs.append(leg(1, 1000))  # 60 km/h but only a minute

    stats = accumulate({}, legs, TZ)

    stat = stats[9]
    assert stat.samples == 3
    assert stat.speed_kph() == pytest.approx((8000 / (71 * 60)) * 3.6, rel=1e-6)
    speed = stat.speed_kph()
    assert speed is not None and speed < 8.0, "the mean of the three speeds would be about 24"


def test_accumulating_twice_equals_accumulating_once() -> None:
    first = [leg(10, 2500)]
    second = [leg(20, 5000, MONDAY_9AM + timedelta(days=7))]

    two_steps = accumulate(accumulate({}, first, TZ), second, TZ)
    one_step = accumulate({}, first + second, TZ)

    assert two_steps == one_step


def test_a_leg_is_attributed_to_the_hour_it_started_in() -> None:
    straddling = Leg(
        datetime(2026, 10, 5, 3, 55, tzinfo=UTC),  # 09:25 IST
        datetime(2026, 10, 5, 4, 45, tzinfo=UTC),  # 10:15 IST
        8000,
    )

    assert set(accumulate({}, [straddling], TZ)) == {9}


def test_only_slots_with_enough_samples_are_trusted() -> None:
    stats = {9: SlotStat(5000, 1000, 3), 10: SlotStat(5000, 1000, 40)}

    assert speeds(stats, min_samples=20) == {10: pytest.approx(18.0)}
    assert speeds(stats, min_samples=1).keys() == {9, 10}


def test_unusable_legs_change_nothing() -> None:
    assert accumulate({}, [leg(10, 10), leg(0, 3000)], TZ) == {}


# --- approx listens --------------------------------------------------------------------------


async def eta_seconds(learned: LearnedSpeeds | None, when: datetime = MONDAY_9AM) -> float:
    provider = ApproxRoutingProvider(FakeClock(when), ApproxConfig(), learned)
    return (await provider.route(FROM, TO)).duration_seconds


async def test_a_learned_speed_changes_the_estimate_measurably() -> None:
    clock = FakeClock(MONDAY_9AM)
    constant = await eta_seconds(None)
    slower = await eta_seconds(LearnedSpeeds.fixed(clock, {9: 8.0}))
    faster = await eta_seconds(LearnedSpeeds.fixed(clock, {9: 40.0}))

    assert slower > constant * 1.5
    assert faster < constant * 0.6


async def test_the_estimate_is_distance_x_road_factor_over_the_learned_speed() -> None:
    from app.domain.geo import haversine_km

    clock = FakeClock(MONDAY_9AM)

    seconds = await eta_seconds(LearnedSpeeds.fixed(clock, {9: 12.0}))

    expected = haversine_km(FROM, TO) * ApproxConfig().road_factor / 12.0 * 3600.0
    assert seconds == pytest.approx(expected)


async def test_a_slot_with_nothing_learned_keeps_the_constant() -> None:
    clock = FakeClock(MONDAY_9AM)

    assert await eta_seconds(LearnedSpeeds.fixed(clock, {23: 5.0})) == await eta_seconds(None)


async def test_only_the_matching_hour_of_the_week_is_affected() -> None:
    clock = FakeClock(MONDAY_9AM)
    learned = LearnedSpeeds.fixed(clock, {9: 8.0})
    next_hour = MONDAY_9AM + timedelta(hours=1)

    assert await eta_seconds(learned, next_hour) == await eta_seconds(None, next_hour)
    assert await eta_seconds(learned, MONDAY_9AM + timedelta(days=1)) == await eta_seconds(
        None, MONDAY_9AM + timedelta(days=1)
    )


# --- the view ---------------------------------------------------------------------------------


async def test_the_view_reloads_on_a_timer_and_survives_a_failed_load() -> None:
    clock = FakeClock(MONDAY_9AM)
    loads = {"count": 0, "fail": False}

    async def loader() -> dict[int, float]:
        loads["count"] += 1
        if loads["fail"]:
            raise RuntimeError("database down")
        return {9: 10.0 + loads["count"]}

    view = LearnedSpeeds(clock, loader, refresh=timedelta(hours=1))

    await view.ensure_fresh()
    await view.ensure_fresh()
    assert loads["count"] == 1 and view.speed_kph(9) == 11.0

    clock.advance(timedelta(minutes=61))
    loads["fail"] = True
    await view.ensure_fresh()  # fails, and must not raise
    assert loads["count"] == 2 and view.speed_kph(9) == 11.0, "keeps what it had"
    await view.ensure_fresh()
    assert loads["count"] == 2, "does not hammer a database that is down"

    clock.advance(timedelta(minutes=61))
    loads["fail"] = False
    await view.ensure_fresh()
    assert view.speed_kph(9) == 13.0
