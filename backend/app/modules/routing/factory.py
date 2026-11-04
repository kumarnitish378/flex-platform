"""Build the configured providers.

This is the only place that decides which implementation runs, so switching between the
public OSM servers and a self-hosted stack really is a configuration change
(ADR-0010) — no caller, test or screen changes.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from app.modules.routing.metered import MeteredRoutingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.rate_limit import (
    RateLimiter,
    RedisRateLimiter,
    UnlimitedRateLimiter,
)
from app.modules.routing.service import EtaService
from app.modules.routing.speed_profile import LearnedSpeeds, database_loader
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
    learned: LearnedSpeeds | None = None,
) -> RoutingProvider:
    approx = ApproxRoutingProvider(clock, ApproxConfig(), learned)

    if settings.routing_provider is RoutingProviderName.approx:
        return MeteredRoutingProvider(approx)

    osrm = OsrmRoutingProvider(
        settings.osrm_url,
        fallback=approx,
        limiter=build_rate_limiter(settings, redis),
        user_agent=settings.user_agent,
        timeout_seconds=settings.osm_request_timeout_seconds,
    )

    if settings.routing_provider is RoutingProviderName.osrm:
        return MeteredRoutingProvider(osrm)

    if redis is None:
        logger.warning("routing_cache_disabled", detail="no redis; using osrm without cache")
        return MeteredRoutingProvider(osrm)
    # Metering wraps the cache, not the other way round: a cache hit is an answer the
    # system served, and counting only the misses would report a 0% hit rate.
    return MeteredRoutingProvider(
        CachedRoutingProvider(osrm, redis, ttl_seconds=settings.routing_cache_ttl_seconds)
    )


def build_bulk_eta_service(
    settings: Settings,
    clock: Clock,
    redis: RedisLike | None = None,
    learned: LearnedSpeeds | None = None,
) -> EtaService:
    """An ETA service for callers that ask for **matrices** - the optimizer.

    CLAUDE.md hard rule 7: "Bulk callers (simulator, optimizer) always use `approx`" against
    the public OSRM, whose shared budget is one request a second and which is not for
    batch traffic. Against our own OSRM there is no such limit, so the configured provider
    is used and the optimizer gets real road times.
    """
    if (
        settings.routing_provider is not RoutingProviderName.approx
        and host_of(settings.osrm_url) in PUBLIC_OSM_HOSTS
    ):
        approx = ApproxRoutingProvider(clock, ApproxConfig(), learned)
        return EtaService(MeteredRoutingProvider(approx), clock)
    return EtaService(build_routing_provider(settings, clock, redis, learned), clock)


def build_learned_speeds(
    settings: Settings, clock: Clock, sessions: async_sessionmaker[AsyncSession]
) -> LearnedSpeeds | None:
    """The learned-speed view for this process, or `None` when the feature is off (B37)."""
    if not settings.speed_profile_enabled:
        return None
    return LearnedSpeeds(
        clock,
        database_loader(sessions, settings.speed_profile_min_samples),
        timedelta(seconds=settings.speed_profile_refresh_seconds),
    )


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
