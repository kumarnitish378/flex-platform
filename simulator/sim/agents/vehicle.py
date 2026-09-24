"""Vehicle agent: movement and GPS ping generation (`simulator-spec.md` §4, §5.1).

M02 covers movement only. Duty, trip acceptance, stop actions and faults arrive with
M04/M05; this agent already emits the pings those stages need.

Movement model:
  speed per segment = provider speed x traffic factor x noise (lognormal, sigma 0.15)
  reported position  = true position + Gaussian noise (sigma 5 m)

The provider's geometry is followed exactly, whatever produced it. Under `approx` that is
a straight line; under a self-hosted OSRM it is the real road polyline. The agent does not
care which, so a scenario runs the same way with either.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import numpy as np
import simpy

from sim.engine import Engine
from sim.geo import LatLng, haversine_km
from sim.pings import Ping, PingSink, ping_interval_seconds
from sim.routing import Route

# simulator-spec.md §4.
SPEED_NOISE_SIGMA = 0.15
GPS_NOISE_METRES = 5.0

# Rough metres per degree of latitude; good enough to turn a GPS error in metres into a
# coordinate offset at NCR latitudes.
METRES_PER_DEGREE_LAT = 111_320.0


@dataclass(frozen=True, slots=True)
class VehicleConfig:
    speed_noise_sigma: float = SPEED_NOISE_SIGMA
    gps_noise_metres: float = GPS_NOISE_METRES
    ping_loss_rate: float = 0.0
    battery_start: int = 100


class VehicleAgent:
    """One simulated cab."""

    def __init__(
        self,
        engine: Engine,
        vehicle_id: str,
        start: LatLng,
        sink: PingSink,
        config: VehicleConfig | None = None,
    ) -> None:
        self.engine = engine
        self.vehicle_id = vehicle_id
        self.position = start
        self.speed_ms = 0.0
        self.heading = 0.0
        self.on_duty = False

        self._sink = sink
        self._config = config or VehicleConfig()
        self._rng: np.random.Generator = engine.rng.for_agent(vehicle_id)
        self._stationary_since: float | None = engine.env.now
        self._battery = float(self._config.battery_start)

    # --- duty ---------------------------------------------------------------

    def go_on_duty(self) -> None:
        self.on_duty = True
        self._stationary_since = self.engine.env.now
        self.engine.record(f"{self.vehicle_id} on duty")

    def go_off_duty(self) -> None:
        # "Off duty: none" - no GPS at all (mqtt-topics.md, and the privacy rule in
        # non-functional.md: driver GPS is collected only while on duty).
        self.on_duty = False
        self.speed_ms = 0.0
        self.engine.record(f"{self.vehicle_id} off duty")

    # --- processes ----------------------------------------------------------

    def idle(self) -> Generator[simpy.Event, Any, None]:
        """Sit still, pinging at the stationary cadence while on duty."""
        while True:
            self._maybe_emit()
            yield self.engine.env.timeout(self._current_interval())

    def drive_to(self, destination: LatLng) -> Generator[simpy.Event, Any, None]:
        """Follow the routed geometry to `destination`, pinging on the way."""
        route = self.route_to(destination)
        if route.duration_seconds <= 0:
            self.position = destination
            self._maybe_emit()
            return

        started_at = self.engine.env.now
        self._stationary_since = None

        while True:
            elapsed = self.engine.env.now - started_at
            if elapsed >= route.duration_seconds:
                break

            previous = self.position
            self.position = route.position_at(elapsed)
            self._update_motion(previous, self.position, self._current_interval())
            self._maybe_emit()
            yield self.engine.env.timeout(self._current_interval())

        self.position = destination
        self.speed_ms = 0.0
        self._stationary_since = self.engine.env.now
        self._maybe_emit()
        self.engine.record(
            f"{self.vehicle_id} arrived at {destination.lat:.4f},{destination.lng:.4f}"
        )

    # --- routing ------------------------------------------------------------

    def route_to(self, destination: LatLng) -> Route:
        """Route from here, with this vehicle's speed noise applied to the duration."""
        route = self.engine.routing.route(self.position, destination, self.engine.now())
        noise = float(self._rng.lognormal(mean=0.0, sigma=self._config.speed_noise_sigma))
        return Route(
            duration_seconds=route.duration_seconds * noise,
            distance_meters=route.distance_meters,
            geometry=route.geometry,
            approximate=route.approximate,
        )

    # --- internals ----------------------------------------------------------

    def _current_interval(self) -> int:
        stationary_for = (
            0.0 if self._stationary_since is None else self.engine.env.now - self._stationary_since
        )
        return ping_interval_seconds(self.speed_ms, stationary_for)

    def _update_motion(self, previous: LatLng, current: LatLng, seconds: float) -> None:
        distance_m = haversine_km(previous, current) * 1000.0
        self.speed_ms = distance_m / seconds if seconds > 0 else 0.0
        if distance_m > 0:
            self.heading = _bearing(previous, current)
        if self.speed_ms <= 1.0 and self._stationary_since is None:
            self._stationary_since = self.engine.env.now
        elif self.speed_ms > 1.0:
            self._stationary_since = None

    def _maybe_emit(self) -> None:
        """Emit a ping unless off duty, or unless this one is 'lost'."""
        if not self.on_duty:
            return
        if self._config.ping_loss_rate > 0 and self._rng.random() < self._config.ping_loss_rate:
            return

        self._battery = max(0.0, self._battery - 0.001)
        self._sink.emit(
            Ping(
                vehicle_id=self.vehicle_id,
                ts=self.engine.now(),
                lat=self._noisy_lat(),
                lng=self._noisy_lng(),
                spd=self.speed_ms,
                hdg=self.heading,
                acc=self._config.gps_noise_metres,
                bat=int(self._battery),
                src="sim",
            )
        )

    def _noisy_lat(self) -> float:
        return self.position.lat + self._gps_offset_degrees()

    def _noisy_lng(self) -> float:
        # Longitude degrees shrink with latitude.
        scale = max(0.1, float(np.cos(np.radians(self.position.lat))))
        return self.position.lng + self._gps_offset_degrees() / scale

    def _gps_offset_degrees(self) -> float:
        if self._config.gps_noise_metres <= 0:
            return 0.0
        metres = float(self._rng.normal(0.0, self._config.gps_noise_metres))
        return metres / METRES_PER_DEGREE_LAT


def _bearing(origin: LatLng, destination: LatLng) -> float:
    """Compass bearing in degrees, 0-359."""
    lat1, lat2 = np.radians(origin.lat), np.radians(destination.lat)
    dlng = np.radians(destination.lng - origin.lng)
    y = np.sin(dlng) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlng)
    return float((np.degrees(np.arctan2(y, x)) + 360.0) % 360.0)
