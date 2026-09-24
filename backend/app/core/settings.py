"""Application settings, loaded from the environment (see `.env.example`).

Business numbers never live here — they come from `ConfigService` per operator
(`allocation-rules.md` §1, CLAUDE.md hard rule 4). This module holds only deployment
wiring: URLs, credentials, TTLs and provider selection.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    dev = "dev"
    sim = "sim"
    staging = "staging"
    prod = "prod"


class OtpProvider(StrEnum):
    console = "console"
    sms = "sms"


class PushProvider(StrEnum):
    log = "log"
    fcm = "fcm"
    ntfy = "ntfy"


class RoutingProviderName(StrEnum):
    """Which routing implementation to build (ADR-0010 rule 2)."""

    osrm = "osrm"
    approx = "approx"
    cached_osrm = "cached_osrm"


class GeocodingProviderName(StrEnum):
    """Phase 1 ships `none`; `nominatim` is self-hosted only (ADR-0010 A1)."""

    none = "none"
    nominatim = "nominatim"


# Hosts that are donated OSM infrastructure. Nominatim's usage policy forbids
# vehicle-tracking applications outright, so it is rejected rather than rate-limited.
# RFC 7518 §3.2: HS256 keys should be at least as long as the hash output.
MIN_JWT_SECRET_BYTES = 32

PUBLIC_NOMINATIM_HOSTS = frozenset({"nominatim.openstreetmap.org", "nominatim.osm.org"})
PUBLIC_OSM_HOSTS = frozenset(
    {
        "router.project-osrm.org",
        "tile.openstreetmap.org",
        "a.tile.openstreetmap.org",
        "b.tile.openstreetmap.org",
        "c.tile.openstreetmap.org",
        *PUBLIC_NOMINATIM_HOSTS,
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = AppEnv.dev

    # --- storage / transport ------------------------------------------------
    database_url: str = "postgresql+asyncpg://smartcab:smartcab@localhost:5432/smartcab"
    redis_url: str = "redis://localhost:6379/0"
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883

    # --- auth ---------------------------------------------------------------
    jwt_secret: SecretStr = SecretStr("change-me-random-64-bytes")
    access_token_ttl_seconds: int = Field(default=900, ge=60)
    refresh_token_ttl_days: int = Field(default=30, ge=1)
    otp_provider: OtpProvider = OtpProvider.console

    # --- map services (ADR-0010) -------------------------------------------
    # URLs are ALWAYS read from here, never written in code (hard rule 7).
    routing_provider: RoutingProviderName = RoutingProviderName.cached_osrm
    geocoding_provider: GeocodingProviderName = GeocodingProviderName.none
    osrm_url: str = "https://router.project-osrm.org"
    tiles_url: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    nominatim_url: str | None = None

    osm_user_agent: str = "flex-platform/0.1"
    osm_contact_email: str = ""

    osm_rate_limit_per_second: float = Field(default=1.0, gt=0, le=50)
    routing_cache_ttl_seconds: int = Field(default=900, ge=0)
    osm_request_timeout_seconds: float = Field(default=5.0, gt=0, le=60)

    # --- notifications ------------------------------------------------------
    push_provider: PushProvider = PushProvider.log

    # --- simulator ----------------------------------------------------------
    simctl_enabled: bool = False

    # --- observability ------------------------------------------------------
    log_level: str = "INFO"
    log_json: bool = True

    @field_validator("osrm_url", "tiles_url")
    @classmethod
    def _require_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("must be an http(s) URL")
        return value.rstrip("/") if not value.endswith("}") else value

    @field_validator("nominatim_url")
    @classmethod
    def _reject_public_nominatim(cls, value: str | None) -> str | None:
        """ADR-0010 A1: the public Nominatim is off limits for this product.

        Its usage policy forbids vehicle-tracking applications and asks that no personal
        data be submitted; employee home locations are personal data. This is categorical,
        so it fails at startup rather than being rate-limited at runtime.
        """
        if not value:
            return None
        host = host_of(value)
        if host in PUBLIC_NOMINATIM_HOSTS:
            raise ValueError(
                f"NOMINATIM_URL must not point at the public Nominatim ({host}). "
                "Its usage policy forbids vehicle-tracking applications (ADR-0010 A1). "
                "Use GEOCODING_PROVIDER=none, or a self-hosted instance (task I02c)."
            )
        return value.rstrip("/")

    @field_validator("database_url")
    @classmethod
    def _require_async_driver(cls, value: str) -> str:
        # A sync driver here fails much later and confusingly, inside the first request.
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use the postgresql+asyncpg:// driver")
        return value

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        if self.app_env in (AppEnv.staging, AppEnv.prod):
            secret = self.jwt_secret.get_secret_value()
            if secret == "change-me-random-64-bytes":
                raise ValueError("JWT_SECRET must be set to a real secret outside dev")
            # RFC 7518 §3.2: an HMAC key shorter than the hash output (32 bytes for
            # SHA-256) weakens the signature. PyJWT warns; we refuse.
            if len(secret.encode()) < MIN_JWT_SECRET_BYTES:
                raise ValueError(
                    f"JWT_SECRET must be at least {MIN_JWT_SECRET_BYTES} bytes "
                    "(RFC 7518 §3.2 for HS256)"
                )
            if self.simctl_enabled:
                raise ValueError("SIMCTL_ENABLED must be false outside APP_ENV=sim")
        # /simctl/* exists only in sim (ADR-0008); enforce it here rather than trusting config.
        if self.simctl_enabled and self.app_env is not AppEnv.sim:
            raise ValueError("SIMCTL_ENABLED requires APP_ENV=sim")

        if self.geocoding_provider is GeocodingProviderName.nominatim and not self.nominatim_url:
            raise ValueError("GEOCODING_PROVIDER=nominatim requires a self-hosted NOMINATIM_URL")

        # The OSM usage policy requires a contact address in the User-Agent. Anonymous
        # traffic gets blocked, so refuse to start rather than fail mysteriously later.
        needs_contact = self.uses_public_osm and self.app_env in (AppEnv.staging, AppEnv.prod)
        if needs_contact and not self.osm_contact_email:
            raise ValueError(
                "OSM_CONTACT_EMAIL is required when calling public OSM servers (ADR-0010 rule 4)"
            )
        return self

    @property
    def is_sim(self) -> bool:
        return self.app_env is AppEnv.sim

    @property
    def uses_public_osm(self) -> bool:
        """True when any configured map URL is donated OSM infrastructure."""
        return any(
            host_of(url) in PUBLIC_OSM_HOSTS
            for url in (self.osrm_url, self.tiles_url, self.nominatim_url or "")
            if url
        )

    @property
    def user_agent(self) -> str:
        """Identifying User-Agent required on every request to a public OSM server.

        Format from ADR-0010 A2: `flex-platform/<version> (contact: <email>)`.
        """
        if self.osm_contact_email:
            return f"{self.osm_user_agent} (contact: {self.osm_contact_email})"
        return self.osm_user_agent


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings. Cached so the environment is read once."""
    return Settings()


def host_of(url: str) -> str:
    """Hostname of a URL, lowercased. Tolerates the `{z}/{x}/{y}` tile template."""
    from urllib.parse import urlsplit

    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""
