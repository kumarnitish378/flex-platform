"""When a driver's tap is believable (B15, DRV-05, `coding-standards.md` section 5).

The driver app queues taps offline and sends them later, so `occurred_at` comes from a
phone we do not control and arrives at an unpredictable time. Pure, like the GPS rules and
for the same reason: a phone with a wrong clock would otherwise rewrite a trip's history.

The transitions themselves live in `state_machines.py`. This only judges the timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class StopAction(StrEnum):
    """The actions `api-spec.yaml` allows on `/driver/stops/{id}/{action}`."""

    arrived = "arrived"
    done = "done"
    no_show = "no_show"


#: A tap cannot have happened in the future. Two minutes of tolerance for clock skew,
#: matching the GPS rule in `mqtt-topics.md` rather than inventing a second number.
MAX_FUTURE = timedelta(minutes=2)

#: The driver app buffers for 30 minutes of GPS, but a status event can sit in the queue
#: for a whole shift on a bad connection. A day is generous and still rejects nonsense
#: like a phone stuck in 1970.
MAX_AGE = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class BadTimestamp:
    reason: str
    detail: str


def check_occurred_at(occurred_at: datetime, now: datetime) -> BadTimestamp | None:
    """`None` means the timestamp is usable as the business time of the event."""
    if occurred_at.tzinfo is None:
        # Guessing a zone would silently shift the whole trip's timeline.
        return BadTimestamp("naive_timestamp", "occurred_at must carry a timezone")

    ahead = occurred_at - now
    if ahead > MAX_FUTURE:
        return BadTimestamp("future_timestamp", f"ahead by {ahead}")
    if now - occurred_at > MAX_AGE:
        return BadTimestamp("stale_timestamp", f"older than {MAX_AGE}")
    return None


def effective_time(occurred_at: datetime, now: datetime) -> datetime:
    """The time to record.

    A tap a few seconds "in the future" is clock skew, not a lie, so it is pulled back to
    now rather than rejected: refusing would lose a real event over a phone whose clock is
    three seconds fast.
    """
    return min(occurred_at, now)
