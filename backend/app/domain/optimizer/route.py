"""One vehicle's route: its times, its violations, and its cost (`allocation-rules.md` §2, §4).

This is the **single evaluator** under both solvers. The greedy search calls it for every
insertion it tries; the DARP's answer is judged by it afterwards, so a plan the OR-Tools
model got subtly wrong still cannot be applied. The hard rules are enforced twice on
purpose - once as constraints inside the model, so the solver searches only legal space,
and once here on the result - and the second pass is the one that carries the guarantee.

It reuses `check_hard_rules` rather than restating §2, so manual assignment, semi-auto
suggestions and the optimizer cannot drift apart on what a rule means.

**Cost.** `allocation-rules.md` §4 prices one insertion. A batch has to price several, and
the honest generalisation is symmetric: every rider on a touched route is charged
`w x (ride - baseline)`, where the baseline is the ride they would have had without this
plan - their direct time if they are new, their current ride if they are already seated.
For a single insertion this equals §4 plus the newcomer's own excess ride, which §4 leaves
out because a lone insertion has no one else to blame it on; for two newcomers who detour
each other it is the only definition that does not ignore half the harm.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

from app.domain.cost import rider_weight
from app.domain.dispatch import (
    AssignmentFacts,
    DetourLimits,
    Insertion,
    Place,
    Rider,
    Violation,
    check_hard_rules,
)
from app.domain.dispatch import Plan as StopPlan
from app.domain.enums import Direction, Urgency
from app.domain.optimizer.model import Problem, Req, Seated, Veh
from app.domain.timeofday import local_time

VIP_VEHICLE_TYPE = "vip"
DISPATCHABLE = frozenset({"available", "on_trip"})


@dataclass(frozen=True, slots=True)
class Person:
    """A rider on a route, new or already seated - one shape for the evaluator."""

    seated: Seated | None = None
    req: Req | None = None

    @property
    def request_id(self) -> uuid.UUID:
        return self.seated.request_id if self.seated else self._req.request_id

    @property
    def _req(self) -> Req:
        assert self.req is not None
        return self.req

    @property
    def is_new(self) -> bool:
        return self.seated is None

    @property
    def rider(self) -> Rider:
        return self.seated.rider if self.seated else self._req.rider

    @property
    def picked_up(self) -> bool:
        return self.seated.picked_up if self.seated else False

    @property
    def ridden_seconds(self) -> float:
        return self.seated.ridden_seconds if self.seated else 0.0

    @property
    def priority(self) -> int:
        return self.seated.priority if self.seated else self._req.priority

    @property
    def urgency(self) -> Urgency:
        return self.seated.urgency if self.seated else self._req.urgency

    @property
    def limits(self) -> DetourLimits:
        return self.seated.limits if self.seated else self._req.limits

    @property
    def exclusive(self) -> bool:
        if self.seated:
            return self.seated.no_sharing or self.seated.is_vip
        return self._req.no_sharing or self._req.is_vip

    @property
    def night_escort_required(self) -> bool:
        if self.seated:
            return self.seated.night_escort_required
        return self._req.night_escort_required


def seated_people(trip_riders: Sequence[Seated]) -> list[Person]:
    return [Person(seated=rider) for rider in trip_riders]


def new_person(req: Req) -> Person:
    return Person(req=req)


@dataclass(frozen=True, slots=True)
class RouteEval:
    order: tuple[Person, ...]
    #: Seconds from now until each rider is collected (to_office), or until the cab is at
    #: the office where everyone boards (from_office). Absent for riders already aboard.
    pickup_arrival: dict[uuid.UUID, float]
    ride_seconds: dict[uuid.UUID, float]
    approach_seconds: float
    approach_meters: float
    total_seconds: float


def direct_seconds(problem: Problem, person: Person, direction: Direction, office: Place) -> float:
    rider = person.rider
    return problem.duration(
        rider.pickup_place(direction, office), rider.drop_place(direction, office)
    )


def evaluate_route(
    problem: Problem,
    veh: Veh,
    direction: Direction,
    office: Place,
    order: Sequence[Person],
) -> RouteEval:
    """Times along the route for this rider order, from the vehicle's position now."""
    here = veh.position
    pickup_arrival: dict[uuid.UUID, float] = {}
    ride: dict[uuid.UUID, float] = {}

    if direction is Direction.to_office:
        elapsed = 0.0
        previous = here
        first_leg: tuple[float, float] | None = None
        for person in order:
            if person.picked_up:
                continue
            stop = person.rider.pickup_place(direction, office)
            leg = problem.duration(previous, stop)
            if first_leg is None:
                first_leg = (leg, problem.distance(previous, stop))
            elapsed += leg
            pickup_arrival[person.request_id] = elapsed
            previous = stop
        if first_leg is None:
            first_leg = (problem.duration(here, office), problem.distance(here, office))
        total = elapsed + problem.duration(previous, office)
        for person in order:
            if person.picked_up:
                ride[person.request_id] = person.ridden_seconds + total
            else:
                ride[person.request_id] = total - pickup_arrival[person.request_id]
        return RouteEval(tuple(order), pickup_arrival, ride, first_leg[0], first_leg[1], total)

    # from_office: the cab goes to the office first, unless the riders already left it.
    left_office = any(person.picked_up for person in order)
    if left_office:
        approach = 0.0
        approach_m = 0.0
        elapsed = 0.0
        previous = here
        departed = 0.0
    else:
        approach = problem.duration(here, office)
        approach_m = problem.distance(here, office)
        elapsed = approach
        previous = office
        departed = approach
    for person in order:
        stop = person.rider.drop_place(direction, office)
        elapsed += problem.duration(previous, stop)
        previous = stop
        if not person.picked_up:
            pickup_arrival[person.request_id] = departed
        ride[person.request_id] = person.ridden_seconds + (elapsed - departed)
    return RouteEval(tuple(order), pickup_arrival, ride, approach, approach_m, elapsed)


