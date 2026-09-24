"""Geocoding providers.

Phase 1 ships exactly one: `none`. The public Nominatim is not an option — its usage
policy forbids vehicle-tracking applications and asks that no personal data be submitted,
and employee home locations are personal data (ADR-0010 A1). Settings reject a public
Nominatim URL outright, so this is enforced at startup as well as here.

Locations come from map pins plus landmark text. A self-hosted Nominatim implementation
may be added behind this interface later (task I02c) without touching any caller.
"""

from __future__ import annotations

from app.domain.geo import LatLng
from app.modules.routing.types import GeocodingUnavailableError, Place


class NoGeocodingProvider:
    """The Phase 1 provider: there is no address lookup, and that is deliberate."""

    name = "none"

    async def search(self, query: str, *, limit: int = 5) -> list[Place]:
        raise GeocodingUnavailableError(
            "Geocoding is disabled in Phase 1: set locations with a map pin and landmark "
            "text (ADR-0010 A1). A self-hosted Nominatim can be enabled with "
            "GEOCODING_PROVIDER=nominatim once task I02c is done."
        )

    async def reverse(self, location: LatLng) -> Place | None:
        raise GeocodingUnavailableError("Reverse geocoding is disabled in Phase 1 (ADR-0010 A1).")
