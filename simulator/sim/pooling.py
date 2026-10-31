"""Pooling metrics: what Phase 3's exit criterion is stated in (M11, `phase-3-tasks.md`).

> cab-km per trip and vehicles used reduced vs baseline; median wait reduced.

**Everything here is computed from the trips the drivers actually drove**, never from what
dispatch intended. A plan that pooled three riders and a trip that three riders actually
boarded are different facts, and only the second is a result. So the inputs are the
drivers' own logs (`TripLog`): the distance the cab *moved* between the moment the driver
started the trip and the moment they finished it, the moments each rider got in and out,
and nothing else.

Pure: logs in, numbers out, so a manual run and a pooled run over the same seed are
comparable and the computation has tests that do not need a backend.

**Not measured is `None`, never zero** - the same rule as `DemandMetrics`. A run with no
platform has not driven zero kilometres; it has not driven.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

from sim.agents.driver import TripLog
from sim.geo import LatLng
from sim.stats import percentile

#: Direct ride time between two points at a moment, in minutes. Supplied by the caller so
#: this module needs no routing client of its own.
DirectMinutes = Callable[[LatLng, LatLng, datetime], float]


@dataclass
class PoolingMetrics:
    #: Trips a driver started and that carried at least one rider.
    trips_driven: int | None = None
    #: Distinct cabs that drove at least one such trip.
    vehicles_used: int | None = None
    riders_carried: int | None = None
    riders_per_trip: float | None = None
    #: Trips that carried two or more riders at once, and their share of all trips driven.
    pooled_trips: int | None = None
    pooling_rate: float | None = None
    #: Kilometres the cabs moved between starting and finishing those trips.
    cab_km_total: float | None = None
    cab_km_per_trip: float | None = None
    cab_km_per_rider: float | None = None
    #: Minutes beyond a direct ride, per rider who was carried end to end.
    rides_measured: int | None = None
    detour_minutes_median: float | None = None
    detour_minutes_p90: float | None = None
    detour_minutes_mean: float | None = None
    #: Riders whose ride exceeded `allocation-rules.md` section 2 rule 7's limit. S10
    #: asserts this is zero.
    detour_over_limit: int | None = None
    #: S11. Flagged riders who were carried, and how many of those were left alone in
    #: the lone position of a pooled trip. `None` when nobody was flagged.
    night_flagged_carried: int | None = None
    night_safety_violations: int | None = None


def pooling_metrics(
    logs: Iterable[TripLog],
    direct_minutes: DirectMinutes,
    *,
    max_detour_factor: float = 1.5,
    max_detour_minutes: float = 15.0,
    night_escort_riders: frozenset[str] = frozenset(),
) -> PoolingMetrics:
    """Compute the metrics from the drivers' trip logs.

    Trips that carried nobody are left out: a cab that drove to a pickup and was refused a
    rider (a no-show) did no pooling work, and counting its kilometres would punish a
    policy for a rider who never came.
    """
    carried = [log for log in logs if _boarded(log)]
    if not carried:
        return PoolingMetrics()

    km = [_cab_km(log) for log in carried]
    riders = [len(_boarded(log)) for log in carried]
    detours: list[float] = []
    over = 0
    for log in carried:
        for ride in log.rides.values():
            if None in (
                ride.picked_up_at,
                ride.dropped_at,
                ride.picked_up_at_place,
                ride.dropped_at_place,
            ):
                continue
            assert ride.picked_up_at and ride.dropped_at
            assert ride.picked_up_at_place and ride.dropped_at_place
            actual = (ride.dropped_at - ride.picked_up_at).total_seconds() / 60.0
            direct = direct_minutes(
                ride.picked_up_at_place, ride.dropped_at_place, ride.picked_up_at
            )
            detours.append(max(actual - direct, 0.0))
            if actual > min(direct * max_detour_factor, direct + max_detour_minutes) + 1e-9:
                over += 1

    total_riders = sum(riders)
    pooled = sum(1 for count in riders if count >= 2)
    flagged_carried, night_violations = _night_safety(carried, night_escort_riders)
    return PoolingMetrics(
        trips_driven=len(carried),
        vehicles_used=len({log.vehicle_id for log in carried}),
        riders_carried=total_riders,
        riders_per_trip=_round(total_riders / len(carried)),
        pooled_trips=pooled,
        pooling_rate=_round(pooled / len(carried), 3),
        cab_km_total=_round(sum(km), 3),
        cab_km_per_trip=_round(sum(km) / len(carried), 3),
        cab_km_per_rider=_round(sum(km) / total_riders, 3),
        rides_measured=len(detours),
        detour_minutes_median=_round(percentile(detours, 0.5)),
        detour_minutes_p90=_round(percentile(detours, 0.9)),
        detour_minutes_mean=_round(sum(detours) / len(detours)) if detours else None,
        detour_over_limit=over,
        night_flagged_carried=flagged_carried,
        night_safety_violations=night_violations,
    )


def _night_safety(logs: list[TripLog], flagged: frozenset[str]) -> tuple[int | None, int | None]:
    """Rule 11, judged on what was driven: a flagged rider alone in the lone position.

    Going to the office the lone position is the first pickup (everybody is dropped
    together at the office); coming home it is the last drop. A solo trip can never
    breach it - there is no one to be alone *with* - so only pooled trips count.
    """
    if not flagged:
        return None, None
    carried = 0
    violations = 0
    for log in logs:
        boarded = {rid: ride for rid, ride in log.rides.items() if ride.picked_up_at}
        carried += sum(1 for rid in boarded if rid in flagged)
        if len(boarded) < 2:
            continue
        if log.direction == "from_office":
            dropped = [(ride.dropped_at, rid) for rid, ride in boarded.items() if ride.dropped_at]
            lone = max(dropped)[1] if dropped else None
        else:
            lone = min(
                (ride.picked_up_at, rid) for rid, ride in boarded.items() if ride.picked_up_at
            )[1]
        if lone is not None and lone in flagged:
            violations += 1
    return carried, violations


def _boarded(log: TripLog) -> list[str]:
    """Riders who actually got in: a completed pickup, not a stop that was listed."""
    return [rid for rid, ride in log.rides.items() if ride.picked_up_at is not None]


def _cab_km(log: TripLog) -> float:
    if log.odometer_end_km is None:
        return 0.0
    return max(log.odometer_end_km - log.odometer_start_km, 0.0)


def _round(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)
