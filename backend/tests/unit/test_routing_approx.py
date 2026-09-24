"""The approx provider: correct arithmetic, time-of-day speeds, and no network at all."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest

from app.core.clock import FakeClock
from app.domain.geo import LatLng, haversine_km
from app.modules.routing.approx import IST, ApproxConfig, ApproxRoutingProvider, SpeedWindow
from app.modules.routing.types import Source

# Sector 62 Noida -> Sector 135 Noida, the fixture pair used across the docs.
ORIGIN = LatLng(lat=28.5703, lng=77.3218)
DESTINATION = LatLng(lat=28.5123, lng=77.3910)

# 12:00 IST = 06:30 UTC: outside every configured window, so the base speed applies.
OFF_PEAK = datetime(2026, 9, 24, 6, 30, tzinfo=UTC)
MORNING_PEAK = datetime(2026, 9, 24, 3, 30, tzinfo=UTC)  # 09:00 IST


def provider(now: datetime, config: ApproxConfig | None = None) -> ApproxRoutingProvider:
    return ApproxRoutingProvider(FakeClock(now), config)


async def test_distance_is_haversine_times_the_road_factor() -> None:
    config = ApproxConfig()
    result = await provider(OFF_PEAK, config).route(ORIGIN, DESTINATION)
    expected_m = haversine_km(ORIGIN, DESTINATION) * config.road_factor * 1000.0
    assert result.distance_meters == pytest.approx(expected_m)


async def test_duration_follows_distance_and_speed() -> None:
    config = ApproxConfig(base_speed_kmh=24.0, road_factor=1.4, windows=())
    result = await provider(OFF_PEAK, config).route(ORIGIN, DESTINATION)
    expected_s = (haversine_km(ORIGIN, DESTINATION) * 1.4 / 24.0) * 3600.0
    assert result.duration_seconds == pytest.approx(expected_s)
    assert result.duration_minutes == pytest.approx(expected_s / 60)


async def test_results_are_always_flagged_approximate() -> None:
    result = await provider(OFF_PEAK).route(ORIGIN, DESTINATION)
    assert result.approximate is True
    assert result.source is Source.approx


async def test_peak_hours_are_slower_than_off_peak() -> None:
    """simulator-spec.md §6: 08:00-10:30 IST runs at 0.6 of normal speed."""
    off_peak = await provider(OFF_PEAK).route(ORIGIN, DESTINATION)
    peak = await provider(MORNING_PEAK).route(ORIGIN, DESTINATION)
    assert peak.duration_seconds == pytest.approx(off_peak.duration_seconds / 0.6)
    assert peak.distance_meters == pytest.approx(off_peak.distance_meters)


async def test_identical_points_cost_nothing() -> None:
    result = await provider(OFF_PEAK).route(ORIGIN, ORIGIN)
    assert result.distance_meters == pytest.approx(0.0)
    assert result.duration_seconds == pytest.approx(0.0)


async def test_table_matches_pairwise_routes() -> None:
    third = LatLng(lat=28.6000, lng=77.4000)
    routing = provider(OFF_PEAK)

    table = await routing.table([ORIGIN, third], [DESTINATION, third])

    assert len(table.durations) == 2
    assert len(table.durations[0]) == 2
    assert table.approximate is True
    for i, origin in enumerate([ORIGIN, third]):
        for j, destination in enumerate([DESTINATION, third]):
            single = await routing.route(origin, destination)
            assert table.durations[i][j] == pytest.approx(single.duration_seconds)
            assert table.distances[i][j] == pytest.approx(single.distance_meters)


async def test_geometry_is_the_straight_line() -> None:
    """There is no road network, so the honest geometry is origin -> destination."""
    result = await provider(OFF_PEAK).route(ORIGIN, DESTINATION)
    assert result.geometry == (ORIGIN, DESTINATION)


async def test_no_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """B01/I02 acceptance: approx must work with the network unplugged."""
    import httpx

    def explode(*args: object, **kwargs: object) -> None:
        raise AssertionError("approx must never touch the network")

    monkeypatch.setattr(httpx.AsyncClient, "get", explode)
    monkeypatch.setattr(httpx.AsyncClient, "request", explode)
    monkeypatch.setattr(httpx.AsyncClient, "send", explode)

    result = await provider(OFF_PEAK).route(ORIGIN, DESTINATION)
    assert result.duration_seconds > 0


def test_speed_window_wrapping_past_midnight() -> None:
    night = SpeedWindow(time(23, 0), time(6, 0), 1.3)
    assert night.contains(time(23, 30)) is True
    assert night.contains(time(2, 0)) is True
    assert night.contains(time(6, 0)) is False
    assert night.contains(time(12, 0)) is False


def test_speed_window_normal_order() -> None:
    peak = SpeedWindow(time(8, 0), time(10, 30), 0.6)
    assert peak.contains(time(8, 0)) is True
    assert peak.contains(time(10, 29)) is True
    assert peak.contains(time(10, 30)) is False


def test_windows_are_evaluated_in_ist_not_utc() -> None:
    """09:00 IST is 03:30 UTC; reading the clock as UTC would miss the morning peak."""
    config = ApproxConfig()
    ist_local = MORNING_PEAK.astimezone(IST).time()
    utc_local = MORNING_PEAK.time()
    assert config.speed_kmh_at(ist_local) < config.speed_kmh_at(utc_local)


async def test_time_of_day_is_read_from_the_injected_clock() -> None:
    clock = FakeClock(OFF_PEAK)
    routing = ApproxRoutingProvider(clock)
    off_peak = await routing.route(ORIGIN, DESTINATION)

    clock.set(MORNING_PEAK)
    peak = await routing.route(ORIGIN, DESTINATION)

    assert peak.duration_seconds > off_peak.duration_seconds


async def test_zero_speed_configuration_does_not_divide_by_zero() -> None:
    config = ApproxConfig(base_speed_kmh=0.0, windows=())
    result = await provider(OFF_PEAK, config).route(ORIGIN, DESTINATION)
    assert result.duration_seconds == 0.0


def test_night_window_is_faster_than_base() -> None:
    config = ApproxConfig()
    assert config.speed_kmh_at(time(1, 0)) > config.speed_kmh_at(time(12, 0))


async def test_clock_advance_moves_into_the_peak() -> None:
    clock = FakeClock(datetime(2026, 9, 24, 2, 0, tzinfo=UTC))  # 07:30 IST, off peak
    routing = ApproxRoutingProvider(clock)
    before = await routing.route(ORIGIN, DESTINATION)
    clock.advance(timedelta(hours=2))  # 09:30 IST, peak
    after = await routing.route(ORIGIN, DESTINATION)
    assert after.duration_seconds > before.duration_seconds
