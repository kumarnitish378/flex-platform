"""The Redis cache in front of a routing provider."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.clock import FakeClock
from app.domain.geo import LatLng
from app.modules.routing.cache import CachedRoutingProvider
from app.modules.routing.types import RouteResult, Source, TableResult
from tests.fakes import FakeRedis

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
ORIGIN = LatLng(lat=28.5703, lng=77.3218)
DESTINATION = LatLng(lat=28.5123, lng=77.3910)


class CountingProvider:
    """Records how often the wrapped provider is actually consulted."""

    name = "counting"

    def __init__(self, approximate: bool = False) -> None:
        self.route_calls = 0
        self.table_calls = 0
        self._approximate = approximate

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        self.route_calls += 1
        return RouteResult(
            duration_seconds=1380.0,
            distance_meters=9123.0,
            source=Source.approx if self._approximate else Source.osrm,
            approximate=self._approximate,
            geometry=(origin, destination),
        )

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        self.table_calls += 1
        return TableResult(
            durations=tuple(tuple(60.0 for _ in destinations) for _ in origins),
            distances=tuple(tuple(900.0 for _ in destinations) for _ in origins),
            source=Source.approx if self._approximate else Source.osrm,
            approximate=self._approximate,
        )

    async def close(self) -> None:
        return None


def build(
    approximate: bool = False, ttl: int = 900
) -> tuple[CachedRoutingProvider, CountingProvider, FakeRedis]:
    inner = CountingProvider(approximate)
    redis = FakeRedis(FakeClock(NOW))
    return CachedRoutingProvider(inner, redis, ttl_seconds=ttl), inner, redis


async def test_miss_then_hit() -> None:
    cached, inner, _ = build()

    first = await cached.route(ORIGIN, DESTINATION)
    second = await cached.route(ORIGIN, DESTINATION)

    assert inner.route_calls == 1, "second call must be served from cache"
    assert first.source is Source.osrm
    assert second.source is Source.cache
    assert second.duration_seconds == first.duration_seconds
    assert second.approximate is False


async def test_geometry_survives_the_round_trip() -> None:
    cached, _, _ = build()
    await cached.route(ORIGIN, DESTINATION)
    hit = await cached.route(ORIGIN, DESTINATION)
    assert hit.geometry == (ORIGIN, DESTINATION)


async def test_different_points_are_different_entries() -> None:
    cached, inner, _ = build()
    await cached.route(ORIGIN, DESTINATION)
    await cached.route(DESTINATION, ORIGIN)
    assert inner.route_calls == 2


async def test_nearby_points_share_an_entry() -> None:
    """Rounding to ~11 m keeps a nudged map pin on the same cache entry."""
    cached, inner, _ = build()
    await cached.route(ORIGIN, DESTINATION)
    nudged = LatLng(lat=ORIGIN.lat + 0.000001, lng=ORIGIN.lng)
    await cached.route(nudged, DESTINATION)
    assert inner.route_calls == 1


async def test_entry_expires_after_the_ttl() -> None:
    inner = CountingProvider()
    clock = FakeClock(NOW)
    redis = FakeRedis(clock)
    cached = CachedRoutingProvider(inner, redis, ttl_seconds=900)

    await cached.route(ORIGIN, DESTINATION)
    clock.advance(timedelta(seconds=899))
    await cached.route(ORIGIN, DESTINATION)
    assert inner.route_calls == 1

    clock.advance(timedelta(seconds=2))
    await cached.route(ORIGIN, DESTINATION)
    assert inner.route_calls == 2


async def test_approximate_results_are_never_cached() -> None:
    """Caching a degraded answer would outlive the outage that caused it."""
    cached, inner, redis = build(approximate=True)

    await cached.route(ORIGIN, DESTINATION)
    await cached.route(ORIGIN, DESTINATION)

    assert inner.route_calls == 2
    assert redis.store == {}


async def test_table_is_cached() -> None:
    cached, inner, _ = build()
    await cached.table([ORIGIN], [DESTINATION])
    result = await cached.table([ORIGIN], [DESTINATION])
    assert inner.table_calls == 1
    assert result.source is Source.cache
    assert result.durations[0][0] == pytest.approx(60.0)


async def test_table_key_depends_on_shape() -> None:
    cached, inner, _ = build()
    await cached.table([ORIGIN], [DESTINATION])
    await cached.table([ORIGIN], [DESTINATION, ORIGIN])
    assert inner.table_calls == 2


async def test_zero_ttl_disables_caching() -> None:
    cached, inner, redis = build(ttl=0)
    await cached.route(ORIGIN, DESTINATION)
    await cached.route(ORIGIN, DESTINATION)
    assert inner.route_calls == 2
    assert redis.get_calls == 0


async def test_redis_read_failure_is_survivable() -> None:
    inner = CountingProvider()
    redis = FakeRedis(FakeClock(NOW), fail_on={"get"})
    cached = CachedRoutingProvider(inner, redis)

    result = await cached.route(ORIGIN, DESTINATION)
    assert result.duration_seconds == pytest.approx(1380.0)
    assert inner.route_calls == 1


async def test_redis_write_failure_is_survivable() -> None:
    inner = CountingProvider()
    redis = FakeRedis(FakeClock(NOW), fail_on={"set"})
    cached = CachedRoutingProvider(inner, redis)

    result = await cached.route(ORIGIN, DESTINATION)
    assert result.approximate is False
    assert inner.route_calls == 1


async def test_corrupt_cache_entry_is_ignored() -> None:
    cached, inner, redis = build()
    await cached.route(ORIGIN, DESTINATION)
    key = next(iter(redis.store))
    redis.store[key].value = "{not json"

    result = await cached.route(ORIGIN, DESTINATION)
    assert inner.route_calls == 2
    assert result.source is Source.osrm


async def test_close_propagates_to_the_inner_provider() -> None:
    cached, _, _ = build()
    await cached.close()  # must not raise
