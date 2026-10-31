"""Single-insertion greedy over a batch (`allocation-rules.md` §6: "fall back to single-insertion
greedy using §4").

This is Phase 2's strategy, made pure and run across a whole batch: take the requests in
order of importance, and put each where it adds least to the total cost, keeping every
existing rider's relative order (an insertion, never a rearrangement). It is the answer
whenever the DARP has none, and the baseline the DARP must beat to be used at all.

Order of play is the rider weight, heaviest first, then the earlier ask, then the id - so
the same problem always gives the same plan, and a VIP or a priority-1 rider gets the first
pick of the cabs rather than the last.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.cost import rider_weight
from app.domain.optimizer.model import Placement, Plan, Problem, Req, Unplaced, Veh
from app.domain.optimizer.route import (
    Person,
    RouteCost,
    RouteEval,
    baseline_rides,
    check_route,
    new_person,
    price_route,
    refusal_for,
    seated_people,
)


@dataclass(slots=True)
class _Slot:
    """A vehicle's evolving route during one solve."""

    veh: Veh
    order: list[Person]
    baseline: dict[uuid.UUID, float]
    cost: RouteCost | None = None
    route: RouteEval | None = None
    new_ids: list[uuid.UUID] = field(default_factory=list)


def request_order(problem: Problem) -> list[Req]:
    weights = problem.params.weights
    return sorted(
        problem.requests,
        key=lambda req: (
            -rider_weight(req.priority, req.urgency, weights),
            req.queued_at,
            str(req.request_id),
        ),
    )


def solve_greedy(problem: Problem, *, only: frozenset[uuid.UUID] | None = None) -> Plan:
    """Place each request where it is cheapest; `only` restricts to a subset (for repair)."""
    slots: dict[uuid.UUID, _Slot] = {}
    for veh in problem.vehicles:
        trip = veh.trip
        direction_office = (trip.direction, trip.office_id) if trip else None
        baseline = (
            baseline_rides(problem, veh, direction_office[0], direction_office[1])
            if direction_office
            else {}
        )
        slots[veh.vehicle_id] = _Slot(
            veh=veh,
            order=seated_people(trip.riders) if trip else [],
            baseline=baseline,
        )

    unplaced: list[Unplaced] = []
    for req in request_order(problem):
        if only is not None and req.request_id not in only:
            continue
        person = new_person(req)
        best: tuple[tuple[float, float, str], _Slot, list[Person], RouteEval, RouteCost] | None = (
            None
        )
        reasons: set[str] = set()

        for slot in slots.values():
            veh = slot.veh
            # A slot that already took a newcomer this batch is no longer idle for the
            # purposes of "does this need a trip of its own", but its trip identity is
            # unchanged: the direction and office were fixed by its first rider.
            why = _refusal(problem, slot, req)
            if why is not None:
                reasons.add(why)
                continue
            current_cost = slot.cost.total if slot.cost else 0.0
            for position in range(len(slot.order) + 1):
                trial = [*slot.order[:position], person, *slot.order[position:]]
                checked = check_route(problem, veh, req.direction, req.office_id, trial)
                if checked.violations:
                    reasons.update(str(v) for v in checked.violations)
                    continue
                cost = price_route(
                    problem, veh, req.direction, req.office_id, checked.route, slot.baseline
                )
                delta = cost.total - current_cost
                arrival = checked.route.pickup_arrival.get(req.request_id, 0.0)
                key = (delta, arrival, str(veh.vehicle_id))
                if best is None or key < best[0]:
                    best = (key, slot, trial, checked.route, cost)

        if best is None:
            unplaced.append(Unplaced(req.request_id, tuple(sorted(reasons)) or ("no_vehicle",)))
            continue
        _, slot, trial, route, cost = best
        slot.order = trial
        slot.route = route
        slot.cost = cost
        slot.new_ids.append(req.request_id)

    placements = [
        _placement(slot) for slot in slots.values() if slot.new_ids and slot.route and slot.cost
    ]
    placements.sort(key=lambda placement: str(placement.vehicle_id))
    return Plan(
        placements=tuple(placements),
        unplaced=tuple(unplaced),
        solver="greedy",
        cost=sum(placement.cost for placement in placements),
    )


def _refusal(problem: Problem, slot: _Slot, req: Req) -> str | None:
    """Static refusal, taking into account riders already placed on this slot this batch."""
    veh = slot.veh
    why = refusal_for(problem, veh, req)
    if why is not None:
        return why
    if slot.new_ids:
        # The slot has taken a newcomer, so it carries riders now whatever it did before.
        existing_new = [p.req for p in slot.order if p.is_new and p.req is not None]
        if req.no_sharing or req.is_vip or any(r.no_sharing or r.is_vip for r in existing_new):
            return "no_sharing"
        if slot.veh.trip is None:
            first = existing_new[0]
            if first.direction is not req.direction or first.office_id != req.office_id:
                return (
                    "direction_mismatch"
                    if first.direction is not req.direction
                    else ("office_mismatch")
                )
        if len(slot.order) + 1 > veh.seat_capacity:
            return "vehicle_unavailable"
    return None


def _placement(slot: _Slot) -> Placement:
    assert slot.route is not None and slot.cost is not None
    route = slot.route
    return Placement(
        vehicle_id=slot.veh.vehicle_id,
        trip_id=slot.veh.trip.trip_id if slot.veh.trip else None,
        order=tuple(person.request_id for person in route.order),
        new_request_ids=tuple(slot.new_ids),
        pickup_eta_seconds={rid: route.pickup_arrival.get(rid, 0.0) for rid in slot.new_ids},
        added_minutes=dict(slot.cost.added_minutes),
        cost=slot.cost.total,
        reorders_existing=False,
    )