def route_proximity_seconds(
    problem: Problem,
    veh: Veh,
    direction: Direction,
    office: Place,
    existing: Sequence[Person],
    newcomer: Person,
) -> float:
    """How far off its route the cab must go to collect this rider (B33).

    `allocation-rules.md` §3: an en-route cab is a candidate if its **route** passes within
    `enroute_reuse_max_eta_minutes` of the pickup. The Phase 1 number was the straight ETA
    from the cab's current position, which cannot tell a cab whose next stop is the rider's
    street from one that is two minutes away and heading the other way - the first is the
    best candidate there is and the second is a trap.

    The measure is the extra driving, in seconds, of the cheapest place to fit the pickup
    into the cab's remaining stops: `dur(a, p) + dur(p, b) - dur(a, b)` for the best leg
    `(a, b)`. A cab already on its way past the rider scores near zero however far away it
    is; one near the rider that must double back scores about twice its distance.
    """
    if direction is Direction.from_office:
        # Every pickup is the office, which this cab is already heading for.
        return 0.0
    pickup = newcomer.rider.pickup_place(direction, office)
    stops = [veh.position]
    stops += [
        person.rider.pickup_place(direction, office) for person in existing if not person.picked_up
    ]
    stops.append(office)
    best = float("inf")
    for index in range(len(stops) - 1):
        a, b = stops[index], stops[index + 1]
        extra = problem.duration(a, pickup) + problem.duration(pickup, b) - problem.duration(a, b)
        best = min(best, max(extra, 0.0))
    return best


@dataclass(frozen=True, slots=True)
class RouteCheck:
    route: RouteEval
    violations: tuple[Violation, ...]


def check_route(
    problem: Problem,
    veh: Veh,
    direction: Direction,
    office_id: uuid.UUID,
    order: Sequence[Person],
) -> RouteCheck:
    """Evaluate a rider order and apply every hard rule that depends on the route."""
    office = problem.offices[office_id]
    route = evaluate_route(problem, veh, direction, office, order)

    limits = {person.request_id: person.limits for person in order}
    direct = {
        person.request_id: direct_seconds(problem, person, direction, office) for person in order
    }
    flagged = {person.request_id for person in order if person.night_escort_required}
    riders_in_order = tuple(person.rider for person in order)
    plan = StopPlan(
        order=riders_in_order,
        stops=(),
        ride_seconds=dict(route.ride_seconds),
        total_seconds=route.total_seconds,
    )
    insertion = Insertion(plan=plan, position=0, added_minutes={})

    found: list[Violation] = []

    def note(violations: Sequence[Violation]) -> None:
        for violation in violations:
            if violation not in found:
                found.append(violation)

    trip = veh.trip
    for person in order:
        if not person.is_new:
            continue
        req = person.req
        assert req is not None
        arrival = route.pickup_arrival.get(req.request_id, 0.0)
        pickup_at = problem.now + timedelta(seconds=arrival)
        if trip is None:
            eta_for_ceiling = route.approach_seconds
        else:
            existing = [other for other in order if other.request_id != req.request_id]
            eta_for_ceiling = route_proximity_seconds(
                problem, veh, direction, office, existing, person
            )
        facts = AssignmentFacts(
            vehicle_id=veh.vehicle_id,
            vehicle_status=veh.status,
            vehicle_type=veh.vehicle_type,
            gps_age_seconds=veh.gps_age_seconds,
            stale_gps_seconds=problem.params.stale_gps_seconds,
            eta_to_pickup_seconds=eta_for_ceiling,
            candidate_max_eta_minutes=req.candidate_max_eta_minutes,
            pickup_window_minutes=req.pickup_window_minutes,
            requested_time=req.requested_time,
            pickup_at=pickup_at,
            direction=direction,
            office_id=office_id,
            employee_is_vip=req.is_vip,
            request_no_sharing=req.no_sharing,
            lock_vehicle_id=req.lock_vehicle_id,
            enroute_reuse_max_eta_minutes=problem.params.enroute_reuse_max_eta_minutes,
            trip_direction=trip.direction if trip else None,
            trip_office_id=trip.office_id if trip else None,
            trip_pooling_blocked=trip.pooling_blocked if trip else False,
            trip_has_other_riders=len(order) > 1,
            night_safety_enabled=req.night.enabled,
            night_start=req.night.start,
            night_end=req.night.end,
            night_safety_positions=req.night.positions,
            pickup_time_local=local_time(pickup_at, problem.timezone),
        )
        note(check_hard_rules(facts, insertion, limits, direct, flagged))

    # An exclusive rider already seated (a VIP, or an opt-out) is protected from the
    # *newcomer's* side as well: `check_hard_rules` only looks at the new rider's flags,
    # and a trip that was not marked `pooling_blocked` would otherwise accept company.
    if len(order) > 1 and any(person.exclusive for person in order):
        note([Violation.no_sharing])

    # Seats. Not a `Violation` (ADR-0011 refuses capacity outright instead), but an
    # automatic path must never produce it either.
    if len(order) > veh.seat_capacity:
        note([Violation.vehicle_unavailable])

    return RouteCheck(route, tuple(found))


