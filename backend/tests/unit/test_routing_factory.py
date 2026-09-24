"""Provider selection and the OSM policy guard rails (ADR-0010)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.clock import FakeClock
from app.core.settings import Settings
from app.modules.routing.approx import ApproxRoutingProvider
from app.modules.routing.cache import CachedRoutingProvider
from app.modules.routing.factory import (
    build_geocoding_provider,
    build_rate_limiter,
    build_routing_provider,
)
from app.modules.routing.geocoding import NoGeocodingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.rate_limit import RedisRateLimiter, UnlimitedRateLimiter
from app.modules.routing.types import GeocodingUnavailableError, RoutingProvider
from tests.fakes import FakeRedis

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
DB = "postgresql+asyncpg://test:test@localhost:5432/test"
PUBLIC_OSRM = "https://router.project-osrm.org"
SELF_HOSTED_OSRM = "http://localhost:5000"


def settings(**overrides: object) -> Settings:
    return Settings(database_url=DB, **overrides)  # type: ignore[arg-type]


def clock() -> FakeClock:
    return FakeClock(NOW)


def redis() -> FakeRedis:
    return FakeRedis(clock())


# --- provider selection ------------------------------------------------------


def test_approx_is_selected() -> None:
    provider = build_routing_provider(settings(routing_provider="approx"), clock(), redis())
    assert isinstance(provider, ApproxRoutingProvider)


def test_osrm_is_selected() -> None:
    provider = build_routing_provider(settings(routing_provider="osrm"), clock(), redis())
    assert isinstance(provider, OsrmRoutingProvider)


def test_cached_osrm_is_the_default() -> None:
    provider = build_routing_provider(settings(), clock(), redis())
    assert isinstance(provider, CachedRoutingProvider)


def test_every_provider_satisfies_the_protocol() -> None:
    for name in ("approx", "osrm", "cached_osrm"):
        provider = build_routing_provider(settings(routing_provider=name), clock(), redis())
        assert isinstance(provider, RoutingProvider)


def test_cached_degrades_to_plain_osrm_without_redis() -> None:
    provider = build_routing_provider(settings(routing_provider="cached_osrm"), clock(), None)
    assert isinstance(provider, OsrmRoutingProvider)


def test_approx_needs_no_redis() -> None:
    provider = build_routing_provider(settings(routing_provider="approx"), clock(), None)
    assert isinstance(provider, ApproxRoutingProvider)


# --- rate limiting -----------------------------------------------------------


def test_public_osrm_is_rate_limited() -> None:
    limiter = build_rate_limiter(settings(osrm_url=PUBLIC_OSRM), redis())
    assert isinstance(limiter, RedisRateLimiter)


def test_self_hosted_osrm_is_not_rate_limited() -> None:
    limiter = build_rate_limiter(settings(osrm_url=SELF_HOSTED_OSRM), redis())
    assert isinstance(limiter, UnlimitedRateLimiter)


async def test_public_osrm_without_redis_refuses_to_call_out() -> None:
    """No shared budget means no way to honour it, so we spend nothing."""
    limiter = build_rate_limiter(settings(osrm_url=PUBLIC_OSRM), None)
    assert await limiter.try_acquire("osrm") is False


# --- geocoding: the categorical rule -----------------------------------------


def test_default_geocoding_provider_is_none() -> None:
    assert isinstance(build_geocoding_provider(settings()), NoGeocodingProvider)


async def test_geocoding_search_is_unavailable_in_phase_1() -> None:
    provider = build_geocoding_provider(settings())
    with pytest.raises(GeocodingUnavailableError, match="map pin"):
        await provider.search("Sector 62 Noida")


async def test_reverse_geocoding_is_unavailable_in_phase_1() -> None:
    from app.domain.geo import LatLng

    provider = build_geocoding_provider(settings())
    with pytest.raises(GeocodingUnavailableError):
        await provider.reverse(LatLng(lat=28.57, lng=77.32))


@pytest.mark.parametrize(
    "url",
    [
        "https://nominatim.openstreetmap.org",
        "http://nominatim.openstreetmap.org/search",
        "https://NOMINATIM.OpenStreetMap.ORG",
        "https://nominatim.osm.org",
    ],
)
def test_public_nominatim_is_rejected_at_startup(url: str) -> None:
    """I02 acceptance: configuring the public Nominatim must fail, not be rate-limited.

    Its usage policy forbids vehicle-tracking applications outright (ADR-0010 A1).
    """
    with pytest.raises(ValidationError, match="public Nominatim"):
        settings(nominatim_url=url)


def test_self_hosted_nominatim_is_accepted() -> None:
    configured = settings(nominatim_url="http://localhost:8080", geocoding_provider="nominatim")
    assert configured.nominatim_url == "http://localhost:8080"


def test_nominatim_provider_requires_a_url() -> None:
    with pytest.raises(ValidationError, match="self-hosted NOMINATIM_URL"):
        settings(geocoding_provider="nominatim")


def test_nominatim_implementation_is_not_pretended_to_exist() -> None:
    configured = settings(geocoding_provider="nominatim", nominatim_url="http://localhost:8080")
    with pytest.raises(NotImplementedError, match="I02c"):
        build_geocoding_provider(configured)


# --- user agent --------------------------------------------------------------


def test_user_agent_includes_the_contact_address() -> None:
    configured = settings(osm_user_agent="flex-platform/0.1", osm_contact_email="ops@example.com")
    assert configured.user_agent == "flex-platform/0.1 (contact: ops@example.com)"


def test_contact_email_is_required_in_production_on_public_servers() -> None:
    with pytest.raises(ValidationError, match="OSM_CONTACT_EMAIL"):
        Settings(
            app_env="prod",
            jwt_secret="real-secret-long-enough-for-hs256-01",
            database_url=DB,
            osrm_url=PUBLIC_OSRM,
            osm_contact_email="",
        )


def test_production_on_self_hosted_needs_no_contact_email() -> None:
    configured = Settings(
        app_env="prod",
        jwt_secret="real-secret-long-enough-for-hs256-01",
        database_url=DB,
        osrm_url=SELF_HOSTED_OSRM,
        tiles_url="http://localhost:8081",
        osm_contact_email="",
    )
    assert configured.uses_public_osm is False


def test_public_host_detection() -> None:
    assert settings(osrm_url=PUBLIC_OSRM).uses_public_osm is True
    assert (
        settings(osrm_url=SELF_HOSTED_OSRM, tiles_url="http://localhost:8081").uses_public_osm
        is False
    )
