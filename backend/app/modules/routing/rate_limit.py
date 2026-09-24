"""Shared rate limit for public OSM services (ADR-0010 rule 3).

The budget is per *service*, not per process: API workers, Celery workers and beat all
draw from one Redis key, so adding processes cannot multiply the load we put on donated
infrastructure.

Implementation: `SET <key> 1 NX PX <interval>`. With a budget of one request per
interval this is exactly a token bucket of capacity 1 refilling once per interval, in a
single atomic round trip — whoever wins the SET holds the only token for that interval.
`capacity > 1` would need a Lua script; we do not need it, and must not want it, for
public servers.

A caller that cannot get a token is never queued or blocked: it falls back to `approx`
and flags the result approximate. Waiting would turn a rate limit into latency for a
supervisor staring at a dispatch screen.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.logging import get_logger
from app.core.redis import RedisLike

logger = get_logger(__name__)

KEY_PREFIX = "osm:ratelimit"


@runtime_checkable
class RateLimiter(Protocol):
    async def try_acquire(self, service: str) -> bool:
        """True if this caller may make one request to `service` right now."""
        ...


class RedisRateLimiter:
    """Cross-process limiter backed by Redis."""

    def __init__(self, redis: RedisLike, requests_per_second: float = 1.0) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self._redis = redis
        self._interval_ms = max(1, int(1000.0 / requests_per_second))

    async def try_acquire(self, service: str) -> bool:
        key = f"{KEY_PREFIX}:{service}"
        try:
            acquired = await self._redis.set(key, "1", nx=True, px=self._interval_ms)
        except Exception as exc:  # noqa: BLE001 - Redis down must not call public servers
            # Failing closed is deliberate: if we cannot account for our request rate,
            # we must not spend someone else's donated capacity.
            logger.warning("rate_limiter_unavailable", service=service, error=type(exc).__name__)
            return False
        return bool(acquired)


class UnlimitedRateLimiter:
    """No limiting. Only for a self-hosted OSRM, or tests."""

    async def try_acquire(self, service: str) -> bool:
        return True
