"""Time access for the whole backend.

This module is the **only** place allowed to read the system clock
(`coding-standards.md` §2 rule 2). Everything else receives a `Clock` by dependency
injection, which is what lets the simulator drive time through `/simctl/clock`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable


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
