"""Network-free travel time estimation.

`approx` is the floor the whole system stands on: it always answers, so a dead, slow or
rate-limited OSRM degrades quality instead of breaking dispatch (`control-model.md` §6).
It is also the only provider the simulator and the optimizer may use, because they issue
thousands of requests per run (ADR-0010 rule 6).

Method: great-circle distance x a road factor, divided by a time-of-day speed.
Every number is a config key, never a literal in the logic (CLAUDE.md hard rule 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time, timedelta, timezone

from app.core.clock import Clock
from app.domain.geo import LatLng, haversine_km
from app.modules.routing.types import RouteResult, Source, TableResult

# The platform stores UTC; these windows are local Indian time (coding-standards §2.13).
IST = timezone(timedelta(hours=5, minutes=30))


@dataclass(frozen=True, slots=True)
class SpeedWindow:
    """A local-time window and the speed factor that applies inside it."""

    start: time
    end: time
    factor: float

    def contains(self, moment: time) -> bool:
        if self.start <= self.end:
            return self.start <= moment < self.end
        # Window wraps past midnight (e.g. 22:00-06:00).
        return moment >= self.start or moment < self.end


@dataclass(frozen=True, slots=True)
class ApproxConfig:
    """Defaults for the `approx` estimator.

    - `road_factor` 1.4 is specified: `control-model.md` §6 and ADR-0010 rule 2.
    - Peak windows and the 0.6 peak factor come from `simulator-spec.md` §6.
    - `base_speed_kmh` is NOT specified anywhere in the docs. The value here is a
      provisional NCR figure pending OQ-22; it is a config key so tuning it needs no
      code change.
    """

    base_speed_kmh: float = 24.0
    road_factor: float = 1.4
    windows: tuple[SpeedWindow, ...] = field(
        default_factory=lambda: (
            SpeedWindow(time(8, 0), time(10, 30), 0.6),  # morning peak
            SpeedWindow(time(17, 30), time(20, 30), 0.6),  # evening peak
            SpeedWindow(time(23, 0), time(6, 0), 1.3),  # free-flowing night
        )
    )

    def speed_kmh_at(self, local: time) -> float:
        for window in self.windows:
            if window.contains(local):
                return self.base_speed_kmh * window.factor
        return self.base_speed_kmh


class ApproxRoutingProvider:
    """Straight-line distance x road factor, at a time-of-day speed. No network."""

    name = "approx"

    def __init__(self, clock: Clock, config: ApproxConfig | None = None) -> None:
        self._clock = clock
        self._config = config or ApproxConfig()

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        distance_m, duration_s = self._estimate(origin, destination)
        return RouteResult(
            duration_seconds=duration_s,
            distance_meters=distance_m,
            source=Source.approx,
            approximate=True,
            # No road geometry exists without a road network; the straight line is
            # honest about that and is what the simulator animates.
            geometry=(origin, destination),
        )

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        durations: list[tuple[float, ...]] = []
        distances: list[tuple[float, ...]] = []
        for origin in origins:
            row = [self._estimate(origin, destination) for destination in destinations]
            distances.append(tuple(distance for distance, _ in row))
            durations.append(tuple(duration for _, duration in row))
        return TableResult(
            durations=tuple(durations),
            distances=tuple(distances),
            source=Source.approx,
            approximate=True,
        )

    async def close(self) -> None:
        return None

    def _estimate(self, origin: LatLng, destination: LatLng) -> tuple[float, float]:
        """Return (metres, seconds)."""
        road_km = haversine_km(origin, destination) * self._config.road_factor
        local_time = self._clock.now().astimezone(IST).time()
        speed_kmh = self._config.speed_kmh_at(local_time)
        seconds = (road_km / speed_kmh) * 3600.0 if speed_kmh > 0 else 0.0
        return road_km * 1000.0, seconds
