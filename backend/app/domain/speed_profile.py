"""Learned speeds: from what the cabs actually did to what `approx` assumes (B37, OQ-22).

`approx` estimates a trip as straight-line distance x a road factor, divided by a speed. The
speed was a guess: a 24 km/h base, a 0.6 peak factor, a free-flowing night (OQ-22), and it
has been the dominant term in every number the simulator has printed. This is the other
half: measure it.

**What is measured is the effective speed in `approx`'s own frame.** For a leg between two
stops that a driver really drove, the speed is

    (great-circle distance x road factor) / (time the driver took)

and it is the same quantity `approx` divides by, so substituting it for the constant needs
no conversion and cannot double-count the road factor. A speed measured along the real road
would be higher than this number and would be wrong to put into a formula that multiplies
distance by 1.4 first.

**Granularity is the hour of the week** (168 slots, `data-model.md`), summed rather than
averaged: a slot's speed is total distance over total time, because that is what a travel
time is. Averaging per-leg speeds would let one short fast leg count as much as a long slow
one.

**Not map-matched.** `road_speed_profile` is keyed by OSM way, and attributing a leg to ways
needs map matching against the routing graph, which `approx` does not have. The aggregate
across the service area lives under `AREA_WAY_ID` (0), per slot; per-way profiles - and the
OSRM `--segment-speed-file` they would feed - are a later step this table already has room
for.

Pure: legs in, statistics out.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

#: Hours in a week: the number of slots.
SLOTS = 168
#: `osm_way_id` of the whole-service-area aggregate (see the module docstring).
AREA_WAY_ID = 0

#: A leg shorter than this carries no information about speed: the cab barely moved, and a
#: few metres over a few seconds is mostly GPS noise and a driver parking.
MIN_LEG_METRES = 200.0
#: Nor does one that took longer than this: the driver stopped for tea.
MAX_LEG_SECONDS = 3 * 3600.0
#: Nor one faster than this effective speed. In `approx`'s frame (straight line x road
#: factor over time) anything above it is a mis-timed stop, not a cab that flew.
MAX_PLAUSIBLE_KPH = 120.0


@dataclass(frozen=True, slots=True)
class Leg:
    """One stretch a driver drove: from the previous stop being done to this one's arrival."""

    started_at: datetime
    ended_at: datetime
    #: Great-circle metres between the two stops times the road factor - `approx`'s frame.
    road_metres: float


@dataclass(frozen=True, slots=True)
class SlotStat:
    """Running totals for one hour-of-week slot."""

    metres: float = 0.0
    seconds: float = 0.0
    samples: int = 0

    def speed_kph(self) -> float | None:
        return None if self.seconds <= 0 else (self.metres / self.seconds) * 3.6


def slot_of(moment: datetime, timezone: str) -> int:
    """Hour of the week, local: Monday 00:00-00:59 is 0, Sunday 23:00-23:59 is 167."""
    local = moment.astimezone(ZoneInfo(timezone))
    return local.weekday() * 24 + local.hour


def usable(leg: Leg) -> bool:
    """Is this leg evidence of a speed, or noise?"""
    seconds = (leg.ended_at - leg.started_at).total_seconds()
    if seconds <= 0 or seconds > MAX_LEG_SECONDS or leg.road_metres < MIN_LEG_METRES:
        return False
    return (leg.road_metres / seconds) * 3.6 <= MAX_PLAUSIBLE_KPH


def accumulate(
    stats: dict[int, SlotStat], legs: Iterable[Leg], timezone: str
) -> dict[int, SlotStat]:
    """Fold legs into the per-slot totals, returning the updated copy.

    A leg is attributed to the slot it **started** in. A leg that straddles an hour boundary
    is a small error either way, and picking the start keeps the rule explainable.
    """
    updated = dict(stats)
    for leg in legs:
        if not usable(leg):
            continue
        slot = slot_of(leg.started_at, timezone)
        before = updated.get(slot, SlotStat())
        updated[slot] = SlotStat(
            metres=before.metres + leg.road_metres,
            seconds=before.seconds + (leg.ended_at - leg.started_at).total_seconds(),
            samples=before.samples + 1,
        )
    return updated


def speeds(stats: dict[int, SlotStat], min_samples: int) -> dict[int, float]:
    """kph per slot, for the slots with enough evidence to trust over the constant."""
    found: dict[int, float] = {}
    for slot, stat in stats.items():
        speed = stat.speed_kph()
        if speed is not None and stat.samples >= min_samples:
            found[slot] = speed
    return found
