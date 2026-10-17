"""Rule 11: nobody flagged for an escort is left alone at either end of a night trip.

`allocation-rules.md` §2 rule 11, in full: "during night window, a trip's sequence must
not leave a rider flagged `night_escort_required` as first pickup or last drop without
an escort (exact client policy configurable; see OQ-10)".

Three things that sentence does not settle, decided here and visible in the tests:

**Which positions are actually lone ones depends on the direction.** On a `to_office`
trip every rider is dropped at the same office, so the drops happen together and the
only solitary moment is the **first pickup** - from their door until the second rider
gets in. On a `from_office` trip everyone boards at the office together, and the lone
moment is the **last drop**. Checking "first pickup and last drop" on both directions
would flag a rider who is never alone, and a safety rule that cries wolf gets waived
out of habit. Which of the two positions an operator polices is still a config key
(`night_safety_positions`), because OQ-10 is open and a pilot client may want only one.

**A solo trip cannot breach it.** This is a constraint on the *order* of a shared
trip - with one rider aboard there is no order to get wrong, and refusing the ride
would leave them with no cab at all, which is not safer. Whether a flagged rider may
travel alone at night *at all*, and what an escort is in the data model, is exactly
what OQ-10 has to answer; until it does, this rule stays a sequencing rule.

**The window is judged on when the rider is actually collected**, not on when they
asked. A 19:50 booking whose cab arrives at 20:10 is a night ride.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from datetime import time
from enum import StrEnum

from app.domain.enums import Direction


class NightPosition(StrEnum):
    """A place in the sequence where a rider can be the only passenger."""

    first_pickup = "first_pickup"
    last_drop = "last_drop"


#: The `night_safety_positions` config key, as a set each time.
POLICED: dict[str, frozenset[NightPosition]] = {
    "both": frozenset(NightPosition),
    "first_pickup": frozenset({NightPosition.first_pickup}),
    "last_drop": frozenset({NightPosition.last_drop}),
}


def lone_positions(direction: Direction) -> frozenset[NightPosition]:
    """Where a rider is actually alone, given the shape of the trip."""
    if direction is Direction.to_office:
        # Pickups in rider order, then every drop at the one office.
        return frozenset({NightPosition.first_pickup})
    return frozenset({NightPosition.last_drop})


def in_night_window(at: time, start: time, end: time) -> bool:
    """Is this time of day inside the night window?

    The window normally crosses midnight (20:00-06:00), which is the case that gets
    written wrong: a plain `start <= at <= end` is empty for every real night window.
    """
    if start <= end:
        return start <= at <= end
    return at >= start or at <= end


def exposed_riders(
    direction: Direction, order: Sequence[uuid.UUID], positions: str
) -> frozenset[uuid.UUID]:
    """Riders who would be alone in the cab, given this order and this policy."""
    if len(order) < 2:
        return frozenset()

    policed = POLICED.get(positions, POLICED["both"]) & lone_positions(direction)
    exposed: set[uuid.UUID] = set()
    if NightPosition.first_pickup in policed:
        exposed.add(order[0])
    if NightPosition.last_drop in policed:
        exposed.add(order[-1])
    return frozenset(exposed)


def breaches_night_safety(
    *,
    direction: Direction,
    order: Sequence[uuid.UUID],
    flagged: Iterable[uuid.UUID],
    at: time,
    enabled: bool,
    night_start: time,
    night_end: time,
    positions: str = "both",
) -> bool:
    """Would this rider order leave a flagged rider alone during the night window?"""
    if not enabled or not in_night_window(at, night_start, night_end):
        return False
    return bool(exposed_riders(direction, order, positions) & set(flagged))
