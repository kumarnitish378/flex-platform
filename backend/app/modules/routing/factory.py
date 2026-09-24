"""Build the configured providers.

This is the only place that decides which implementation runs, so switching between the
public OSM servers and a self-hosted stack really is a configuration change
(ADR-0010) — no caller, test or screen changes.
"""

from __future__ import annotations

from app.core.clock import Clock
from app.core.logging import get_logger
from app.core.redis import RedisLike
from app.core.settings import (
    PUBLIC_OSM_HOSTS,
    GeocodingProviderName,
    RoutingProviderName,
    Settings,
    host_of,
)
from app.modules.routing.approx import ApproxConfig, ApproxRoutingProvider
from app.modules.routing.cache import CachedRoutingProvider
from app.modules.routing.geocoding import NoGeocodingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.rate_limit import (
    RateLimiter,
    RedisRateLimiter,
    UnlimitedRateLimiter,
)
from app.modules.routing.types import GeocodingProvider, RoutingProvider

logger = get_logger(__name__)


def build_rate_limiter(settings: Settings, redis: RedisLike | None) -> RateLimiter:
    """Rate limiting applies to public hosts only; our own OSRM needs no budget."""
    if host_of(settings.osrm_url) not in PUBLIC_OSM_HOSTS:
        return UnlimitedRateLimiter()
    if redis is None:
        # Without Redis we cannot coordinate across processes, so we cannot honour a
        # shared budget. Refusing every request (and using approx) is the safe choice.
        logger.warning("rate_limiter_without_redis", detail="public OSRM calls will be skipped")
        return _AlwaysDeny()
    return RedisRateLimiter(redis, requests_per_second=settings.osm_rate_limit_per_second)


def build_routing_provider(
    settings: Settings,
    clock: Clock,
    redis: RedisLike | None = None,
) -> RoutingProvider:
    approx = ApproxRoutingProvider(clock, ApproxConfig())

    if settings.routing_provider is RoutingProviderName.approx:
        return approx

    osrm = OsrmRoutingProvider(
        settings.osrm_url,
        fallback=approx,
        limiter=build_rate_limiter(settings, redis),
        user_agent=settings.user_agent,
        timeout_seconds=settings.osm_request_timeout_seconds,
    )

    if settings.routing_provider is RoutingProviderName.osrm:
        return osrm

    if redis is None:
        logger.warning("routing_cache_disabled", detail="no redis; using osrm without cache")
        return osrm
    return CachedRoutingProvider(osrm, redis, ttl_seconds=settings.routing_cache_ttl_seconds)


def build_geocoding_provider(settings: Settings) -> GeocodingProvider:
    if settings.geocoding_provider is GeocodingProviderName.none:
        return NoGeocodingProvider()
    # Settings guarantee a self-hosted, non-public URL here; the implementation itself
    # arrives with task I02c.
    raise NotImplementedError(
        "GEOCODING_PROVIDER=nominatim needs the self-hosted client from task I02c. "
        "Phase 1 runs with GEOCODING_PROVIDER=none."
    )


class _AlwaysDeny:
    async def try_acquire(self, service: str) -> bool:
        return False
