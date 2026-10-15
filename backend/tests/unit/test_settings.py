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
        jwt_secret="a-real-secret-long-enough-for-hs256-0123",
        database_url=GOOD_DB,
        # Defaults point at the public OSM servers, which require a contact address
        # in production (ADR-0010 rule 4).
        osm_contact_email="ops@example.com",
    )
    assert settings.app_env is AppEnv.prod
    assert settings.is_sim is False


def test_short_jwt_secret_is_rejected_outside_dev() -> None:
    """RFC 7518 §3.2: an HS256 key shorter than the hash output weakens the signature."""
    with pytest.raises(ValidationError, match="at least 32 bytes"):
        Settings(
            app_env="prod",
            jwt_secret="too-short",
            database_url=GOOD_DB,
            osm_contact_email="ops@example.com",
        )


def test_short_jwt_secret_is_allowed_in_dev() -> None:
    """Dev keeps its friction low; the guard is for staging and prod."""
    assert Settings(app_env="dev", jwt_secret="short", database_url=GOOD_DB).app_env == "dev"


def test_staging_also_requires_a_real_secret() -> None:
    with pytest.raises(ValidationError, match="real secret"):
        Settings(app_env="staging", database_url=GOOD_DB, osm_contact_email="ops@example.com")


def test_secret_is_not_exposed_by_repr() -> None:
    settings = Settings(jwt_secret="super-secret-value", database_url=GOOD_DB)
    assert "super-secret-value" not in repr(settings)
    assert settings.jwt_secret.get_secret_value() == "super-secret-value"


# --- what a driver's phone is told (R01) -------------------------------------


def test_device_broker_address_falls_back_to_the_internal_one() -> None:
    """Correct for local development, where they are the same machine."""
    settings = Settings(database_url=GOOD_DB, mqtt_host="localhost", mqtt_port=1883)

    assert settings.broker_host_for_devices == "localhost"
    assert settings.broker_port_for_devices == 1883
    assert settings.mqtt_public_tls is False


def test_a_deployment_tells_devices_the_public_address_not_its_own() -> None:
    """The defect this exists to prevent.

    Inside a deployment `MQTT_HOST` is a compose service name on an unpublished
    plaintext port. Handing that to a phone - which is what `/driver/duty` did until
    this was found by running the staging stack - tells every driver to connect to a
    host that does not resolve, in clear text, and GPS never starts.
    """
    settings = Settings(
        database_url=GOOD_DB,
        mqtt_host="mosquitto",
        mqtt_port=1883,
        mqtt_public_host="staging.example.com",
        mqtt_public_port=8883,
        mqtt_public_tls=True,
    )

    # What this process uses to reach the broker.
    assert settings.mqtt_host == "mosquitto"
    # What a phone is told.
    assert settings.broker_host_for_devices == "staging.example.com"
    assert settings.broker_port_for_devices == 8883
    assert settings.mqtt_public_tls is True
