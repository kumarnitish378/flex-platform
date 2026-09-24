"""The shared 1 request/second budget for public OSM servers (ADR-0010 rule 3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.clock import FakeClock
from app.modules.routing.rate_limit import (
    RedisRateLimiter,
    UnlimitedRateLimiter,
)
from tests.fakes import FakeRedis

START = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)


async def test_first_request_is_allowed() -> None:
    limiter = RedisRateLimiter(FakeRedis(FakeClock(START)))
    assert await limiter.try_acquire("osrm") is True


async def test_second_request_in_the_same_second_is_refused() -> None:
    limiter = RedisRateLimiter(FakeRedis(FakeClock(START)))
    assert await limiter.try_acquire("osrm") is True
    assert await limiter.try_acquire("osrm") is False


async def test_budget_refills_after_the_interval() -> None:
    clock = FakeClock(START)
    limiter = RedisRateLimiter(FakeRedis(clock))

    assert await limiter.try_acquire("osrm") is True
    clock.advance(timedelta(milliseconds=999))
    assert await limiter.try_acquire("osrm") is False
    clock.advance(timedelta(milliseconds=1))
    assert await limiter.try_acquire("osrm") is True


async def test_two_processes_sharing_redis_cannot_exceed_one_per_second() -> None:
    """I02 acceptance: the budget is per service, not per process.

    One FakeRedis instance is one Redis server; two limiters over it are two processes.
    """
    clock = FakeClock(START)
    redis = FakeRedis(clock)
    api_worker = RedisRateLimiter(redis)
    celery_worker = RedisRateLimiter(redis)

    granted = 0
    for _ in range(10):
        if await api_worker.try_acquire("osrm"):
            granted += 1
        if await celery_worker.try_acquire("osrm"):
            granted += 1
    assert granted == 1, "ten attempts from two processes inside one second"

    clock.advance(timedelta(seconds=1))
    assert await celery_worker.try_acquire("osrm") is True
    assert await api_worker.try_acquire("osrm") is False


async def test_ten_seconds_of_traffic_yields_ten_requests() -> None:
    clock = FakeClock(START)
    redis = FakeRedis(clock)
    limiters = [RedisRateLimiter(redis) for _ in range(4)]

    granted = 0
    for _ in range(10):
        for limiter in limiters:
            for _attempt in range(5):
                if await limiter.try_acquire("osrm"):
                    granted += 1
        clock.advance(timedelta(seconds=1))
    assert granted == 10


async def test_budgets_are_independent_per_service() -> None:
    redis = FakeRedis(FakeClock(START))
    limiter = RedisRateLimiter(redis)
    assert await limiter.try_acquire("osrm") is True
    assert await limiter.try_acquire("tiles") is True
    assert await limiter.try_acquire("osrm") is False


async def test_a_higher_rate_shortens_the_interval() -> None:
    clock = FakeClock(START)
    limiter = RedisRateLimiter(FakeRedis(clock), requests_per_second=4.0)

    assert await limiter.try_acquire("osrm") is True
    clock.advance(timedelta(milliseconds=250))
    assert await limiter.try_acquire("osrm") is True


async def test_redis_failure_denies_rather_than_allows() -> None:
    """If we cannot account for our rate, we must not spend donated capacity."""
    redis = FakeRedis(FakeClock(START), fail_on={"set"})
    limiter = RedisRateLimiter(redis)
    assert await limiter.try_acquire("osrm") is False


async def test_unlimited_limiter_always_allows() -> None:
    limiter = UnlimitedRateLimiter()
    for _ in range(100):
        assert await limiter.try_acquire("osrm") is True
