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

**A second case (owner decision 2026-11-02):** on a *shared* `from_office` trip, a woman who is the
**last rider left in the cab** - the last drop - also needs an escort, however many people shared
the earlier part of the trip and whether or not they were men. Going home, everybody boards at the
office together and the last drop is the one stretch where one passenger is alone with the driver.
Unlike the first case, a male co-rider cannot clear it: he is gone by then. It is flagged when the
trip is planned (the stops are known), and the start is gated exactly as before.

This is separate from B28's `night_escort_required` rider flag, which polices the **order** of a
shared trip (rule 11) and stays as it was.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import time
from enum import StrEnum

from app.domain.enums import Direction
from app.domain.night_safety import in_night_window

FEMALE = "female"


class EscortReason(StrEnum):
    """Why a trip needs a supervisor's confirmation before it starts."""

    #: She is the only rider in the cab (owner decision 2026-11-01).
    lone_rider = "lone_rider"
    #: She is the last rider left on a shared trip home (owner decision 2026-11-02).
    last_out = "last_out"


class EscortBasis(StrEnum):
    """What the supervisor is attesting when they clear a flagged trip."""

    escort_arranged = "escort_arranged"
    male_co_rider_present = "male_co_rider_present"


def accepted_bases(reason: EscortReason) -> frozenset[EscortBasis]:
    """What can clear each reason. A man sharing the trip home does not help a woman who is
    dropped after he has gone, so only an arranged escort clears `last_out`."""
    if reason is EscortReason.last_out:
        return frozenset({EscortBasis.escort_arranged})
    return frozenset(EscortBasis)


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


def escort_reason(
    *,
    enabled: bool,
    local_time: time,
    night_start: time,
    night_end: time,
    direction: Direction,
    genders_in_drop_order: Sequence[str | None],
) -> EscortReason | None:
    """Why this trip needs an escort confirmation, or `None` if it does not.

    `genders_in_drop_order` is every rider still on the trip, in the order they will be dropped.
    """
    if not enabled or not in_night_window(local_time, night_start, night_end):
        return None
    if len(genders_in_drop_order) == 1 and genders_in_drop_order[0] == FEMALE:
        return EscortReason.lone_rider
    if (
        direction is Direction.from_office
        and len(genders_in_drop_order) >= 2
        and genders_in_drop_order[-1] == FEMALE
    ):
        return EscortReason.last_out
    return None
