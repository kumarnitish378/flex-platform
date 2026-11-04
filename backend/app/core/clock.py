"""Time access for the whole backend.

This module is the **only** place allowed to read the system clock
(`coding-standards.md` §2 rule 2). Everything else receives a `Clock` by dependency
injection, which is what lets the simulator drive time through `/simctl/clock`.
"""

from __future__ import annotations

import contextlib
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Source of the current time, always timezone-aware UTC."""

    def now(self) -> datetime: ...


class SystemClock:
    """Real time. Used in dev, staging and prod."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FakeClock:
    """Controllable time for tests and for `APP_ENV=sim`.

    The simulator owns time and steps it forward; tests advance it to make scheduled
    work (expiry, failsafe, ETA refresh) fire deterministically.
    """

    def __init__(self, start: datetime) -> None:
        self._now = _require_utc(start)

    def now(self) -> datetime:
        return self._now

    def set(self, moment: datetime) -> None:
        """Jump to an absolute moment. Moving backwards is allowed (scenario reset)."""
        self._now = _require_utc(moment)

    def advance(self, delta: timedelta) -> datetime:
        """Move forward by `delta` and return the new time."""
        if delta < timedelta(0):
            raise ValueError("advance() moves forward; use set() to go back")
        self._now = self._now + delta
        return self._now


def _require_utc(moment: datetime) -> datetime:
    """Reject naive datetimes early: a naive time here would silently mean 'local'."""
    if moment.tzinfo is None:
        raise ValueError("Clock times must be timezone-aware UTC")
    return moment.astimezone(UTC)


#: Where the simulated clock is shared between processes.
SIM_CLOCK_KEY = "sim:clock"


class SharedSimClock:
    """The simulated clock, read from Redis, for processes that are not the API.

    The API owns simulated time and `/simctl/clock` moves it. The ingestor is a separate
    process (ADR-0005), so without this it validates simulated pings against real wall
    time and rejects every one of them as hours in the future - a failure that looks
    exactly like "MQTT is broken" and is not.

    Falls back to real time whenever the key is missing or unreadable: a sim run that has
    not set the clock yet must not stall the ingestor.

    `now()` stays synchronous because `Clock` is, and reading Redis is not: the caller
    `await`s `refresh()` on its own loop (the ingestor does it each flush) and `now()`
    serves the last value read. A clock the simulator steps in jumps does not need
    sub-second freshness.
    """

    def __init__(
        self,
        redis: Any,
        fallback: Clock | None = None,
        min_interval_seconds: float = 0.25,
    ) -> None:
        self._redis = redis
        self._fallback = fallback or SystemClock()
        self._cached: datetime | None = None
        #: Rate limit on Redis reads. Callers may refresh per message; a simulated hour
        #: arrives in milliseconds, so the clock must keep up without a round trip per
        #: ping.
        self._min_interval = min_interval_seconds
        self._last_read = 0.0

    def now(self) -> datetime:
        return self._cached or self._fallback.now()

    async def refresh(self, force: bool = False) -> datetime:
        """Re-read the shared time. Never raises: a clock read cannot fell the process."""
        elapsed = time.monotonic() - self._last_read
        if not force and self._cached is not None and elapsed < self._min_interval:
            return self.now()
        self._last_read = time.monotonic()

        try:
            raw = await self._redis.get(SIM_CLOCK_KEY)
        except Exception:  # noqa: BLE001
            return self.now()
        if raw is None:
            return self.now()

        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        # A malformed value keeps the previous time rather than lurching to wall clock.
        with contextlib.suppress(ValueError):
            self._cached = _require_utc(datetime.fromisoformat(text))
        return self.now()
