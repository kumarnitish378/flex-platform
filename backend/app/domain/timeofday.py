"""Local time of day, for the rules that are written in one.

Everything the platform stores is timezone-aware UTC (`core/clock.py`), and that is
right: a trip that starts at 18:29 UTC starts at one instant everywhere. But several
rules are written in **local clock time** instead, because that is how the people using
them think:

* a mode setting scoped to "18:00-21:00" (`control-model.md` §2),
* the night-safety window, "20:00-06:00" (`allocation-rules.md` §2 rule 11),
* an override expiring "at the end of the shift, 23:59" (`control-model.md` §3 rule 5).

Comparing `moment.time()` against those is wrong by the offset - five and a half hours
for every Indian operator, which turns an evening rule into an afternoon one and a
night window into an afternoon one. It is also the kind of wrong that passes every test
written in UTC, so the conversion lives here and the rules take a local value.
"""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


def local(moment: datetime, timezone: str) -> datetime:
    """The same instant, as the operator's wall clock shows it."""
    return moment.astimezone(ZoneInfo(timezone))


def local_time(moment: datetime, timezone: str) -> time:
    """Local time of day, naive - comparable against a config `HH:MM`.

    Naive on purpose: an aware `time` cannot be compared with a naive one at all
    (Python raises), and a config value parsed from "20:00" is always naive.
    """
    return local(moment, timezone).time()
