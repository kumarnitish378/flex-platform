"""How far a cab really drove on a trip, from its GPS pings (B38, B39).

`trip.actual_distance_m` existed in the data model from the start and nothing wrote it. Two
Phase 3 outputs need it: cab-km per trip in the operator report (B39), and the kilometres on
a client's invoice (B38). Both are claims about what was driven, so this measures what was
driven: the length of the path the pings trace between the trip starting and finishing.

GPS is noisy and the noise is not zero-mean for *length*: a cab standing still at a stop
for five minutes emits a ping every thirty seconds, each a few metres from the last, and
summing those hops credits it with a walk it never took. Two filters, both stated:

* **a hop shorter than `JITTER_METRES` is not movement** (see `path_length_m` for why this
  loses nothing from a moving cab);
* **a hop implying more than `MAX_PLAUSIBLE_KPH` is a bad fix, not a drive,** and is
  skipped rather than counted as a 2 km leap.

Pure: pings in, metres out.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.domain.gps import distance_m

#: Below this a hop is GPS jitter. A receiver with 5 m of noise on each axis puts two fixes of
#: a parked cab up to ~15 m apart, so 25 m clears it. Skipping costs nothing for a moving
#: cab: the distance is measured from an anchor that stays put until the cab has really gone
#: this far, so nothing is lost, only the smallest wiggles are straightened.
JITTER_METRES = 25.0
#: Above this implied speed a hop is a bad fix.
MAX_PLAUSIBLE_KPH = 160.0


@dataclass(frozen=True, slots=True)
class Fix:
    at: datetime
    lat: float
    lng: float


def path_length_m(fixes: Iterable[Fix]) -> float:
    """Metres along the path the fixes trace, in time order, ignoring jitter and bad fixes.

    Measured from an **anchor**, not from the previous fix: a cab stands still and its
    receiver wanders a few metres, so every fix stays inside the jitter radius of the anchor
    and adds nothing; a cab crawling at walking pace moves the anchor each time it has really
    gone `JITTER_METRES`, so a traffic jam is not rounded down to zero hop by hop.
    """
    ordered = sorted(fixes, key=lambda fix: fix.at)
    total = 0.0
    anchor: Fix | None = None
    previous: Fix | None = None
    for fix in ordered:
        if anchor is None or previous is None:
            anchor = previous = fix
            continue
        # Is this fix believable? Judged against the last fix we believed, because the
        # anchor may be minutes old and a 2 km leap from a cab that has been parked for ten
        # minutes would imply a perfectly ordinary speed.
        gap = (fix.at - previous.at).total_seconds()
        step = distance_m(previous.lat, previous.lng, fix.lat, fix.lng)
        if gap <= 0 or step / gap * 3.6 > MAX_PLAUSIBLE_KPH:
            continue
        previous = fix
        hop = distance_m(anchor.lat, anchor.lng, fix.lat, fix.lng)
        if hop >= JITTER_METRES:
            total += hop
            anchor = fix
    return total
