"""Mosquitto password and ACL generation (B11).

The password format was verified against a real Mosquitto 2.1.2 by running
`mosquitto_passwd -b` in the container and reproducing its output byte for byte; the
vector below is that output. If this test ever fails, the broker will silently reject
every driver, so it is worth pinning.
"""

from __future__ import annotations

import base64

from app.domain.mqtt_credentials import (
    ITERATIONS,
    VehicleCredential,
    build_acl_file,
    build_password_file,
    generate_password,
    hash_password,
    topic_prefix,
    username_for,
    vehicle_id_from_username,
    verify_password,
)

# Captured from: mosquitto_passwd -b /tmp/pw testuser testpass  (Mosquitto 2.1.2)
KNOWN_SALT = base64.b64decode(
    "5J5ELve9xpzZn6jNI7sRQ8RYfRrN/i3qXhb24sWQ5XcblkwRX7gYx0Kk1+woNBzjSy7RZ18XGokUQtjmiaxcvA=="
)
KNOWN_HASH = (
    "$7$1000$5J5ELve9xpzZn6jNI7sRQ8RYfRrN/i3qXhb24sWQ5XcblkwRX7gYx0Kk1+woNBzjSy7RZ18XGokUQtjm"
    "iaxcvA==$ORZentv+Qs2hnCNe3VgnXFofCmrdbknJilLZ8ao62kFVEmFtBe/YwZfJxtba+zdxxHv7+hNt0Xm8n5t"
    "kQ2o31A=="
)


def credential(vehicle: str = "veh-1", operator: str = "op-1") -> VehicleCredential:
    return VehicleCredential(
        vehicle_id=vehicle,
        operator_id=operator,
        username=username_for(vehicle),
        password_hash=hash_password("secret"),
    )


# --- the hash format -------------------------------------------------------------


def test_hash_matches_mosquitto_byte_for_byte() -> None:
    """The whole feature rests on this: a different format means every login fails."""
    assert hash_password("testpass", KNOWN_SALT) == KNOWN_HASH


def test_verify_accepts_mosquittos_own_hash() -> None:
    assert verify_password("testpass", KNOWN_HASH)


def test_verify_rejects_the_wrong_password() -> None:
    assert not verify_password("wrong", KNOWN_HASH)


def test_the_scheme_and_iterations_are_pinned() -> None:
    assert hash_password("x").startswith(f"$7${ITERATIONS}$")


def test_each_hash_gets_a_fresh_salt() -> None:
    assert hash_password("same") != hash_password("same")


def test_both_hashes_of_one_password_still_verify() -> None:
    password = "same"
    assert verify_password(password, hash_password(password))
    assert verify_password(password, hash_password(password))


def test_a_malformed_hash_is_rejected_rather_than_raising() -> None:
    for broken in ("", "not-a-hash", "$7$", "$6$1000$aa$bb", "$7$x$y$z"):
        assert verify_password("x", broken) is False


def test_generated_passwords_are_long_and_unique() -> None:
    passwords = {generate_password() for _ in range(100)}
    assert len(passwords) == 100
    assert all(len(p) >= 30 for p in passwords)


# --- usernames and topics ----------------------------------------------------------


def test_the_username_is_derived_from_the_vehicle() -> None:
    assert username_for("abc") == "veh-abc"
    assert vehicle_id_from_username("veh-abc") == "abc"
    assert vehicle_id_from_username("ingestor") is None


def test_the_topic_prefix_matches_the_spec() -> None:
    """mqtt-topics.md: sc/v1/op/{operator_id}/veh/{vehicle_id}."""
    assert topic_prefix("op1", "veh1") == "sc/v1/op/op1/veh/veh1"


# --- the password file --------------------------------------------------------------


def test_password_file_has_one_line_per_credential() -> None:
    content = build_password_file([credential("a"), credential("b")])
    lines = content.strip().splitlines()
    assert len(lines) == 2
    assert all(line.count(":") == 1 for line in lines)


def test_password_file_is_sorted_so_it_only_changes_with_the_data() -> None:
    forwards = build_password_file([credential("a"), credential("b")])
    backwards = build_password_file([credential("b"), credential("a")])
    assert [line.split(":")[0] for line in forwards.splitlines()] == ["veh-a", "veh-b"]
    assert forwards.splitlines()[0].split(":")[0] == backwards.splitlines()[0].split(":")[0]


def test_the_ingestor_can_be_added() -> None:
    content = build_password_file([credential("a")], ingestor=("ingestor", "$7$x"))
    assert "ingestor:$7$x" in content


def test_an_empty_registry_still_produces_a_valid_file() -> None:
    assert build_password_file([]) == "\n"


# --- the ACL file ----------------------------------------------------------------------


def test_a_vehicle_may_publish_only_to_its_own_topics() -> None:
    acl = build_acl_file([credential("v1", "op1")])
    assert "user veh-v1" in acl
    assert "topic write sc/v1/op/op1/veh/v1/gps" in acl
    assert "topic write sc/v1/op/op1/veh/v1/status" in acl
    assert "topic read sc/v1/op/op1/veh/v1/cmd" in acl


def test_a_vehicle_gets_no_write_to_its_own_cmd_topic() -> None:
    """cmd is backend to device; a cab must not be able to command itself."""
    acl = build_acl_file([credential("v1", "op1")])
    assert "topic write sc/v1/op/op1/veh/v1/cmd" not in acl


def test_no_vehicle_is_granted_a_wildcard() -> None:
    """A single stray '+' here would let one cab publish as every other."""
    acl = build_acl_file([credential("v1", "op1"), credential("v2", "op1")])
    vehicle_block = acl.split("user ingestor")[0]
    assert "+" not in vehicle_block


def test_each_vehicle_gets_its_own_block() -> None:
    acl = build_acl_file([credential("v1", "op1"), credential("v2", "op2")])
    assert "user veh-v1" in acl and "user veh-v2" in acl
    assert "sc/v1/op/op1/veh/v1/gps" in acl
    assert "sc/v1/op/op2/veh/v2/gps" in acl
    # v1 must not appear under op2's tree.
    assert "sc/v1/op/op2/veh/v1/gps" not in acl


def test_the_ingestor_reads_everything_and_writes_only_commands() -> None:
    acl = build_acl_file([credential("v1", "op1")])
    tail = acl.split("user ingestor")[1]
    assert "topic read sc/v1/op/+/veh/+/gps" in tail
    assert "topic read sc/v1/op/+/veh/+/status" in tail
    assert "topic write sc/v1/op/+/veh/+/cmd" in tail
    assert "topic write sc/v1/op/+/veh/+/gps" not in tail


def test_the_acl_says_it_is_generated() -> None:
    """Whoever finds this file must know not to hand-edit it."""
    assert "GENERATED FILE" in build_acl_file([])


def test_an_empty_registry_still_grants_the_ingestor() -> None:
    assert "user ingestor" in build_acl_file([])