@dataclass(frozen=True, slots=True)
class RouteCost:
    total: float
    wait: float
    detour: float
    empty_km: float
    new_vehicle: float
    added_minutes: dict[uuid.UUID, float]


def price_route(
    problem: Problem,
    veh: Veh,
    direction: Direction,
    office_id: uuid.UUID,
    route: RouteEval,
    baseline: dict[uuid.UUID, float],
) -> RouteCost:
    """`allocation-rules.md` §4, generalised to a batch (see the module docstring)."""
    weights = problem.params.weights
    office = problem.offices[office_id]
    wait = 0.0
    detour = 0.0
    added: dict[uuid.UUID, float] = {}
    any_new = False
    for person in route.order:
        w = rider_weight(person.priority, person.urgency, weights)
        base = baseline.get(person.request_id)
        if base is None:
            base = direct_seconds(problem, person, direction, office)
        extra = max(route.ride_seconds[person.request_id] - base, 0.0) / 60.0
        added[person.request_id] = extra
        detour += w * extra
        if person.is_new:
            any_new = True
            req = person.req
            assert req is not None
            from_time = max((req.requested_time - problem.now).total_seconds(), 0.0)
            arrival = route.pickup_arrival.get(req.request_id, 0.0)
            wait += weights.weight_wait * w * max(arrival - from_time, 0.0) / 60.0

    idle = veh.trip is None
    empty_km = (
        weights.weight_empty_km * (route.approach_meters / 1000.0) if idle and any_new else 0.0
    )
    new_vehicle = weights.cost_new_vehicle if idle and any_new else 0.0
    return RouteCost(
        total=wait + detour + empty_km + new_vehicle,
        wait=wait,
        detour=detour,
        empty_km=empty_km,
        new_vehicle=new_vehicle,
        added_minutes=added,
    )


def baseline_rides(
    problem: Problem, veh: Veh, direction: Direction, office_id: uuid.UUID
) -> dict[uuid.UUID, float]:
    """Each seated rider's ride on the trip as it stands now: what "added" is measured from."""
    if veh.trip is None or not veh.trip.riders:
        return {}
    people = seated_people(veh.trip.riders)
    route = evaluate_route(problem, veh, direction, problem.offices[office_id], people)
    return dict(route.ride_seconds)


def refusal_for(problem: Problem, veh: Veh, req: Req) -> str | None:
    """A reason this vehicle can never take this request, from facts that do not vary with
    route order. `None` means worth evaluating. Cheap, so both solvers use it to prune.
    """
    if veh.status not in DISPATCHABLE:
        return Violation.vehicle_unavailable
    if veh.gps_age_seconds is None or veh.gps_age_seconds > problem.params.stale_gps_seconds:
        return Violation.gps_stale
    if req.lock_vehicle_id is not None and req.lock_vehicle_id != veh.vehicle_id:
        return Violation.locked_to_other_vehicle
    if req.is_vip and veh.vehicle_type != VIP_VEHICLE_TYPE:
        return Violation.vip_needs_vip_vehicle
    trip = veh.trip
    if trip is None:
        return None
    if trip.direction is not req.direction:
        return Violation.direction_mismatch
    if trip.office_id != req.office_id:
        return Violation.office_mismatch
    if trip.pooling_blocked:
        return Violation.pooling_blocked
    if req.no_sharing or req.is_vip or any(r.no_sharing or r.is_vip for r in trip.riders):
        return Violation.no_sharing
    if req.direction is Direction.from_office and trip.pickups_done:
        # Riders have already left the office, which is where every pickup is.
        return Violation.vehicle_unavailable
    if len(trip.riders) + 1 > veh.seat_capacity:
        return Violation.vehicle_unavailable
    return None
