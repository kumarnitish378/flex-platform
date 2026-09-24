"""Settings validation — the guards that stop a misconfigured process from starting."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.settings import AppEnv, Settings

GOOD_DB = "postgresql+asyncpg://smartcab:smartcab@localhost:5432/smartcab"


def test_defaults_are_development_safe() -> None:
    settings = Settings(database_url=GOOD_DB)
    assert settings.app_env is AppEnv.dev
    assert settings.otp_provider == "console"
    assert settings.push_provider == "log"
    assert settings.simctl_enabled is False


def test_sync_database_driver_is_rejected() -> None:
    with pytest.raises(ValidationError, match="asyncpg"):
        Settings(database_url="postgresql://smartcab:smartcab@localhost:5432/smartcab")


def test_simctl_requires_sim_environment() -> None:
    """ADR-0008: /simctl/* must not exist outside APP_ENV=sim."""
    with pytest.raises(ValidationError, match="APP_ENV=sim"):
        Settings(app_env="dev", simctl_enabled=True, database_url=GOOD_DB)


def test_simctl_allowed_in_sim() -> None:
    settings = Settings(app_env="sim", simctl_enabled=True, database_url=GOOD_DB)
    assert settings.is_sim is True


def test_prod_rejects_the_placeholder_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(app_env="prod", database_url=GOOD_DB)


def test_prod_accepts_a_real_secret() -> None:
    settings = Settings(
        app_env="prod",
        jwt_secret="a-real-secret",
        database_url=GOOD_DB,
        # Defaults point at the public OSM servers, which require a contact address
        # in production (ADR-0010 rule 4).
        osm_contact_email="ops@example.com",
    )
    assert settings.app_env is AppEnv.prod
    assert settings.is_sim is False


def test_secret_is_not_exposed_by_repr() -> None:
    settings = Settings(jwt_secret="super-secret-value", database_url=GOOD_DB)
    assert "super-secret-value" not in repr(settings)
    assert settings.jwt_secret.get_secret_value() == "super-secret-value"
