"""Stop sequencing and the hard-rule checks (`allocation-rules.md` sections 2-3, B14).

Pure. Takes riders, an office and a `duration` callable; returns an ordering and a list of
violations. No database, no routing client, no clock of its own - the caller supplies a
pre-fetched duration matrix, which is what keeps a candidate list to **one** routing call
instead of one per insertion position (ADR-0010: the shared public server has a 1 req/s
budget).

Trip shape (`data-model.md`, `trip-lifecycle.md`): a trip has one direction and one office,
and every rider contributes two stops.

    to_office    pickup(r1) -> pickup(r2) -> ... -> drop(r1) drop(r2) ... at the office
    from_office  pickup(r1) pickup(r2) ... at the office -> drop(r1) -> drop(r2) -> ...

So adding a rider means choosing **one** insertion position in the rider order, not two.
The drops of a `to_office` trip are separate rows at the same location because each one
completes a different request (a pickup stop going `done` sets `picked_up`, a drop sets
`dropped`), and `trip_stop` is unique on `(trip_id, sequence)`.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.domain.enums import Direction
from app.domain.state_machines import StopKind

#: Travel time in seconds between two points, from a pre-fetched matrix.
Duration = Callable[["Place", "Place"], float]


class Violation(StrEnum):
    """A hard rule this assignment breaks (`allocation-rules.md` section 2).

    Reported, not enforced, for manual assignment in Phase 1 - see ADR-0011. Phase 2's
    optimizer treats the same list as a filter.
    """

    vehicle_unavailable = "vehicle_unavailable"
    gps_stale = "gps_stale"
    locked_to_other_vehicle = "locked_to_other_vehicle"
    pooling_blocked = "pooling_blocked"
    no_sharing = "no_sharing"
    vip_needs_vip_vehicle = "vip_needs_vip_vehicle"
    direction_mismatch = "direction_mismatch"
    office_mismatch = "office_mismatch"
    detour_factor_exceeded = "detour_factor_exceeded"
    detour_minutes_exceeded = "detour_minutes_exceeded"
    pickup_window_missed = "pickup_window_missed"
    eta_over_candidate_limit = "eta_over_candidate_limit"


@dataclass(frozen=True, slots=True)
class Place:
    """A point the vehicle must reach. Hashable, so it can key a duration matrix."""

    lat: float
    lng: float


@dataclass(frozen=True, slots=True)
class Rider:
    """One request's contribution to a trip: the rider's own end of the journey."""

    request_id: uuid.UUID
    place: Place


@dataclass(frozen=True, slots=True)
class PlannedStop:
    sequence: int
    kind: StopKind
    request_id: uuid.UUID
    place: Place


@dataclass(frozen=True, slots=True)
class Plan:
    """A rider order and what it costs."""

    order: tuple[Rider, ...]
    stops: tuple[PlannedStop, ...]
    #: Seconds each rider spends between their pickup and their drop.
    ride_seconds: dict[uuid.UUID, float]
    #: Whole-route driving time, from the first stop to the last.
    total_seconds: float


@dataclass(frozen=True, slots=True)
class Insertion:
    """The chosen position for a new rider, and its effect on the others."""

    plan: Plan
    position: int
    #: Extra minutes each *existing* rider now spends in the cab. Never negative.
    added_minutes: dict[uuid.UUID, float]

    @property
    def worst_added_minutes(self) -> float:
        return max(self.added_minutes.values(), default=0.0)


@dataclass(frozen=True, slots=True)
class DetourLimits:
    """Per-client limits (`allocation-rules.md` section 1). The stricter value wins."""

    max_detour_factor: float
    max_detour_minutes: float


def build_plan(
    direction: Direction, office: Place, riders: Sequence[Rider], duration: Duration
) -> Plan:
    """Lay out the stops for a rider order and measure what each rider rides.

    Sequence numbers start at 1 and are contiguous, which is what `trip_stop` stores.
    """
    if not riders:
        return Plan((), (), {}, 0.0)

    stops: list[PlannedStop] = []
    sequence = 1
    if direction is Direction.to_office:
        for rider in riders:
            stops.append(PlannedStop(sequence, StopKind.pickup, rider.request_id, rider.place))
            sequence += 1
        for rider in riders:
            stops.append(PlannedStop(sequence, StopKind.drop, rider.request_id, office))
            sequence += 1
    else:
        for rider in riders:
            stops.append(PlannedStop(sequence, StopKind.pickup, rider.request_id, office))
            sequence += 1
        for rider in riders:
            stops.append(PlannedStop(sequence, StopKind.drop, rider.request_id, rider.place))
            sequence += 1

    # Cumulative driving time to each stop. Stops at the same place cost nothing extra,
    # which is exactly right for the block of drops at one office.
    elapsed = 0.0
    arrival: list[float] = []
    for index, stop in enumerate(stops):
        if index > 0:
            elapsed += duration(stops[index - 1].place, stop.place)
        arrival.append(elapsed)

    first_at: dict[uuid.UUID, float] = {}
    last_at: dict[uuid.UUID, float] = {}
    for index, stop in enumerate(stops):
        if stop.kind is StopKind.pickup:
            first_at[stop.request_id] = arrival[index]
        else:
            last_at[stop.request_id] = arrival[index]

    ride = {request_id: last_at[request_id] - first_at[request_id] for request_id in first_at}
    return Plan(tuple(riders), tuple(stops), ride, elapsed)


def best_insertion(
    direction: Direction,
    office: Place,
    existing: Sequence[Rider],
    newcomer: Rider,
    duration: Duration,
) -> Insertion:
    """Insert `newcomer` where it adds the least time for the riders already on board.

    "Least added time" is measured on the **existing** riders, because they are the ones
    who did not ask for a detour; whole-route duration only breaks ties. A trip holds at
    most `seat_capacity` riders (12 in the widest vehicle), so trying every position is a
    handful of arithmetic, not a search problem.
    """
    before = build_plan(direction, office, existing, duration)

    best: Insertion | None = None
    for position in range(len(existing) + 1):
        order = [*existing[:position], newcomer, *existing[position:]]
        plan = build_plan(direction, office, order, duration)
        added = {
            rider.request_id: max(
                0.0,
                (plan.ride_seconds[rider.request_id] - before.ride_seconds[rider.request_id])
                / 60.0,
            )
            for rider in existing
        }
        candidate = Insertion(plan, position, added)
        if best is None or _insertion_key(candidate) < _insertion_key(best):
            best = candidate

    # range(len+1) always yields position 0, so a best always exists.
    assert best is not None
    return best


def _insertion_key(insertion: Insertion) -> tuple[float, float]:
    return (sum(insertion.added_minutes.values()), insertion.plan.total_seconds)


@dataclass(frozen=True, slots=True)
class AssignmentFacts:
    """Everything the hard-rule checks need, already loaded by the caller.

    A dataclass rather than ORM objects, so the rules stay pure and a test can state a
    situation in four lines instead of building a database.
    """

    vehicle_id: uuid.UUID
    vehicle_status: str
    vehicle_type: str
    gps_age_seconds: float | None
    stale_gps_seconds: int
    eta_to_pickup_seconds: float
    candidate_max_eta_minutes: int
    pickup_window_minutes: int
    requested_time: datetime
    pickup_at: datetime
    direction: Direction
    office_id: uuid.UUID
    employee_is_vip: bool
    request_no_sharing: bool
    lock_vehicle_id: uuid.UUID | None
    #: None for a brand-new trip.
    trip_direction: Direction | None = None
    trip_office_id: uuid.UUID | None = None
    trip_pooling_blocked: bool = False
    trip_has_other_riders: bool = False


AVAILABLE_FOR_DISPATCH = frozenset({"available", "on_trip"})
VIP_VEHICLE_TYPE = "vip"


def check_hard_rules(
    facts: AssignmentFacts,
    insertion: Insertion | None = None,
    limits: dict[uuid.UUID, DetourLimits] | None = None,
    direct_seconds: dict[uuid.UUID, float] | None = None,
) -> list[Violation]:
    """Every hard rule this assignment breaks, in the order `allocation-rules.md` lists them.

    An empty list means the assignment satisfies section 2. Capacity is deliberately **not**
    here: the caller refuses on capacity (ADR-0011), so it can never be quietly reported
    and then ignored.
    """
    violations: list[Violation] = []

    # 1. Vehicle state and fresh GPS.
    if facts.vehicle_status not in AVAILABLE_FOR_DISPATCH:
        violations.append(Violation.vehicle_unavailable)
    if facts.gps_age_seconds is None or facts.gps_age_seconds > facts.stale_gps_seconds:
        violations.append(Violation.gps_stale)

    # 3. Locks.
    if facts.lock_vehicle_id is not None and facts.lock_vehicle_id != facts.vehicle_id:
        violations.append(Violation.locked_to_other_vehicle)
    if facts.trip_pooling_blocked and facts.trip_has_other_riders:
        violations.append(Violation.pooling_blocked)

    # 4. VIP: a VIP vehicle, and the trip is theirs alone.
    if facts.employee_is_vip:
        if facts.vehicle_type != VIP_VEHICLE_TYPE:
            violations.append(Violation.vip_needs_vip_vehicle)
        if facts.trip_has_other_riders:
            violations.append(Violation.no_sharing)

    # 6. Direction and office compatibility.
    if facts.trip_direction is not None and facts.trip_direction is not facts.direction:
        violations.append(Violation.direction_mismatch)
    if facts.trip_office_id is not None and facts.trip_office_id != facts.office_id:
        violations.append(Violation.office_mismatch)

    # 7. Detour limits, for every rider on the resulting trip.
    if insertion is not None:
        violations.extend(_detour_violations(insertion, limits or {}, direct_seconds or {}))

    # 8. Time window.
    drift = abs((facts.pickup_at - facts.requested_time).total_seconds())
    if drift > facts.pickup_window_minutes * 60:
        violations.append(Violation.pickup_window_missed)

    # 9. Opt-out of sharing.
    if (
        facts.request_no_sharing
        and facts.trip_has_other_riders
        and Violation.no_sharing not in violations
    ):
        violations.append(Violation.no_sharing)

    # Section 3: the candidate ETA ceiling.
    if facts.eta_to_pickup_seconds > facts.candidate_max_eta_minutes * 60:
        violations.append(Violation.eta_over_candidate_limit)

    return violations


def _detour_violations(
    insertion: Insertion,
    limits: dict[uuid.UUID, DetourLimits],
    direct_seconds: dict[uuid.UUID, float],
) -> list[Violation]:
    """`ride <= min(direct x factor, direct + minutes)` for every rider on the trip."""
    found: list[Violation] = []
    for request_id, ride in insertion.plan.ride_seconds.items():
        limit = limits.get(request_id)
        direct = direct_seconds.get(request_id)
        if limit is None or direct is None:
            continue
        over_factor = ride > direct * limit.max_detour_factor
        over_minutes = ride > direct + limit.max_detour_minutes * 60
        if over_factor and Violation.detour_factor_exceeded not in found:
            found.append(Violation.detour_factor_exceeded)
        if over_minutes and Violation.detour_minutes_exceeded not in found:
            found.append(Violation.detour_minutes_exceeded)
    return found


def stricter(first: DetourLimits, second: DetourLimits) -> DetourLimits:
    """The tighter of two clients' limits (`allocation-rules.md` section 2, rule 7)."""
    return DetourLimits(
        max_detour_factor=min(first.max_detour_factor, second.max_detour_factor),
        max_detour_minutes=min(first.max_detour_minutes, second.max_detour_minutes),
    )


def pickup_time(now: datetime, eta_seconds: float) -> datetime:
    return now + timedelta(seconds=eta_seconds)
