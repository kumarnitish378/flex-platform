"""Redis cache in front of any routing provider (ADR-0010 rule 2).

Caching is what makes a 1 request/second budget usable: a dispatch screen asking for the
same pickup's ETA from twenty supervisors costs one upstream request.

Only exact, non-approximate answers are cached. Caching an `approx` result would freeze a
degraded answer in place for the whole TTL, long after OSRM recovered.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.core.redis import RedisLike
from app.domain.geo import LatLng
from app.modules.routing.types import RouteResult, RoutingProvider, Source, TableResult

logger = get_logger(__name__)

KEY_PREFIX = "route"
# 4 decimal places is about 11 m: precise enough for an ETA, coarse enough that a
# pin nudged by a few metres still hits the same cache entry.
COORD_DECIMALS = 4


class CachedRoutingProvider:
    """Wraps another provider; serves repeats from Redis."""

    name = "cached"

    def __init__(
        self,
        inner: RoutingProvider,
        redis: RedisLike,
        *,
        ttl_seconds: int = 900,
    ) -> None:
        self._inner = inner
        self._redis = redis
        self._ttl = ttl_seconds

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        key = self._route_key(origin, destination)
        cached = await self._read(key)
        if cached is not None:
            return RouteResult(
                duration_seconds=cached["duration_seconds"],
                distance_meters=cached["distance_meters"],
                source=Source.cache,
                approximate=False,
                geometry=tuple(LatLng(lat=p[0], lng=p[1]) for p in cached.get("geometry", [])),
            )

        result = await self._inner.route(origin, destination)
        if not result.approximate:
            await self._write(
                key,
                {
                    "duration_seconds": result.duration_seconds,
                    "distance_meters": result.distance_meters,
                    "geometry": [[p.lat, p.lng] for p in result.geometry],
                },
            )
        return result

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        key = self._table_key(origins, destinations)
        cached = await self._read(key)
        if cached is not None:
            return TableResult(
                durations=tuple(tuple(row) for row in cached["durations"]),
                distances=tuple(tuple(row) for row in cached["distances"]),
                source=Source.cache,
                approximate=False,
            )

        result = await self._inner.table(origins, destinations)
        if not result.approximate:
            await self._write(
                key,
                {
                    "durations": [list(row) for row in result.durations],
                    "distances": [list(row) for row in result.distances],
                },
            )
        return result

    async def close(self) -> None:
        await self._inner.close()

    # --- redis plumbing -----------------------------------------------------

    async def _read(self, key: str) -> dict[str, Any] | None:
        if self._ttl <= 0:
            return None
        try:
            raw = await self._redis.get(key)
        except Exception as exc:  # noqa: BLE001 - a cache miss is always survivable
            logger.warning("route_cache_read_failed", error=type(exc).__name__)
            return None
        if raw is None:
            return None
        try:
            payload: dict[str, Any] = json.loads(raw)
            return payload
        except (TypeError, ValueError):
            return None

    async def _write(self, key: str, payload: dict[str, Any]) -> None:
        if self._ttl <= 0:
            return
        try:
            await self._redis.set(key, json.dumps(payload), ex=self._ttl)
        except Exception as exc:  # noqa: BLE001 - failing to cache is not a request failure
            logger.warning("route_cache_write_failed", error=type(exc).__name__)

    def _route_key(self, origin: LatLng, destination: LatLng) -> str:
        return f"{KEY_PREFIX}:{self._inner.name}:r:{_point(origin)}:{_point(destination)}"

    def _table_key(self, origins: list[LatLng], destinations: list[LatLng]) -> str:
        left = ",".join(_point(p) for p in origins)
        right = ",".join(_point(p) for p in destinations)
        return f"{KEY_PREFIX}:{self._inner.name}:t:{left}|{right}"


def _point(point: LatLng) -> str:
    lat, lng = point.rounded(COORD_DECIMALS)
    return f"{lat},{lng}"
