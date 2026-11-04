"""Per-cab-per-day billing (owner decision 2026-11-02; OQ-03).

The employer company pays **per cab per day on the total running km between duty start (cab in)
and duty end (cab out), including the dead km between trips**, at the operator's rate per km
(Rs 8 to begin with). Riders never pay.

So the unit of an invoice is a cab's day, not a trip and not a ride. A day's kilometres come from
the cab's GPS pings between going on and off duty. The driver may also enter the dashboard
odometer when going on and off duty; it is a cross-check and, only when an operator says so for
that day, the figure billed:

* **GPS km** is what the cab moved, measured from pings with jitter and bad fixes ignored.
* **Odometer km** is closing minus opening, present only when both were entered and the closing
  one is not lower.
* **Billed km** is the GPS figure, unless the operator marked that session's odometer figure.
* A **gap** between the two beyond the configured share of the odometer figure (default 10%)
  flags the row. The platform never decides which of the two is right.

Pure: facts in, a row out.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.domain.errors import ValidationFailed


class Basis(StrEnum):
    gps = "gps"
    odometer = "odometer"


class Flag(StrEnum):
    #: GPS and odometer disagree by more than the threshold.
    odometer_gap = "odometer_gap"
    #: The cab served more than one client that day; billed to the operator's default client.
    multiple_clients = "multiple_clients"
    #: No client could be worked out (no trips that day); billed to the default client.
    no_client_trips = "no_client_trips"
    #: No default client is configured and the operator has several; the first was used.
    default_client_unset = "default_client_unset"
    #: A session has not ended yet; its kilometres are so far.
    still_on_duty = "still_on_duty"
    #: Not one session produced a GPS figure (no pings): nothing to bill on GPS.
    no_gps = "no_gps"
    #: An operator chose the odometer figure for at least one session.
    odometer_billed = "odometer_billed"


@dataclass(frozen=True, slots=True)
class SessionFacts:
    session_id: str
    driver: str
    started_at: datetime
    ended_at: datetime | None
    gps_km: float | None
    odometer_start_km: float | None
    odometer_end_km: float | None
    basis: Basis = Basis.gps

    @property
    def odometer_km(self) -> float | None:
        return odometer_km(self.odometer_start_km, self.odometer_end_km)

    @property
    def billed_km(self) -> float:
        """What this session adds to the invoice."""
        if self.basis is Basis.odometer and self.odometer_km is not None:
            return self.odometer_km
        return self.gps_km or 0.0


@dataclass(frozen=True, slots=True)
class CabDay:
    """One cab, one day: the row on an invoice."""

    vehicle: str
    day: str
    drivers: tuple[str, ...]
    duty_in: datetime
    duty_out: datetime | None
    gps_km: float | None
    odometer_km: float | None
    billed_km: float
    amount: float | None
    gap_percent: float | None
    flags: tuple[Flag, ...] = ()
    sessions: tuple[SessionFacts, ...] = field(default=())


def odometer_km(start: float | None, end: float | None) -> float | None:
    """Closing minus opening, or `None` when either is missing or the closing is lower."""
    if start is None or end is None or end < start:
        return None
    return end - start


def check_odometer_reading(opening: float | None, closing: float | None) -> None:
    """A closing reading below the opening one is a typo, caught while the driver can fix it."""
    if opening is not None and closing is not None and closing < opening:
        raise ValidationFailed(
            "The closing odometer reading is lower than the opening one",
            {"opening_km": opening, "closing_km": closing},
        )


def gap_percent(gps_km: float | None, odo_km: float | None) -> float | None:
    """How far GPS is from the odometer, as a percentage of the odometer figure."""
    if gps_km is None or odo_km is None or odo_km <= 0:
        return None
    return abs(odo_km - gps_km) / odo_km * 100.0


def build_cab_day(
    *,
    vehicle: str,
    day: str,
    sessions: Sequence[SessionFacts],
    threshold_percent: float,
    rate_per_km: float | None,
    extra_flags: Sequence[Flag] = (),
) -> CabDay:
    """One cab's sessions for one day, summed into the invoice row."""
    ordered = sorted(sessions, key=lambda s: s.started_at)
    gps_values = [s.gps_km for s in ordered if s.gps_km is not None]
    odo_values = [s.odometer_km for s in ordered if s.odometer_km is not None]
    gps_total = sum(gps_values) if gps_values else None
    odo_total = sum(odo_values) if odo_values else None
    billed = sum(s.billed_km for s in ordered)

    # Compare like with like: the sessions that have both figures.
    both = [(s.gps_km, s.odometer_km) for s in ordered if s.gps_km is not None and s.odometer_km]
    gap = gap_percent(sum(g for g, _ in both), sum(o for _, o in both)) if both else None

    flags: list[Flag] = list(extra_flags)
    if gap is not None and gap > threshold_percent:
        flags.append(Flag.odometer_gap)
    if any(s.ended_at is None for s in ordered):
        flags.append(Flag.still_on_duty)
    if not gps_values:
        flags.append(Flag.no_gps)
    if any(s.basis is Basis.odometer and s.odometer_km is not None for s in ordered):
        flags.append(Flag.odometer_billed)

    ended = [s.ended_at for s in ordered if s.ended_at is not None]
    return CabDay(
        vehicle=vehicle,
        day=day,
        drivers=tuple(dict.fromkeys(s.driver for s in ordered)),
        duty_in=ordered[0].started_at,
        duty_out=None if any(s.ended_at is None for s in ordered) else max(ended),
        gps_km=gps_total,
        odometer_km=odo_total,
        billed_km=billed,
        amount=round(billed * rate_per_km, 2) if rate_per_km else None,
        gap_percent=gap,
        flags=tuple(dict.fromkeys(flags)),
        sessions=tuple(ordered),
    )
