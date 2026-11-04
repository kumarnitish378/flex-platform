"""Turning a scored candidate into something a supervisor can read (B23).

`allocation-rules.md` §5: "Each suggestion lists: ETA to pickup, seats free after
assignment, added minutes per existing rider, empty km added, whether it opens a new
trip, and cost. Shown as plain text, e.g. *8 min away · 2 seats left · +4 min for Rahul
· reuses trip T-102*."

Pure, and separate from the cost function on purpose. The number decides the order; the
sentence decides whether a human agrees with it. A supervisor who cannot see *why* the
system picked a cab will either approve everything without reading - which makes the
Phase 2 acceptance metric meaningless - or reject everything and go back to the phone.

**Cost is deliberately not in the sentence.** It is a minutes-equivalent score with four
weighted terms; shown next to "8 min away" it invites the reading "this ride costs 13.8
of something", which is wrong and unfixable once believed. It travels in its own field
for the ranking and for reports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

#: `allocation-rules.md` §5 renders these separated by a middle dot.
SEPARATOR = " · "


@dataclass(frozen=True, slots=True)
class RiderImpact:
    """One rider already on the trip, and what this insertion costs them."""

    name: str
    added_minutes: float


@dataclass(frozen=True, slots=True)
class SuggestionFacts:
    """Everything §5 says a suggestion must show."""

    eta_to_pickup_seconds: float
    seats_free_after: int
    empty_km_added: float
    new_trip: bool
    #: Existing riders, in the order they should be read. Empty for a new trip.
    riders: Sequence[RiderImpact] = ()
    #: How the trip is identified to a human. The caller decides the format; the domain
    #: must not invent one, because `trip.id` is a UUID and "T-102" is the operator's
    #: language, not ours.
    trip_label: str | None = None
    #: True when the ETA is a straight-line estimate rather than road routing
    #: (ADR-0010). A supervisor comparing two cabs is comparing two claims, and an
    #: approximate one is a weaker claim.
    eta_approximate: bool = False


def minutes(seconds: float) -> int:
    """Whole minutes, rounded to nearest. `8 min away`, never `7.6 min away`.

    Rounding rather than truncating: a 7.6-minute ETA shown as 7 reads as a promise the
    cab will beat, and the rider is the one who finds out it did not.
    """
    return int(round(seconds / 60.0))


def reasons(facts: SuggestionFacts) -> list[str]:
    """The §5 phrases, in the order §5 lists them.

    Returned as a list rather than a joined string so a screen can lay them out however
    it likes - chips, lines, a table - without parsing a sentence apart again.
    """
    parts: list[str] = []

    away = f"{minutes(facts.eta_to_pickup_seconds)} min away"
    if facts.eta_approximate:
        away += " (approx)"
    parts.append(away)

    parts.append(_seats(facts.seats_free_after))

    for rider in facts.riders:
        parts.append(f"+{minutes(rider.added_minutes * 60)} min for {rider.name}")

    # Only when there is some: "0 km empty" on every suggestion is noise that trains
    # people to stop reading the line.
    if facts.empty_km_added > 0:
        parts.append(f"{facts.empty_km_added:.1f} km empty")

    parts.append("new trip" if facts.new_trip else _reuse(facts.trip_label))
    return parts


def sentence(facts: SuggestionFacts) -> str:
    """The §5 one-liner."""
    return SEPARATOR.join(reasons(facts))


def _seats(free: int) -> str:
    if free <= 0:
        return "full after this"
    return "1 seat left" if free == 1 else f"{free} seats left"


def _reuse(trip_label: str | None) -> str:
    return f"reuses trip {trip_label}" if trip_label else "reuses a trip already running"


def named_riders(added_minutes: Mapping[str, float], names: Mapping[str, str]) -> list[RiderImpact]:
    """Pair each affected rider's detour with their name, worst affected first.

    Worst first because that is the one a supervisor has to justify. A list led by
    "+1 min for Asha" buries the "+14 min for Rahul" that is the actual decision.
    Riders whose name is unknown are dropped rather than rendered as an id - "+4 min for
    8f3c-..." tells a human nothing and costs them a line.
    """
    impacts = [
        RiderImpact(name=names[key], added_minutes=value)
        for key, value in added_minutes.items()
        if key in names
    ]
    return sorted(impacts, key=lambda impact: (-impact.added_minutes, impact.name))
