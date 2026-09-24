"""Redis client factory.

`from_url` does not connect eagerly, so building the client is safe even when Redis is
down; the failure surfaces at the first command, where the routing cache and rate limiter
already handle it.
"""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Protocol, runtime_checkable

from redis.asyncio import Redis

from app.core.health import CheckFn, CheckResult, Status
from app.core.settings import Settings


@runtime_checkable
class RedisLike(Protocol):
    """The slice of Redis this codebase uses.

    Declared as returning `Awaitable` rather than with `async def`, so both the real
    `redis.asyncio.Redis` (which returns an Awaitable) and plain `async def` fakes in
    tests satisfy it.
    """

    def get(self, name: str) -> Awaitable[Any]: ...

    def set(
        self,
        name: str,
        value: str,
        *,
        nx: bool = ...,
        px: int | None = ...,
        ex: int | None = ...,
    ) -> Awaitable[Any]: ...


def create_redis(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,  # the cache stores JSON strings
        socket_connect_timeout=2.0,
        socket_timeout=2.0,
    )


def redis_check(redis: Any) -> CheckFn:
    """Readiness check for Redis.

    Optional for now: losing Redis costs the routing cache and the shared rate limit
    (both degrade to `approx`), not the ability to serve requests. Tasks B12/B13 should
    promote this to required once live tracking and WebSocket fan-out depend on it.
    """

    async def check() -> CheckResult:
        await redis.ping()
        return CheckResult(Status.ok)

    return check
