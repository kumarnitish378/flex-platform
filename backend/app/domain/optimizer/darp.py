"""Pickup-and-delivery with time windows and capacities, on OR-Tools routing (B31, ADR-0027).

`allocation-rules.md` §6: "Model: Pickup-and-Delivery Problem with Time Windows and
capacities (Dial-a-Ride), solved with Google OR-Tools routing using OSRM time matrices.
Objective matches the cost function; hard rules become constraints."

**Why this is a plain VRP and not a full pickup-and-delivery model.** Trip shape fixes one
end of every rider's journey at the one office (`model.py`), so the delivery half of each
request is a node every rider shares. What the solver actually chooses is *which cab* and
*in what order* - an open-ended vehicle-routing problem with time windows, capacities and
ride-time limits. Modelling the shared office as 2N separate delivery nodes would add
variables and no freedom.

**The hard rules are constraints** (what the model searches over):

* capacity - seats, per vehicle, with riders already aboard taken off it;
* exclusivity - a second dimension, so a VIP or opt-out rider can never share a cab;
* rule 8 - a hard time window around the requested time (`to_office`);
* rule 7 - a maximum ride time per rider, conditional on the cab they end up in;
* which cabs a request may use at all - locks, VIP vehicle type, direction and office,
  blocked trips, the candidate and en-route ceilings;
* seated riders - mandatory on their own cab, in their own order when it is fixed.

**The objective is §4's cost, as far as arc costs can say it.** The routing library
minimises a sum over arcs plus fixed costs; §4's detour term is a function of a whole
path, so it cannot be written exactly. What the arcs do carry exactly is the empty
kilometres of an idle cab's approach and the cost of waking an idle cab (a fixed cost);
every minute of driving is charged at the batch's mean rider weight, which is the rider
time that driving burns. The honest part is what happens next: **the result is re-priced
exactly by `route.price_route`**, and `solve()` keeps whichever of this plan and the
greedy plan is better under §4. The surrogate steers the search; it does not get to
decide the answer.

**Determinism.** The search stops on a solution count, not on the clock, so the answer
does not depend on how fast the machine is. `time_limit_seconds` is a failsafe cap only.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.domain.cost import rider_weight
from app.domain.dispatch import Place
from app.domain.enums import Direction
from app.domain.optimizer.model import Placement, Plan, Problem, Req, Unplaced, Veh
from app.domain.optimizer.route import (
    Person,
    baseline_rides,
    check_route,
    direct_seconds,
    excess_minutes,
    new_person,
    price_route,
    refusal_for,
    route_proximity_seconds,
    seated_people,
)

#: Cost units per minute-equivalent. Arc costs must be integers.
SCALE = 100
#: Seconds a cab spends at a stop. Zero: the exact evaluator (`route.py`) charges none, and
#: a model that charged one would reject a rider the evaluator accepts at the edge of a
#: window. Two stops at one address may therefore tie; `_restore_fixed_order` settles it.
DWELL_SECONDS = 0
#: A day. The routing library needs a finite horizon.
HORIZON_SECONDS = 24 * 3600
#: Per-vehicle load that no one may share: an exclusive rider weighs this much on the
#: exclusivity dimension, every other rider weighs 1, and the capacity is this much.
EXCLUSIVE_LOAD = 1000
#: Cost of leaving a request unserved. Far above any route cost, scaled by the rider's
#: weight so that when seats run out, the heavier rider is the one served.
UNSERVED_PENALTY = 50_000_000


class DarpUnavailableError(RuntimeError):
    """The model found no solution (infeasible or out of time). Callers fall back."""


@dataclass(slots=True)
class _Group:
    direction: Direction
    office_id: uuid.UUID
    requests: list[Req]


def solve_darp(problem: Problem) -> Plan:
    """A plan from OR-Tools, or `DarpUnavailableError` when it has none to give."""
    groups: dict[tuple[str, uuid.UUID], _Group] = {}
    # Sorted, so the node numbering - and with it every tie-break the search makes - does
    # not depend on the order the caller happened to list the requests in.
    for req in sorted(problem.requests, key=lambda r: (r.queued_at, str(r.request_id))):
        key = (str(req.direction), req.office_id)
        groups.setdefault(key, _Group(req.direction, req.office_id, [])).requests.append(req)

    used_vehicles: set[uuid.UUID] = set()
    placements: list[Placement] = []
    unplaced: list[Unplaced] = []
    any_solution = False

    for key in sorted(groups, key=lambda k: (k[0], str(k[1]))):
        group = groups[key]
        result = _solve_group(problem, group, used_vehicles)
        if result is None:
            unplaced.extend(Unplaced(req.request_id, ("no_vehicle",)) for req in group.requests)
            continue
        any_solution = True
        group_placements, group_unplaced = result
        for placement in group_placements:
            used_vehicles.add(placement.vehicle_id)
        placements.extend(group_placements)
        unplaced.extend(group_unplaced)

    if not any_solution:
        raise DarpUnavailableError("OR-Tools returned no solution for any group")
    placements.sort(key=lambda placement: str(placement.vehicle_id))
    return Plan(
        placements=tuple(placements),
        unplaced=tuple(unplaced),
        solver="darp",
        cost=sum(placement.cost for placement in placements),
    )


def _solve_group(
    problem: Problem, group: _Group, used: set[uuid.UUID]
) -> tuple[list[Placement], list[Unplaced]] | None:
    direction, office_id = group.direction, group.office_id
    office = problem.offices[office_id]
    params = problem.params
    weights = params.weights

    # --- which cabs take part, and which requests each may use --------------------------
    allowed: dict[uuid.UUID, list[int]] = defaultdict(list)  # request id -> vehicle slots
    vehicles: list[Veh] = []
    for veh in sorted(problem.vehicles, key=lambda v: str(v.vehicle_id)):
        if veh.vehicle_id in used:
            continue
        if veh.trip is not None and (
            veh.trip.direction is not direction or veh.trip.office_id != office_id
        ):
            continue
        if veh.trip is not None and _already_over_limit(problem, veh, direction, office_id):
            continue
        vehicles.append(veh)

    usable: list[Veh] = []
    request_vehicles: dict[uuid.UUID, list[Veh]] = {}
    refusals: dict[uuid.UUID, set[str]] = defaultdict(set)
    for req in group.requests:
        fits: list[Veh] = []
        if (
            direction is Direction.to_office
            and (req.requested_time - problem.now).total_seconds() + req.pickup_window_minutes * 60
            < 0
        ):
            # Rule 8: the window around the requested time has already closed.
            refusals[req.request_id].add("pickup_window_missed")
            request_vehicles[req.request_id] = fits
            continue
        for veh in vehicles:
            why = refusal_for(problem, veh, req)
            if why is None:
                why = _ceiling_refusal(problem, veh, req, direction, office)
            if why is None:
                fits.append(veh)
            else:
                refusals[req.request_id].add(str(why))
        request_vehicles[req.request_id] = fits
    needed = {veh.vehicle_id for fits in request_vehicles.values() for veh in fits}
    usable = [veh for veh in vehicles if veh.vehicle_id in needed]

    servable = [req for req in group.requests if request_vehicles[req.request_id]]
    unplaced = [
        Unplaced(req.request_id, tuple(sorted(refusals[req.request_id])) or ("no_vehicle",))
        for req in group.requests
        if not request_vehicles[req.request_id]
    ]
    if not servable:
        return [], unplaced

    slot_of = {veh.vehicle_id: slot for slot, veh in enumerate(usable)}
    for req in servable:
        allowed[req.request_id] = [slot_of[v.vehicle_id] for v in request_vehicles[req.request_id]]

    # --- nodes -----------------------------------------------------------------------------
    # to_office:   [vehicle starts..., office, stops...]   routes end at the office
    # from_office: [office, end, stops...]                  routes start at the office
    places: list[Place] = []
    to_office = direction is Direction.to_office
    start_nodes: list[int] = []
    if to_office:
        for veh in usable:
            start_nodes.append(len(places))
            places.append(veh.position)
        office_node = len(places)
        places.append(office)
        end_node = office_node
        first_stop = len(places)
    else:
        office_node = len(places)
        places.append(office)
        end_node = len(places)
        places.append(office)  # the open end: zero-cost arcs from every stop
        start_nodes = [office_node] * len(usable)
        first_stop = len(places)

    node_person: dict[int, Person] = {}
    node_vehicle: dict[int, int] = {}  # seated nodes are bound to their cab
    for slot, veh in enumerate(usable):
        if veh.trip is None:
            continue
        for person in seated_people(veh.trip.riders):
            if person.picked_up:
                continue
            node = len(places)
            places.append(_own_end(person, direction, office))
            node_person[node] = person
            node_vehicle[node] = slot
    for req in servable:
        node = len(places)
        places.append(_own_end(new_person(req), direction, office))
        node_person[node] = new_person(req)

    # --- the cost surrogate ----------------------------------------------------------------
    all_weights = [rider_weight(p.priority, p.urgency, weights) for p in node_person.values()] or [
        1.0
    ]
    mean_weight = sum(all_weights) / len(all_weights)

    def seconds_between(a: int, b: int) -> int:
        if to_office is False and b == end_node:
            return 0
        if a == b:
            return 0
        return int(round(problem.duration(places[a], places[b])))

    approach = {
        slot: int(round(problem.duration(veh.position, office))) for slot, veh in enumerate(usable)
    }

    manager = pywrapcp.RoutingIndexManager(
        len(places), len(usable), start_nodes, [end_node] * len(usable)
    )
    routing = pywrapcp.RoutingModel(manager)

    def transit(from_index: int, to_index: int) -> int:
        a, b = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        if not to_office and b == end_node:
            return 0
        dwell = DWELL_SECONDS if b >= first_stop else 0
        return seconds_between(a, b) + dwell

    idle_start = (
        {start_nodes[slot]: slot for slot, veh in enumerate(usable) if veh.trip is None}
        if to_office
        else {}
    )

    def cost(from_index: int, to_index: int) -> int:
        a, b = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        if not to_office and b == end_node:
            return 0
        minutes = seconds_between(a, b) / 60.0
        value = mean_weight * minutes
        if to_office and a in idle_start:
            value += weights.weight_empty_km * (problem.distance(places[a], places[b]) / 1000.0)
        return int(round(value * SCALE))

    transit_index = routing.RegisterTransitCallback(transit)
    routing.SetArcCostEvaluatorOfAllVehicles(routing.RegisterTransitCallback(cost))

    routing.AddDimension(transit_index, 0, HORIZON_SECONDS, to_office, "Time")
    time = routing.GetDimensionOrDie("Time")
    solver = routing.solver()

    if not to_office:
        for slot in range(len(usable)):
            time.CumulVar(routing.Start(slot)).SetRange(approach[slot], approach[slot])

    # Fixed cost of waking an idle cab, and its empty approach when that is one lump.
    for slot, veh in enumerate(usable):
        if veh.trip is None:
            lump = weights.cost_new_vehicle
            if not to_office:
                lump += weights.weight_empty_km * (problem.distance(veh.position, office) / 1000.0)
            routing.SetFixedCostOfVehicle(int(round(lump * SCALE)), slot)

    # --- capacity and exclusivity ------------------------------------------------------------
    def seat_demand(index: int) -> int:
        person = node_person.get(manager.IndexToNode(index))
        return 1 if person is not None else 0

    def exclusive_demand(index: int) -> int:
        person = node_person.get(manager.IndexToNode(index))
        if person is None:
            return 0
        return EXCLUSIVE_LOAD if person.exclusive else 1

    onboard = [
        sum(1 for p in seated_people(v.trip.riders) if p.picked_up) if v.trip else 0 for v in usable
    ]
    routing.AddDimensionWithVehicleCapacity(
        routing.RegisterUnaryTransitCallback(seat_demand),
        0,
        [veh.seat_capacity - onboard[slot] for slot, veh in enumerate(usable)],
        True,
        "Seats",
    )
    routing.AddDimensionWithVehicleCapacity(
        routing.RegisterUnaryTransitCallback(exclusive_demand),
        0,
        [EXCLUSIVE_LOAD] * len(usable),
        True,
        "Exclusive",
    )

    # --- per-node constraints -----------------------------------------------------------------
    for node, person in node_person.items():
        index = manager.NodeToIndex(node)
        if person.is_new:
            wanted = person.req
            assert wanted is not None
            _restrict_vehicles(routing, index, allowed[wanted.request_id], len(usable))
            routing.AddDisjunction(
                [index],
                int(
                    UNSERVED_PENALTY * (1 + rider_weight(wanted.priority, wanted.urgency, weights))
                ),
            )
            if to_office:
                asked = int((wanted.requested_time - problem.now).total_seconds())
                window = wanted.pickup_window_minutes * 60
                time.CumulVar(index).SetRange(max(0, asked - window), asked + window)
            # Approach ceiling for an idle cab: it may not open its route with a stop it
            # cannot reach in time (rule: candidate_max_eta_minutes).
            if to_office:
                for slot in allowed[wanted.request_id]:
                    veh = usable[slot]
                    if veh.trip is None:
                        eta = problem.duration(
                            veh.position, person.rider.pickup_place(direction, office)
                        )
                        if eta > wanted.candidate_max_eta_minutes * 60:
                            routing.NextVar(routing.Start(slot)).RemoveValue(index)
        else:
            _restrict_vehicles(routing, index, [node_vehicle[node]], len(usable))

        # Rule 7: ride time no longer than the stricter of factor and minutes.
        direct = direct_seconds(problem, person, direction, office)
        limit = int(
            min(
                direct * person.limits.max_detour_factor,
                direct + person.limits.max_detour_minutes * 60,
            )
        )
        for slot in allowed[person.request_id] if person.is_new else [node_vehicle[node]]:
            on_cab = solver.IsEqualCstVar(routing.VehicleVar(index), slot)
            if to_office:
                ride = time.CumulVar(routing.End(slot)) - time.CumulVar(index)
            else:
                ride = time.CumulVar(index) - time.CumulVar(routing.Start(slot))
            solver.Add(solver.ConditionalExpression(on_cab, ride, -HORIZON_SECONDS) <= limit)

    # Riders already aboard: their ride so far plus the rest of this route.
    if to_office:
        for slot, veh in enumerate(usable):
            if veh.trip is None:
                continue
            for person in seated_people(veh.trip.riders):
                if person.picked_up:
                    direct = direct_seconds(problem, person, direction, office)
                    limit = int(
                        min(
                            direct * person.limits.max_detour_factor,
                            direct + person.limits.max_detour_minutes * 60,
                        )
                        - person.ridden_seconds
                    )
                    time.CumulVar(routing.End(slot)).SetMax(max(limit, 0))

    # Fixed-order trips keep their riders' relative order; new riders slot in around them.
    for slot, veh in enumerate(usable):
        if veh.trip is None or not veh.trip.order_fixed:
            continue
        order_ids = [person.request_id for person in seated_people(veh.trip.riders)]
        chain = sorted(
            (node for node in node_person if node_vehicle.get(node) == slot),
            key=lambda node: order_ids.index(node_person[node].request_id),
        )
        for earlier, later in zip(chain, chain[1:], strict=False):
            solver.Add(
                time.CumulVar(manager.NodeToIndex(earlier))
                <= time.CumulVar(manager.NodeToIndex(later))
            )

    # --- search -----------------------------------------------------------------------------------
    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search.solution_limit = params.solution_limit
    search.time_limit.FromMilliseconds(int(params.time_limit_seconds * 1000))
    solution = routing.SolveWithParameters(search)
    if solution is None:
        raise DarpUnavailableError(f"OR-Tools status {routing.status()}")

    # --- read it back, and judge it with the exact evaluator ----------------------------
    placements: list[Placement] = []
    leftover: list[Req] = []
    served: set[uuid.UUID] = set()
    for slot, veh in enumerate(usable):
        index = routing.Start(slot)
        order_nodes: list[int] = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node in node_person:
                order_nodes.append(node)
            index = solution.Value(routing.NextVar(index))
        people = [node_person[node] for node in order_nodes]
        # Riders already aboard are not nodes, but they are on the route all the same.
        if veh.trip is not None:
            people = [
                *[p for p in seated_people(veh.trip.riders) if p.picked_up],
                *people,
            ]
        new_here = [p for p in people if p.is_new]
        if not new_here:
            continue
        if veh.trip is not None and veh.trip.order_fixed:
            people = _restore_fixed_order(people, veh)
        checked = check_route(problem, veh, direction, office_id, people)
        if checked.violations:
            leftover.extend(r for r in (p.req for p in new_here) if r is not None)
            continue
        baseline = (
            baseline_rides(problem, veh, direction, office_id) if veh.trip is not None else {}
        )
        cost_parts = price_route(problem, veh, direction, office_id, checked.route, baseline)
        current = [p.request_id for p in seated_people(veh.trip.riders)] if veh.trip else []
        proposed_existing = [p.request_id for p in people if not p.is_new]
        placements.append(
            Placement(
                vehicle_id=veh.vehicle_id,
                trip_id=veh.trip.trip_id if veh.trip else None,
                order=tuple(p.request_id for p in people),
                new_request_ids=tuple(p.request_id for p in new_here),
                pickup_eta_seconds={
                    p.request_id: checked.route.pickup_arrival.get(p.request_id, 0.0)
                    for p in new_here
                },
                added_minutes=dict(cost_parts.added_minutes),
                cost=cost_parts.total,
                reorders_existing=proposed_existing != current,
                excess_minutes=excess_minutes(problem, direction, office_id, checked.route),
            )
        )
        served.update(p.request_id for p in new_here)

    leftover_ids = {req.request_id for req in leftover}
    for req in servable:
        if req.request_id not in served:
            unplaced.append(
                Unplaced(
                    req.request_id,
                    ("rule_violation",) if req.request_id in leftover_ids else ("not_served",),
                )
            )
    return placements, unplaced


def _restore_fixed_order(people: list[Person], veh: Veh) -> list[Person]:
    """Put a fixed-order trip's riders back in their own order.

    The model only forces `<=` between them, so two riders at one address can come out
    swapped - harmlessly for the cost, but a fixed trip's order is a promise to its driver.
    The seated riders keep the *positions* the route gave them and take their original order.
    """
    assert veh.trip is not None
    original = {p.request_id: p for p in seated_people(veh.trip.riders)}
    order = [rider.request_id for rider in veh.trip.riders]
    slots = [i for i, p in enumerate(people) if not p.is_new and not p.picked_up]
    restored = list(people)
    queue = [original[request_id] for request_id in order if not original[request_id].picked_up]
    for position, person in zip(slots, queue, strict=False):
        restored[position] = person
    return restored


def _restrict_vehicles(
    routing: pywrapcp.RoutingModel, index: int, allowed: list[int], vehicles: int
) -> None:
    """Which cabs may serve a node.

    `RoutingModel.SetAllowedVehiclesForIndex` is the obvious call and this OR-Tools
    build's Python binding cannot take its `absl::Span` argument, so the same restriction
    is expressed on the vehicle variable directly. `-1` (unperformed) is left in the domain:
    whether a node is optional is the disjunction's business, not this function's.
    """
    var = routing.VehicleVar(index)
    for slot in range(vehicles):
        if slot not in allowed:
            var.RemoveValue(slot)


def _own_end(person: Person, direction: Direction, office: Place) -> Place:
    rider = person.rider
    return (
        rider.pickup_place(direction, office)
        if direction is Direction.to_office
        else rider.drop_place(direction, office)
    )


def _ceiling_refusal(
    problem: Problem, veh: Veh, req: Req, direction: Direction, office: Place
) -> str | None:
    """The candidate and en-route ceilings, which depend on the cab's position or route."""
    if veh.trip is None:
        approach = (
            problem.duration(veh.position, req.rider.pickup_place(direction, office))
            if direction is Direction.to_office
            else problem.duration(veh.position, office)
        )
        if approach > req.candidate_max_eta_minutes * 60:
            return "eta_over_candidate_limit"
        return None
    proximity = route_proximity_seconds(
        problem, veh, direction, office, seated_people(veh.trip.riders), new_person(req)
    )
    if proximity > problem.params.enroute_reuse_max_eta_minutes * 60:
        return "enroute_reuse_eta_exceeded"
    return None


def _already_over_limit(
    problem: Problem, veh: Veh, direction: Direction, office_id: uuid.UUID
) -> bool:
    """A trip whose riders already exceed rule 7 can take no one: nothing fixes that."""
    assert veh.trip is not None
    rides = baseline_rides(problem, veh, direction, office_id)
    office = problem.offices[office_id]
    for person in seated_people(veh.trip.riders):
        direct = direct_seconds(problem, person, direction, office)
        limit = min(
            direct * person.limits.max_detour_factor,
            direct + person.limits.max_detour_minutes * 60,
        )
        if rides.get(person.request_id, 0.0) > limit + 1.0:
            return True
    return False
