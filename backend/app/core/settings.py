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

    # --- notifications ------------------------------------------------------
    push_provider: PushProvider = PushProvider.log

    # --- simulator ----------------------------------------------------------
    simctl_enabled: bool = False

    # --- observability ------------------------------------------------------
    log_level: str = "INFO"
    log_json: bool = True

    @field_validator("database_url")
    @classmethod
    def _require_async_driver(cls, value: str) -> str:
        # A sync driver here fails much later and confusingly, inside the first request.
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use the postgresql+asyncpg:// driver")
        return value

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        if self.app_env is AppEnv.prod:
            if self.jwt_secret.get_secret_value() == "change-me-random-64-bytes":
                raise ValueError("JWT_SECRET must be set to a real secret in prod")
            if self.simctl_enabled:
                raise ValueError("SIMCTL_ENABLED must be false outside APP_ENV=sim")
        # /simctl/* exists only in sim (ADR-0008); enforce it here rather than trusting config.
        if self.simctl_enabled and self.app_env is not AppEnv.sim:
            raise ValueError("SIMCTL_ENABLED requires APP_ENV=sim")
        return self

    @property
    def is_sim(self) -> bool:
        return self.app_env is AppEnv.sim


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings. Cached so the environment is read once."""
    return Settings()
