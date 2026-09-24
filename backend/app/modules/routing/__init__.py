"""Routing and geocoding.

The only part of the system that talks to OSRM. Callers depend on the protocols in
`types.py` and never on a concrete implementation, which is what lets configuration
alone switch between the public OSM servers and a self-hosted stack (ADR-0010).
"""

from app.modules.routing.factory import (
    build_geocoding_provider,
    build_rate_limiter,
    build_routing_provider,
)
from app.modules.routing.service import Eta, EtaConfig, EtaService
from app.modules.routing.types import (
    GeocodingProvider,
    GeocodingUnavailableError,
    Place,
    RouteResult,
    RoutingProvider,
    Source,
    TableResult,
)

__all__ = [
    "Eta",
    "EtaConfig",
    "EtaService",
    "GeocodingProvider",
    "GeocodingUnavailableError",
    "Place",
    "RouteResult",
    "RoutingProvider",
    "Source",
    "TableResult",
    "build_geocoding_provider",
    "build_rate_limiter",
    "build_routing_provider",
]
