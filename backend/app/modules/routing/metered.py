"""Counts what the routing stack actually did (`non-functional.md`, Operability).

A wrapper rather than counters sprinkled through the providers, because the three
numbers the operability section asks for - cache hit rate, calls per provider, and the
share of answers served as approximate - are all properties of the *answer*, and every
answer carries its own `source` and `approximate`. One wrapper at the outermost layer
therefore sees all of them, and a provider added later is counted without being edited.

The one thing it cannot see is a call that was never made: the rate limiter refusing a
token happens inside the OSRM client, which counts that itself.
"""

from __future__ import annotations

from app.core import metrics
from app.domain.geo import LatLng
from app.modules.routing.types import RouteResult, RoutingProvider, TableResult


class MeteredRoutingProvider:
    """Passes every call through, recording where the answer came from."""

    def __init__(self, inner: RoutingProvider) -> None:
        self._inner = inner
        #: Reported as the wrapped provider's name, not "metered": callers log this to
        #: say which provider answered, and the wrapper is not one.
        self.name = inner.name

    @property
    def inner(self) -> RoutingProvider:
        """The provider underneath, for tests that assert on what was selected."""
        return self._inner

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        result = await self._inner.route(origin, destination)
        metrics.observe_routing("route", str(result.source), result.approximate)
        return result

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        result = await self._inner.table(origins, destinations)
        metrics.observe_routing("table", str(result.source), result.approximate)
        return result

    async def close(self) -> None:
        await self._inner.close()
