"""The generated ACL really does stop one cab publishing as another (B11 acceptance).

This talks to a real Mosquitto. It is opt-in — `MQTT_ACL_TEST=1` — because it
**reconfigures the shared dev broker**: it writes a generated password and ACL file into
`infra/mosquitto/config/generated/`, points Mosquitto at them, turns anonymous access
off, reloads, and puts everything back afterwards. Running that silently inside an
ordinary `make test` would be rude.

Run it with:

    make up
    MQTT_ACL_TEST=1 python -m pytest tests/integration/test_mqtt_acl_live.py

Denial is asserted behaviourally rather than by reading a return code: Mosquitto drops an
unauthorised publish silently at QoS 0, so the check is that a subscriber never sees the
message. That is also the property that actually matters.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.domain.mqtt_credentials import (
    VehicleCredential,
    build_acl_file,
    build_password_file,
    hash_password,
    topic_prefix,
    username_for,
)

paho = pytest.importorskip("paho.mqtt.client", reason="paho-mqtt is a dev dependency")

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "infra" / "mosquitto" / "config"
GENERATED_DIR = CONFIG_DIR / "generated"
MAIN_CONF = CONFIG_DIR / "mosquitto.conf"
CONTAINER = "smartcab-mosquitto"

HOST = os.environ.get("MQTT_HOST", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))

OPERATOR = "op-live"
VEHICLE_A = "veh-a-" + uuid.uuid4().hex[:8]
VEHICLE_B = "veh-b-" + uuid.uuid4().hex[:8]
PASSWORD_A = "password-for-a"
PASSWORD_B = "password-for-b"
INGESTOR_PASSWORD = "password-for-ingestor"

enabled = pytest.mark.skipif(
    os.environ.get("MQTT_ACL_TEST") != "1",
    reason=(
        "reconfigures the shared dev broker; run deliberately with MQTT_ACL_TEST=1 after `make up`"
    ),
)


def docker() -> str | None:
    found = shutil.which("docker")
    if found:
        return found
    candidate = Path.home() / "AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe"
    return str(candidate) if candidate.exists() else None


def _read(path: Path) -> str:
    """Read without newline translation.

    `Path.read_text(newline=...)` only exists from Python 3.13, and CI runs 3.12.
    """
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write(path: Path, content: str) -> None:
    """Write without newline translation, so files round-trip byte for byte."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def reload_broker() -> None:
    """SIGHUP makes Mosquitto reread its password and ACL files."""
    binary = docker()
    assert binary, "docker is needed to signal the broker"
    subprocess.run([binary, "kill", "-s", "HUP", CONTAINER], check=True, capture_output=True)
    time.sleep(1.0)


@pytest.fixture
def configured_broker() -> Iterator[None]:
    """Point the broker at generated credentials, then put it back."""
    # No newline translation: Python would otherwise rewrite LF as CRLF on Windows and
    # leave the repo's config file "modified" with identical content.
    original_conf = _read(MAIN_CONF)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    credentials = [
        VehicleCredential(VEHICLE_A, OPERATOR, username_for(VEHICLE_A), hash_password(PASSWORD_A)),
        VehicleCredential(VEHICLE_B, OPERATOR, username_for(VEHICLE_B), hash_password(PASSWORD_B)),
    ]
    _write(
        GENERATED_DIR / "passwd",
        build_password_file(credentials, ingestor=("ingestor", hash_password(INGESTOR_PASSWORD))),
    )
    _write(GENERATED_DIR / "acl", build_acl_file(credentials))

    _write(
        MAIN_CONF,
        original_conf.replace("allow_anonymous true", "allow_anonymous false")
        .replace(
            "# password_file /mosquitto/config/passwd",
            "password_file /mosquitto/config/generated/passwd",
        )
        .replace("acl_file /mosquitto/config/acl", "acl_file /mosquitto/config/generated/acl"),
    )
    reload_broker()
    try:
        yield
    finally:
        _write(MAIN_CONF, original_conf)
        shutil.rmtree(GENERATED_DIR, ignore_errors=True)
        reload_broker()


def connect(username: str, password: str):  # type: ignore[no-untyped-def]
    client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=f"test-{uuid.uuid4().hex[:8]}")
    client.username_pw_set(username, password)
    client.connect(HOST, PORT, keepalive=10)
    client.loop_start()
    return client


@enabled
def test_a_vehicle_may_publish_to_its_own_topic(configured_broker: None) -> None:
    received: list[str] = []

    listener = connect("ingestor", INGESTOR_PASSWORD)
    listener.on_message = lambda c, u, m: received.append(m.topic)
    listener.subscribe("sc/v1/op/+/veh/+/gps", qos=1)
    time.sleep(0.5)

    publisher = connect(username_for(VEHICLE_A), PASSWORD_A)
    publisher.publish(f"{topic_prefix(OPERATOR, VEHICLE_A)}/gps", '{"v":1}', qos=1)
    time.sleep(1.0)

    publisher.loop_stop()
    listener.loop_stop()
    assert received == [f"{topic_prefix(OPERATOR, VEHICLE_A)}/gps"]


@enabled
def test_a_vehicle_cannot_publish_as_another_vehicle(configured_broker: None) -> None:
    """B11 acceptance: the ACL denies publishing to another vehicle's topic."""
    received: list[str] = []

    listener = connect("ingestor", INGESTOR_PASSWORD)
    listener.on_message = lambda c, u, m: received.append(m.topic)
    listener.subscribe("sc/v1/op/+/veh/+/gps", qos=1)
    time.sleep(0.5)

    impostor = connect(username_for(VEHICLE_A), PASSWORD_A)
    impostor.publish(f"{topic_prefix(OPERATOR, VEHICLE_B)}/gps", '{"v":1,"spoofed":true}', qos=1)
    time.sleep(1.0)

    impostor.loop_stop()
    listener.loop_stop()
    assert received == [], "vehicle A published onto vehicle B's topic"


@enabled
def test_an_unknown_client_cannot_connect(configured_broker: None) -> None:
    codes: list[int] = []
    client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="stranger")
    client.username_pw_set("veh-nobody", "guess")
    client.on_connect = lambda c, u, f, rc, p: codes.append(int(rc.value))
    client.connect_async(HOST, PORT, keepalive=10)
    client.loop_start()
    time.sleep(1.5)
    client.loop_stop()

    assert codes and codes[0] != 0, "an unknown username was accepted"


@enabled
def test_anonymous_access_is_refused_once_configured(configured_broker: None) -> None:
    codes: list[int] = []
    client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="anon")
    client.on_connect = lambda c, u, f, rc, p: codes.append(int(rc.value))
    client.connect_async(HOST, PORT, keepalive=10)
    client.loop_start()
    time.sleep(1.5)
    client.loop_stop()

    assert codes and codes[0] != 0, "anonymous access was still allowed"
