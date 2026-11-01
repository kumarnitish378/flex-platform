"""The night escort rule (owner decision 3, 2026-11-01; OQ-10).

After the night window opens (20:00), a woman who would be **the only rider in the cab** needs an
escort. If a man on the same route shares the cab, she does not. The platform does not arrange
escorts and does not decide who the escort is: it **flags** the trip and the supervisor has to
confirm - before the trip can start - that an escort is arranged or that a male co-rider is present.

Deliberately narrow, and each narrowing is the owner's wording rather than a guess:

* *Only rider*: exactly one active rider on the trip. Two women together are not alone.
* *Female*: the `gender` of the rider. An unknown gender never triggers it - a rule that guesses
  from a name would flag the wrong people - so riders must have it recorded.
* *Night*: the client's own `night_safety` window and switch (B28), judged when the trip would
  start, in the operator's local time.

This is separate from B28's `night_escort_required` rider flag, which polices the **order** of a
shared trip (rule 11) and stays as it was.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import time
from enum import StrEnum

from app.domain.night_safety import in_night_window

FEMALE = "female"


class EscortBasis(StrEnum):
    """What the supervisor is attesting when they clear a flagged trip."""

    escort_arranged = "escort_arranged"
    male_co_rider_present = "male_co_rider_present"


def escort_required(
    *,
    enabled: bool,
    local_time: time,
    night_start: time,
    night_end: time,
    genders: Sequence[str | None],
) -> bool:
    """Would a woman be the only rider in the cab during the night window?"""
    if not enabled or not in_night_window(local_time, night_start, night_end):
        return False
    return len(genders) == 1 and genders[0] == FEMALE
