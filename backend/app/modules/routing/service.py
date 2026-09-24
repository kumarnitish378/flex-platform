"""ETA service: the one way the rest of the backend asks "how long from A to B?".

Built on the `RoutingProvider` interface from I02, never on a concrete OSRM client, so
switching between the public demo server and a self-hosted instance stays a configuration
change (ADR-0010).

Two things happen on top of the provider:

1. **A time-of-day factor.** ADR-0004 is explicit that "ETAs start from OSM speeds +
   time-of-day factors"; OSRM's own durations come from free-flow road speeds and are
   optimistic in an NCR peak. The factor is a config value, not a literal
   (CLAUDE.md hard rule 4), and is *not* applied to `approx` results, which already price
   the time of day into their speed table - applying it twice would double-count.

2. **The `approximate` flag.** Whatever the provider degraded to, callers learn whether
   this ETA came from road routing, and the flag reaches the client
   (`api-spec.yaml`: `eta_approximate`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone

from app.core.clock import Clock
from app.domain.geo import LatLng
from app.modules.routing.types import RoutingProvider, Source

IST = timezone(timedelta(hours=5, minutes=30))


@dataclass(frozen=True, slots=True)
class TrafficWindow:
    """A local-time window and the factor applied to routed durations inside it."""

    start: time
    end: time
    factor: float

    def contains(self, moment: time) -> bool:
        if self.start <= self.end:
            return self.start <= moment < self.end
        return moment >= self.start or moment < self.end


@dataclass(frozen=True, slots=True)
class EtaConfig:
    """Time-of-day factors applied to routed durations.

    Values are provisional (OQ-22): the peak windows and the 0.6 factor come from
    `simulator-spec.md` §6, expressed here as a duration multiplier (1 / 0.6). They belong
    in `operator_config` and move there with task B05; until then this dataclass is the
    single place to change them, and no caller hard-codes a number.

    `road_speed_profile` learned from our own GPS replaces these in Phase 2
    (ADR-0004, architecture.md §3.2 step 5).
    """

    windows: tuple[TrafficWindow, ...] = field(
        default_factory=lambda: (
            TrafficWindow(time(8, 0), time(10, 30), 1 / 0.6),
            TrafficWindow(time(17, 30), time(20, 30), 1 / 0.6),
            TrafficWindow(time(23, 0), time(6, 0), 1 / 1.3),
        )
    )

    def factor_at(self, local: time) -> float:
        for window in self.windows:
            if window.contains(local):
                return window.factor
        return 1.0


@dataclass(frozen=True, slots=True)
class Eta:
    """An answer the whole backend can use, honest about where it came from."""

    seconds: float
    distance_meters: float
    approximate: bool
    source: Source

    @property
    def minutes(self) -> float:
        return self.seconds / 60.0

    def arrival_from(self, departure: datetime) -> datetime:
        return departure + timedelta(seconds=self.seconds)


class EtaService:
    """Travel-time estimates for dispatch, tracking and the ETA refresh job."""

    def __init__(
        self,
        provider: RoutingProvider,
        clock: Clock,
        config: EtaConfig | None = None,
    ) -> None:
        self._provider = provider
        self._clock = clock
        self._config = config or EtaConfig()

    async def eta(self, origin: LatLng, destination: LatLng) -> Eta:
        """Travel time from `origin` to `destination`, leaving now."""
        route = await self._provider.route(origin, destination)
        return Eta(
            seconds=self._adjust(route.duration_seconds, route.approximate),
            distance_meters=route.distance_meters,
            approximate=route.approximate,
            source=route.source,
        )

    async def eta_matrix(
        self, origins: list[LatLng], destinations: list[LatLng]
    ) -> list[list[Eta]]:
        """Travel times for every origin/destination pair.

        One provider call, not `len(origins) * len(destinations)` calls: on a public
        server that difference is the whole rate-limit budget for several minutes.
        """
        table = await self._provider.table(origins, destinations)
        return [
            [
                Eta(
                    seconds=self._adjust(duration, table.approximate),
                    distance_meters=table.distances[row][column],
                    approximate=table.approximate,
                    source=table.source,
                )
                for column, duration in enumerate(durations)
            ]
            for row, durations in enumerate(table.durations)
        ]

    async def arrival_time(self, origin: LatLng, destination: LatLng) -> tuple[datetime, bool]:
        """Absolute arrival time and whether it is approximate."""
        estimate = await self.eta(origin, destination)
        return estimate.arrival_from(self._clock.now()), estimate.approximate

    def _adjust(self, seconds: float, approximate: bool) -> float:
        """Apply the time-of-day factor to routed durations only."""
        if approximate:
            # `approx` already used a time-of-day speed; factoring again double-counts.
            return seconds
        local = self._clock.now().astimezone(IST).time()
        return seconds * self._config.factor_at(local)
