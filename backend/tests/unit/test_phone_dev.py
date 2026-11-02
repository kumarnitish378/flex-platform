"""`make phone-dev` (scripts/phone_dev.py): what a phone on the Wi-Fi is told."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.settings import AppEnv, Settings

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "phone_dev.py"
_spec = importlib.util.spec_from_file_location("phone_dev", SCRIPT)
assert _spec and _spec.loader
phone_dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(phone_dev)

LAN = "192.168.1.42"


def test_an_explicit_host_wins_over_detection() -> None:
    assert phone_dev.lan_ip(LAN) == LAN


def test_detection_returns_a_non_loopback_address_or_the_hostname_fallback() -> None:
    assert phone_dev.lan_ip() != ""


def test_the_backend_is_told_to_hand_the_phone_the_lan_address() -> None:
    env = phone_dev.backend_environment(LAN, {})

    assert env["APP_ENV"] == "dev" and env["AUTH_TEST_LOGIN"] == "true"
    settings = Settings(
        app_env=env["APP_ENV"],
        auth_test_login=env["AUTH_TEST_LOGIN"] == "true",
        mqtt_public_host=env["MQTT_PUBLIC_HOST"],
        mqtt_public_port=int(env["MQTT_PUBLIC_PORT"]),
        mqtt_host=env["MQTT_HOST"],
        database_url="postgresql+asyncpg://t:t@localhost:5432/t",
    )
    # What /driver/duty returns to the phone, versus what the server itself connects to.
    assert settings.app_env is AppEnv.dev
    assert settings.broker_host_for_devices == LAN
    assert settings.broker_port_for_devices == 1883
    assert settings.mqtt_host == "localhost"


def test_the_dart_defines_name_every_value_the_app_reads() -> None:
    defines = phone_dev.dart_defines(LAN, tiles_ready=True)
    names = {item.removeprefix("--dart-define=").split("=")[0] for item in defines}

    assert names == {
        "API_BASE_URL",
        "MQTT_HOST",
        "MQTT_PORT",
        "TILES_URL",
        "OSM_CONTACT_EMAIL",
        "APP_TESTING",
    }
    assert f"--dart-define=API_BASE_URL=http://{LAN}:8000/api/v1" in defines
    assert f"--dart-define=MQTT_HOST={LAN}" in defines


def test_without_prepared_map_data_the_phone_uses_the_public_tiles() -> None:
    assert phone_dev.urls(LAN, tiles_ready=False)["tiles"].startswith("https://tile.openstreetmap")
    assert phone_dev.urls(LAN, tiles_ready=True)["tiles"].startswith(f"http://{LAN}:8081/")
