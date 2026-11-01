"""The optimizer's vocabulary: a problem goes in, a plan comes out (`allocation-rules.md` §6).

Everything here is a frozen dataclass of plain values. **No database, no clock, no routing
client**: the caller loads the facts and supplies two callables, `duration` and `distance`,
already backed by one pre-fetched matrix (ADR-0010: the shared public server has a
1 request/second budget). That is what B31 asks for - "the solver is pure of the database,
so the same inputs always give the same plan and a scenario can be replayed" - and it is
also what makes the worked examples in `allocation-rules.md` tests rather than comments.

Trip shape is the one `domain/dispatch.py` documents and the data model stores: **one
direction, one office**, every rider contributing a pickup and a drop.

    to_office     vehicle -> pickup(r1) -> pickup(r2) ... -> office (every drop)
    from_office   vehicle -> office (every pickup) -> drop(r1) -> drop(r2) ...

Because every drop (to_office) or every pickup (from_office) sits at the one office, a
route is fully described by **the order of the riders' own ends**. That is the whole
search space, and it is why an exact evaluator is cheap enough to sit under both solvers.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, time

from app.domain.cost import CostWeights
from app.domain.dispatch import DetourLimits, Place, Rider
from app.domain.enums import Direction, Urgency

Seconds = Callable[[Place, Place], float]


@dataclass(frozen=True, slots=True)
class NightPolicy:
    """Rule 11 for one rider's client, already resolved against operator config."""

    enabled: bool = False
    start: time = time(20, 0)
    end: time = time(6, 0)
    positions: str = "both"


@dataclass(frozen=True, slots=True)
class OptimizerParams:
    """The operator's numbers (CLAUDE.md hard rule 4: they come from config, not code)."""

    weights: CostWeights = field(default_factory=CostWeights)
    stale_gps_seconds: int = 60
    #: Seconds a cab spends at each stop (`stop_dwell_seconds`): riders getting in or out.
    #: Without it a plan promises rides that the people on board then spend minutes
    #: waiting for others to board, and a pooled rider's ride runs past rule 7's limit
    #: on a plan the evaluator had passed (found by the first live S10 run).
    dwell_seconds: int = 60
    enroute_reuse_max_eta_minutes: int = 5
    #: Hard cap on one DARP run (`optimizer_time_limit_seconds`). A failsafe, not a tuning
    #: knob: the search stops on `solution_limit` first, so the answer does not depend on
    #: how fast the machine is.
    time_limit_seconds: float = 10.0
    solution_limit: int = 60


@dataclass(frozen=True, slots=True)
class Req:
    """A request waiting to be placed."""

    request_id: uuid.UUID
    rider: Rider
    direction: Direction
    office_id: uuid.UUID
    #: Already the *effective* pair: `force_priority` has been applied (ADR-0021).
    priority: int
    urgency: Urgency
    requested_time: datetime
    queued_at: datetime
    is_vip: bool
    #: The request's own opt-out **or** a client policy that forbids pooling.
    no_sharing: bool
    limits: DetourLimits
    pickup_window_minutes: int
    #: The effective ceiling, already widened for a request nobody has served (ADR-0019).
    candidate_max_eta_minutes: int
    #: The vehicle an active lock pins this request to, or `None`.
    lock_vehicle_id: uuid.UUID | None = None
    night_escort_required: bool = False
    night: NightPolicy = field(default_factory=NightPolicy)


@dataclass(frozen=True, slots=True)
class Seated:
    """A rider already on a trip. The optimizer may *carry* them, never *change* them
    except by inserting someone beside them (`allocation-rules.md` §6, last bullet)."""

    request_id: uuid.UUID
    rider: Rider
    picked_up: bool
    #: Seconds already spent in the cab. Zero until they are picked up.
    ridden_seconds: float
    priority: int
    urgency: Urgency
    limits: DetourLimits
    no_sharing: bool = False
    is_vip: bool = False
    locked: bool = False
    night_escort_required: bool = False


@dataclass(frozen=True, slots=True)
class TripState:
    trip_id: uuid.UUID
    direction: Direction
    office_id: uuid.UUID
    #: Riders in their current stop order.
    riders: tuple[Seated, ...]
    #: The trip's `pooling_blocked` flag **as it currently applies** (override expiry
    #: already taken into account). A blocked trip takes no one.
    pooling_blocked: bool = False
    #: True when the existing order must not be rearranged: the trip is under way, or it
    #: carries a locked rider. New riders may still be inserted into it.
    order_fixed: bool = True
    #: A `from_office` trip whose riders have left the office can take nobody new, because
    #: every pickup *is* the office.
    pickups_done: bool = False


@dataclass(frozen=True, slots=True)
class Veh:
    vehicle_id: uuid.UUID
    position: Place
    gps_age_seconds: float | None
    #: `available` or `on_trip`; anything else is not offered to the optimizer at all.
    status: str
    vehicle_type: str
    seat_capacity: int
    trip: TripState | None = None


@dataclass(frozen=True)
class Problem:
    now: datetime
    #: The operator's wall-clock zone, for rule 11's night window.
    timezone: str
    offices: dict[uuid.UUID, Place]
    requests: tuple[Req, ...]
    vehicles: tuple[Veh, ...]
    duration: Seconds
    distance: Seconds
    params: OptimizerParams = field(default_factory=OptimizerParams)


@dataclass(frozen=True, slots=True)
class Placement:
    """One vehicle's new rider order, and what it costs."""

    vehicle_id: uuid.UUID
    trip_id: uuid.UUID | None
    #: Every rider on the resulting trip, in stop order - existing and new.
    order: tuple[uuid.UUID, ...]
    new_request_ids: tuple[uuid.UUID, ...]
    #: Seconds from now to each *new* rider's pickup.
    pickup_eta_seconds: dict[uuid.UUID, float]
    #: Extra minutes each rider spends in the cab against their baseline.
    added_minutes: dict[uuid.UUID, float]
    cost: float
    #: True when the order differs from the trip's current one (a rearrangement).
    reorders_existing: bool = False
    #: Minutes each rider on the resulting trip spends in the cab beyond riding alone.
    #: What pooling costs them; stored on the request and shown beside the rider (A17).
    excess_minutes: dict[uuid.UUID, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Unplaced:
    request_id: uuid.UUID
    #: Why nothing took it: a rule name, or a structural reason such as `no_vehicle`.
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Plan:
    placements: tuple[Placement, ...] = ()
    unplaced: tuple[Unplaced, ...] = ()
    #: `greedy`, `darp`, or `greedy_fallback` when the DARP produced nothing usable.
    solver: str = "greedy"
    cost: float = 0.0

    @property
    def placed_ids(self) -> frozenset[uuid.UUID]:
        return frozenset(rid for placement in self.placements for rid in placement.new_request_ids)

    @property
    def empty(self) -> bool:
        return not self.placements
