"""A flat world for optimizer tests: latitude is minutes, the office is the origin.

Durations are straight lines at 6000 seconds per degree, so 0.01 degree is one minute and
a test can state "a rider ten minutes out, on the way" as a number rather than a map. The
point is that a plan's cost can be worked out by hand, and a brute-force search over the
same world can be compared with what the solver returns.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.cost import CostWeights
from app.domain.dispatch import DetourLimits, Place, Rider
from app.domain.enums import Direction, Urgency
from app.domain.optimizer.model import (
    OptimizerParams,
    Problem,
    Req,
    Seated,
    TripState,
    Veh,
)

NOW = datetime(2026, 10, 16, 8, 0, tzinfo=UTC)
OFFICE_ID = uuid.UUID("00000000-0000-0000-0000-0000000000f1")
OFFICE = Place(0.0, 0.0)
SECONDS_PER_DEGREE = 6000.0
METRES_PER_DEGREE = 111_000.0


def seconds(a: Place, b: Place) -> float:
    return math.hypot(a.lat - b.lat, a.lng - b.lng) * SECONDS_PER_DEGREE


def metres(a: Place, b: Place) -> float:
    return math.hypot(a.lat - b.lat, a.lng - b.lng) * METRES_PER_DEGREE


def minutes_out(minutes: float, side: float = 0.0) -> Place:
    """A point `minutes` from the office along the north axis, `side` degrees east."""
    return Place(minutes / 100.0, side)


def rid(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


def req(
    n: int,
    place: Place,
    *,
    direction: Direction = Direction.to_office,
    priority: int = 5,
    urgency: Urgency = Urgency.medium,
    requested_in_minutes: float = 0.0,
    **overrides: Any,
) -> Req:
    base: dict[str, Any] = {
        "request_id": rid(n),
        "rider": Rider(rid(n), place),
        "direction": direction,
        "office_id": OFFICE_ID,
        "priority": priority,
        "urgency": urgency,
        "requested_time": NOW + timedelta(minutes=requested_in_minutes),
        "queued_at": NOW,
        "is_vip": False,
        "no_sharing": False,
        "limits": DetourLimits(max_detour_factor=1.5, max_detour_minutes=15),
        "pickup_window_minutes": 10,
        "candidate_max_eta_minutes": 20,
    }
    base.update(overrides)
    return Req(**base)


def seated(n: int, place: Place, **overrides: Any) -> Seated:
    base: dict[str, Any] = {
        "request_id": rid(n),
        "rider": Rider(rid(n), place),
        "picked_up": False,
        "ridden_seconds": 0.0,
        "priority": 5,
        "urgency": Urgency.medium,
        "limits": DetourLimits(max_detour_factor=1.5, max_detour_minutes=15),
    }
    base.update(overrides)
    return Seated(**base)


def trip(
    n: int, riders: list[Seated], *, direction: Direction = Direction.to_office, **overrides: Any
) -> TripState:
    base: dict[str, Any] = {
        "trip_id": uuid.UUID(int=10_000 + n),
        "direction": direction,
        "office_id": OFFICE_ID,
        "riders": tuple(riders),
    }
    base.update(overrides)
    return TripState(**base)


def veh(n: int, place: Place, *, seats: int = 4, **overrides: Any) -> Veh:
    base: dict[str, Any] = {
        "vehicle_id": uuid.UUID(int=1_000 + n),
        "position": place,
        "gps_age_seconds": 5.0,
        "status": "available",
        "vehicle_type": "sedan_4",
        "seat_capacity": seats,
    }
    base.update(overrides)
    return Veh(**base)


def problem(
    requests: list[Req],
    vehicles: list[Veh],
    params: OptimizerParams | None = None,
    **overrides: Any,
) -> Problem:
    base: dict[str, Any] = {
        "now": NOW,
        "timezone": "UTC",
        "offices": {OFFICE_ID: OFFICE},
        "requests": tuple(requests),
        "vehicles": tuple(vehicles),
        "duration": seconds,
        "distance": metres,
        "params": params or OptimizerParams(weights=CostWeights(), dwell_seconds=0),
    }
    base.update(overrides)
    return Problem(**base)
