"""ETA service: the time-of-day factor and the degradation ladder (B10).

The point of these tests is that dispatch keeps getting an answer, and that the answer
never claims more precision than it has.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import httpx
import pytest

from app.core.clock import FakeClock
from app.domain.geo import LatLng
from app.modules.routing.approx import ApproxRoutingProvider
from app.modules.routing.cache import CachedRoutingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.rate_limit import UnlimitedRateLimiter
from app.modules.routing.service import EtaConfig, EtaService, TrafficWindow
from app.modules.routing.types import RouteResult, Source, TableResult
from tests.fakes import FakeRedis

ORIGIN = LatLng(lat=28.5703, lng=77.3218)
DESTINATION = LatLng(lat=28.5123, lng=77.3910)

OFF_PEAK = datetime(2026, 9, 24, 6, 30, tzinfo=UTC)  # 12:00 IST
MORNING_PEAK = datetime(2026, 9, 24, 3, 30, tzinfo=UTC)  # 09:00 IST
NIGHT = datetime(2026, 9, 24, 19, 30, tzinfo=UTC)  # 01:00 IST

OSRM_ROUTE = {
    "code": "Ok",
    "routes": [{"duration": 600.0, "distance": 5000.0, "geometry": {"coordinates": []}}],
}
OSRM_TABLE = {
    "code": "Ok",
    "durations": [[0.0, 600.0], [660.0, 0.0]],
    "distances": [[0.0, 5000.0], [5200.0, 0.0]],
}


class StubProvider:
    """A provider with fully controlled output, so the service is tested in isolation."""

    name = "stub"

    def __init__(self, duration: float = 600.0, approximate: bool = False) -> None:
        self.duration = duration
        self.approximate = approximate
        self.route_calls = 0
        self.table_calls = 0

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        self.route_calls += 1
        return RouteResult(
            duration_seconds=self.duration,
            distance_meters=5000.0,
            source=Source.approx if self.approximate else Source.osrm,
            approximate=self.approximate,
        )

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        self.table_calls += 1
        return TableResult(
            durations=tuple(tuple(self.duration for _ in destinations) for _ in origins),
            distances=tuple(tuple(5000.0 for _ in destinations) for _ in origins),
            source=Source.approx if self.approximate else Source.osrm,
            approximate=self.approximate,
        )

    async def close(self) -> None:
        return None


def osrm_provider(handler: object) -> OsrmRoutingProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # type: ignore[arg-type]
    return OsrmRoutingProvider(
        "https://osrm.internal",
        fallback=ApproxRoutingProvider(FakeClock(OFF_PEAK)),
        limiter=UnlimitedRateLimiter(),
        user_agent="flex-platform/0.1 (contact: dev@example.com)",
        client=client,
    )


# --- time-of-day factor ------------------------------------------------------


async def test_off_peak_eta_is_the_routed_duration() -> None:
    service = EtaService(StubProvider(600.0), FakeClock(OFF_PEAK))
    estimate = await service.eta(ORIGIN, DESTINATION)
    assert estimate.seconds == pytest.approx(600.0)
    assert estimate.minutes == pytest.approx(10.0)


async def test_peak_eta_is_stretched() -> None:
    """ADR-0004: ETAs start from OSM speeds plus time-of-day factors."""
    service = EtaService(StubProvider(600.0), FakeClock(MORNING_PEAK))
    assert (await service.eta(ORIGIN, DESTINATION)).seconds == pytest.approx(1000.0)


async def test_night_eta_is_shortened() -> None:
    service = EtaService(StubProvider(600.0), FakeClock(NIGHT))
    assert (await service.eta(ORIGIN, DESTINATION)).seconds == pytest.approx(600.0 / 1.3)


async def test_the_factor_is_not_applied_to_approx_results() -> None:
    """`approx` already priced in the time of day; factoring again double-counts."""
    service = EtaService(StubProvider(600.0, approximate=True), FakeClock(MORNING_PEAK))
    assert (await service.eta(ORIGIN, DESTINATION)).seconds == pytest.approx(600.0)


async def test_windows_are_read_in_ist_not_utc() -> None:
    """09:00 IST is 03:30 UTC; reading the clock as UTC would miss the peak entirely."""
    peak = EtaService(StubProvider(600.0), FakeClock(MORNING_PEAK))
    same_utc_hour = EtaService(
        StubProvider(600.0), FakeClock(datetime(2026, 9, 24, 9, 0, tzinfo=UTC))
    )
    assert (await peak.eta(ORIGIN, DESTINATION)).seconds > (
        await same_utc_hour.eta(ORIGIN, DESTINATION)
    ).seconds


async def test_factors_come_from_config_not_code() -> None:
    config = EtaConfig(windows=(TrafficWindow(time(0, 0), time(23, 59), 2.0),))
    service = EtaService(StubProvider(600.0), FakeClock(OFF_PEAK), config)
    assert (await service.eta(ORIGIN, DESTINATION)).seconds == pytest.approx(1200.0)


def test_window_wrapping_past_midnight() -> None:
    window = TrafficWindow(time(23, 0), time(6, 0), 2.0)
    assert window.contains(time(23, 30)) is True
    assert window.contains(time(3, 0)) is True
    assert window.contains(time(12, 0)) is False


def test_default_config_has_both_peaks() -> None:
    config = EtaConfig()
    assert config.factor_at(time(9, 0)) > 1.0
    assert config.factor_at(time(18, 30)) > 1.0
    assert config.factor_at(time(12, 0)) == 1.0
    assert config.factor_at(time(1, 0)) < 1.0


# --- results -----------------------------------------------------------------


async def test_arrival_time_is_now_plus_the_eta() -> None:
    clock = FakeClock(OFF_PEAK)
    service = EtaService(StubProvider(600.0), clock)
    arrival, approximate = await service.arrival_time(ORIGIN, DESTINATION)
    assert arrival == OFF_PEAK + timedelta(minutes=10)
    assert approximate is False


async def test_source_is_reported() -> None:
    service = EtaService(StubProvider(600.0), FakeClock(OFF_PEAK))
    assert (await service.eta(ORIGIN, DESTINATION)).source is Source.osrm


async def test_matrix_shape_and_one_provider_call() -> None:
    """A per-pair loop would burn the whole public-server budget."""
    provider = StubProvider(600.0)
    service = EtaService(provider, FakeClock(OFF_PEAK))

    matrix = await service.eta_matrix([ORIGIN, DESTINATION], [ORIGIN, DESTINATION, ORIGIN])

    assert len(matrix) == 2
    assert len(matrix[0]) == 3
    assert provider.table_calls == 1
    assert provider.route_calls == 0


async def test_matrix_applies_the_same_factor() -> None:
    service = EtaService(StubProvider(600.0), FakeClock(MORNING_PEAK))
    matrix = await service.eta_matrix([ORIGIN], [DESTINATION])
    assert matrix[0][0].seconds == pytest.approx(1000.0)


# --- degradation ladder (the operational heart of B10) -----------------------


async def test_osrm_result_is_not_approximate() -> None:
    service = EtaService(
        osrm_provider(lambda r: httpx.Response(200, json=OSRM_ROUTE)), FakeClock(OFF_PEAK)
    )
    estimate = await service.eta(ORIGIN, DESTINATION)
    assert estimate.approximate is False
    assert estimate.source is Source.osrm
    assert estimate.seconds == pytest.approx(600.0)


async def test_eta_degrades_to_approx_when_osrm_errors() -> None:
    service = EtaService(
        osrm_provider(lambda r: httpx.Response(500, text="boom")), FakeClock(OFF_PEAK)
    )
    estimate = await service.eta(ORIGIN, DESTINATION)
    assert estimate.approximate is True
    assert estimate.source is Source.approx
    assert estimate.seconds > 0, "dispatch must still get a usable number"


async def test_eta_degrades_to_approx_on_timeout() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    service = EtaService(osrm_provider(timeout), FakeClock(OFF_PEAK))
    assert (await service.eta(ORIGIN, DESTINATION)).approximate is True


async def test_eta_degrades_to_approx_when_rate_limited() -> None:
    """The public-server budget is spent: answer approximately, never queue or fail."""

    class Deny:
        async def try_acquire(self, service: str) -> bool:
            return False

    provider = OsrmRoutingProvider(
        "https://router.project-osrm.org",
        fallback=ApproxRoutingProvider(FakeClock(OFF_PEAK)),
        limiter=Deny(),
        user_agent="flex-platform/0.1 (contact: dev@example.com)",
        client=httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json=OSRM_ROUTE))
        ),
    )
    estimate = await EtaService(provider, FakeClock(OFF_PEAK)).eta(ORIGIN, DESTINATION)
    assert estimate.approximate is True
    assert estimate.source is Source.approx


async def test_matrix_degrades_too() -> None:
    service = EtaService(
        osrm_provider(lambda r: httpx.Response(503, text="unavailable")), FakeClock(OFF_PEAK)
    )
    matrix = await service.eta_matrix([ORIGIN], [DESTINATION])
    assert matrix[0][0].approximate is True
    assert matrix[0][0].seconds > 0


async def test_the_full_ladder_cache_then_osrm_then_approx() -> None:
    """Cache hit -> OSRM call -> approx, as described in architecture.md §3.4."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json=OSRM_ROUTE)

    clock = FakeClock(OFF_PEAK)
    cached = CachedRoutingProvider(osrm_provider(handler), FakeRedis(clock), ttl_seconds=900)
    service = EtaService(cached, clock)

    first = await service.eta(ORIGIN, DESTINATION)
    second = await service.eta(ORIGIN, DESTINATION)

    assert len(calls) == 1, "the repeat must be served from cache"
    assert first.source is Source.osrm
    assert second.source is Source.cache
    assert second.approximate is False
    assert second.seconds == pytest.approx(first.seconds)


async def test_approximate_results_are_never_cached_so_recovery_is_immediate() -> None:
    state = {"failing": True}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["failing"]:
            return httpx.Response(503, text="down")
        return httpx.Response(200, json=OSRM_ROUTE)

    clock = FakeClock(OFF_PEAK)
    cached = CachedRoutingProvider(osrm_provider(handler), FakeRedis(clock), ttl_seconds=900)
    service = EtaService(cached, clock)

    degraded = await service.eta(ORIGIN, DESTINATION)
    assert degraded.approximate is True

    state["failing"] = False
    recovered = await service.eta(ORIGIN, DESTINATION)
    assert recovered.approximate is False, "a cached approx answer would outlive the outage"


# --- no geocoding ------------------------------------------------------------


def test_the_service_exposes_no_geocoding() -> None:
    """B10 explicitly ships no address lookup (ADR-0010 A1)."""
    assert not [name for name in dir(EtaService) if "geocode" in name or "search" in name]
