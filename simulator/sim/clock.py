"""Simulated time (`simulator-spec.md` §3).

The simulator owns time. `SimClock` converts between SimPy's float seconds and real UTC
datetimes, and (once M04 lands) pushes each step to the backend through `PUT /simctl/clock`
so the platform's injected `Clock` agrees with the simulation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


class SimClock:
    """Maps simulated seconds since `start` onto absolute UTC times."""

    def __init__(self, start: datetime, speed_factor: float = 60.0) -> None:
        if start.tzinfo is None:
            raise ValueError("SimClock start must be timezone-aware")
        if speed_factor <= 0:
            raise ValueError("speed_factor must be positive")
        self._start = start.astimezone(UTC)
        self._speed_factor = speed_factor
        self._elapsed = 0.0

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def speed_factor(self) -> float:
        return self._speed_factor

    @property
    def elapsed_seconds(self) -> float:
        return self._elapsed

    def now(self) -> datetime:
        """Current simulated time, timezone-aware UTC."""
        return self._start + timedelta(seconds=self._elapsed)

    def now_ist(self) -> datetime:
        """Same instant in Indian time, for shift windows and human-readable logs."""
        return self.now().astimezone(IST)

    def advance_to(self, elapsed_seconds: float) -> datetime:
        """Move to an absolute offset from the start. Never moves backwards."""
        if elapsed_seconds < self._elapsed:
            raise ValueError("simulated time cannot move backwards")
        self._elapsed = elapsed_seconds
        return self.now()

    def real_seconds_for(self, simulated_seconds: float) -> float:
        """Wall-clock time a stretch of simulated time should take at this speed factor.

        `speed_factor: 1` runs in real time so a human can watch cabs move on the map;
        60 runs an hour a minute.
        """
        return simulated_seconds / self._speed_factor
