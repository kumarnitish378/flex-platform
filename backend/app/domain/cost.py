"""The assignment cost function (`allocation-rules.md` §4, Phase 2 task B22).

Pure: no database, no routing client, no clock. The caller supplies the facts and the
config values, which is what lets the worked example in §8 be a test rather than a
comment.

**Everything is in minutes-equivalent.** That is the whole design of §4: a rider's wait,
another rider's detour and an empty kilometre are all converted to the same unit so they
can be added. Nothing here is a probability or a score out of ten.

**There is no traffic term, and adding one would be a defect.** Traffic is already inside
every ETA the caller passes in - that is what the time-of-day factor table and OSRM are
for - so a separate term would count it twice. `allocation-rules.md` §4 says so in one
line; `test_cost.py` says so in a test.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.enums import Urgency

#: `w = ((11 - priority) / 10) x urgency_factor`. Priority is 1 (highest) to 10.
MIN_PRIORITY = 1
MAX_PRIORITY = 10


@dataclass(frozen=True, slots=True)
class CostWeights:
    """The operator's §4 weights. Defaults match `config_keys.py`, and must stay matched.

    Passed in rather than read here, because `ConfigService` is per operator and this
    module is pure (CLAUDE.md hard rule 4: business numbers come from config).
    """

    weight_wait: float = 1.0
    weight_empty_km: float = 2.0
    cost_new_vehicle: float = 15.0
    urgency_factor_high: float = 3.0
    urgency_factor_medium: float = 1.5
    urgency_factor_low: float = 1.0

    def urgency_factor(self, urgency: Urgency | str) -> float:
        return {
            Urgency.high: self.urgency_factor_high,
            Urgency.medium: self.urgency_factor_medium,
            Urgency.low: self.urgency_factor_low,
        }[Urgency(urgency)]


@dataclass(frozen=True, slots=True)
class ExistingRider:
    """Someone already on the vehicle's trip, and what this insertion costs them."""

    request_id: uuid.UUID
    priority: int
    urgency: Urgency
    added_minutes: float


@dataclass(frozen=True, slots=True)
class CostInput:
    """Everything §4 needs to price one (request, vehicle) pair."""

    #: The new rider.
    priority: int
    urgency: Urgency
    #: Minutes from the requested time - or from now if that is already past - to the
    #: pickup ETA. Never negative: arriving early is not a negative wait, it is zero.
    wait_minutes: float
    #: Empty kilometres this assignment adds (approach with nobody aboard).
    empty_km_added: float
    #: True when the vehicle is idle and this opens a new trip.
    new_trip: bool
    riders_on_board: tuple[ExistingRider, ...] = ()
    #: Deterministic tie-break, never part of the arithmetic.
    eta_to_pickup_seconds: float = 0.0
    vehicle_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    """The total, and each term that made it.

    Kept apart rather than summed in place because B23 shows a supervisor *why* a
    suggestion costs what it does, and a single number cannot be argued with.
    """

    total: float
    wait: float
    detour: float
    empty_km: float
    new_vehicle: float
    rider_weight: float
    #: Per existing rider, their weighted detour contribution.
    detour_by_rider: dict[uuid.UUID, float] = field(default_factory=dict)


def rider_weight(priority: int, urgency: Urgency | str, weights: CostWeights) -> float:
    """`((11 - priority) / 10) x urgency_factor` (`allocation-rules.md` §4, Rider weight).

    Priority 1 is the *highest*, so the numerator inverts it: priority 1 contributes 1.0
    and priority 10 contributes 0.1. Getting that backwards would quietly serve the
    least important rider first, and every number downstream would still look plausible.
    """
    if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValueError(f"priority must be {MIN_PRIORITY}-{MAX_PRIORITY}, got {priority}")
    return ((11 - priority) / 10) * weights.urgency_factor(urgency)


def effective_rider(
    priority: int, urgency: Urgency | str, *, forced_priority: bool
) -> tuple[int, Urgency]:
    """What priority and urgency the cost function should actually use.

    `control-model.md` §3 defines the `force_priority` override as "treat request as
    priority 1 / high urgency". Phase 1 stored the flag and nothing read it, so a
    supervisor could force a request to the front of a queue that did not exist yet.
    Phase 2's cost function is the thing that was missing.

    The stored `priority` and `urgency` are **not** rewritten - the rider's own answer
    stays the rider's (ADR-0021). This is the view the scorer takes, nothing more.
    """
    if forced_priority:
        return MIN_PRIORITY, Urgency.high
    return priority, Urgency(urgency)


def assignment_cost(facts: CostInput, weights: CostWeights) -> CostBreakdown:
    """Cost of assigning one request to one vehicle, in minutes-equivalent.

        cost = weight_wait x w_r x wait_r
             + sum over riders already aboard of ( w_i x added_minutes_i )
             + weight_empty_km x empty_km_added
             + cost_new_vehicle if the vehicle is idle

    Lower is better.
    """
    w_r = rider_weight(facts.priority, facts.urgency, weights)
    # A pickup earlier than asked for is not a negative wait. Allowing it would let an
    # early cab buy its way past a rider who has actually been waiting.
    wait = weights.weight_wait * w_r * max(facts.wait_minutes, 0.0)

    detour_by_rider: dict[uuid.UUID, float] = {}
    for rider in facts.riders_on_board:
        contribution = rider_weight(rider.priority, rider.urgency, weights) * max(
            rider.added_minutes, 0.0
        )
        detour_by_rider[rider.request_id] = contribution
    detour = sum(detour_by_rider.values())

    empty_km = weights.weight_empty_km * max(facts.empty_km_added, 0.0)
    new_vehicle = weights.cost_new_vehicle if facts.new_trip else 0.0

    return CostBreakdown(
        total=wait + detour + empty_km + new_vehicle,
        wait=wait,
        detour=detour,
        empty_km=empty_km,
        new_vehicle=new_vehicle,
        rider_weight=w_r,
        detour_by_rider=detour_by_rider,
    )


def ranking_key(facts: CostInput, cost: CostBreakdown) -> tuple[float, float, str]:
    """Order candidates: lowest cost, then soonest, then lowest vehicle id.

    `allocation-rules.md` §4: "Ties -> lower ETA -> lower vehicle id (deterministic)".
    Determinism is not tidiness - the simulator replays a seed and expects the same
    choices, and a supervisor who refreshes the screen must not see a different top
    suggestion.
    """
    return (cost.total, facts.eta_to_pickup_seconds, str(facts.vehicle_id or ""))
