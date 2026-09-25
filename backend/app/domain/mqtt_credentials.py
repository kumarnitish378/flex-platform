"""Mosquitto password and ACL file generation (B11).

Pure functions over data: no database, no filesystem, no broker. The formats are exact,
so they are worth testing on their own — a subtly wrong ACL line fails open, letting one
vehicle publish as another, and that is not something to discover in production.

**Password file** (`mosquitto_passwd` format, verified against Mosquitto 2.1.2):

    username:$7$<iterations>$<base64 salt>$<base64 hash>

`$7$` is PBKDF2-HMAC-SHA512 with a 64-byte salt and a 64-byte derived key.

**ACL file** follows `mqtt-topics.md` (Access control): a vehicle may publish only to its
own `gps` and `status` topics and subscribe only to its own `cmd`; the ingestor reads
across all of them.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass

#: What Mosquitto 2.x writes. Matching it exactly is the point.
HASH_SCHEME = 7
ITERATIONS = 1000
SALT_BYTES = 64
KEY_BYTES = 64

TOPIC_ROOT = "sc/v1"
PASSWORD_BYTES = 24


@dataclass(frozen=True, slots=True)
class VehicleCredential:
    """One vehicle's broker identity. `password` exists only at issue time."""

    vehicle_id: str
    operator_id: str
    username: str
    password_hash: str


def generate_password() -> str:
    """A credential the driver app never types, so it can be long and opaque."""
    return secrets.token_urlsafe(PASSWORD_BYTES)


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash in Mosquitto's `$7$` format."""
    salt = salt if salt is not None else secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, ITERATIONS, KEY_BYTES)
    return (
        f"${HASH_SCHEME}${ITERATIONS}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"
    )


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored `$7$` hash.

    Mosquitto does the real check; this exists so our own tests and tooling can confirm
    that what we wrote is what we meant.
    """
    try:
        _, scheme, iterations, salt_b64, hash_b64 = stored.split("$")
        if int(scheme) != HASH_SCHEME:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha512", password.encode("utf-8"), salt, int(iterations), len(expected)
    )
    return secrets.compare_digest(derived, expected)


def username_for(vehicle_id: str) -> str:
    """The broker username for a vehicle.

    The vehicle id itself, so the ACL can be written with `%u` patterns and a credential
    can never be used to publish as a different cab.
    """
    return f"veh-{vehicle_id}"


def vehicle_id_from_username(username: str) -> str | None:
    return username[4:] if username.startswith("veh-") else None


def topic_prefix(operator_id: str, vehicle_id: str) -> str:
    return f"{TOPIC_ROOT}/op/{operator_id}/veh/{vehicle_id}"


def build_password_file(
    credentials: list[VehicleCredential], ingestor: tuple[str, str] | None = None
) -> str:
    """`username:hash` per line, sorted so the file only changes when the data does."""
    lines = [f"{c.username}:{c.password_hash}" for c in credentials]
    if ingestor is not None:
        lines.append(f"{ingestor[0]}:{ingestor[1]}")
    return "\n".join(sorted(lines)) + "\n"


def build_acl_file(
    credentials: list[VehicleCredential], ingestor_username: str = "ingestor"
) -> str:
    """The ACL from `mqtt-topics.md`.

    Per-vehicle `user` blocks rather than one `pattern` rule: patterns would let any
    authenticated client publish under its own name, but the topic also contains the
    operator id, and only this table knows which vehicle belongs to which operator.
    """
    lines: list[str] = [
        "# GENERATED FILE - do not edit.",
        "# Written from the vehicle registry by the backend (task B11).",
        "# Rules: mqtt-topics.md, Access control.",
        "",
        "# No anonymous access: every client is a known vehicle or the ingestor.",
        "topic read $SYS/broker/uptime",
        "",
    ]

    for credential in sorted(credentials, key=lambda c: c.username):
        prefix = topic_prefix(credential.operator_id, credential.vehicle_id)
        lines += [
            f"user {credential.username}",
            f"topic write {prefix}/gps",
            f"topic write {prefix}/status",
            f"topic read {prefix}/cmd",
            "",
        ]

    lines += [
        f"user {ingestor_username}",
        f"topic read {TOPIC_ROOT}/op/+/veh/+/gps",
        f"topic read {TOPIC_ROOT}/op/+/veh/+/status",
        f"topic write {TOPIC_ROOT}/op/+/veh/+/cmd",
        "",
    ]
    return "\n".join(lines)
