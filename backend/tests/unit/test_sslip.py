"""Staging addresses for a box with an IP and no domain (sslip.py), and the broker-cert check."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sslip = load("sslip")
broker_cert = load("check_broker_cert")


def test_a_public_address_becomes_one_dns_label_under_sslip_io() -> None:
    assert sslip.site_address("129.151.20.9") == "129-151-20-9.sslip.io"
    assert sslip.site_address(" 129.151.20.9 ") == "129-151-20-9.sslip.io"


def test_grafana_gets_a_label_in_front_that_resolves_to_the_same_address() -> None:
    assert sslip.monitoring_address("129.151.20.9") == "grafana.129-151-20-9.sslip.io"


def test_the_env_lines_are_what_the_staging_template_expects() -> None:
    lines = dict(line.split("=", 1) for line in sslip.env_lines("129.151.20.9").splitlines())
    assert lines == {
        "SITE_ADDRESS": "129-151-20-9.sslip.io",
        "MONITORING_ADDRESS": "grafana.129-151-20-9.sslip.io",
    }


@pytest.mark.parametrize(
    "bad",
    [
        "10.0.0.4",
        "192.168.1.36",
        "127.0.0.1",
        "169.254.1.1",
        "::1",
        "2001:db8::1",
        "example.com",
        "",
    ],
)
def test_private_loopback_ipv6_and_names_are_refused(bad: str) -> None:
    with pytest.raises(ValueError):
        sslip.site_address(bad)


def test_the_command_prints_or_explains(capsys: pytest.CaptureFixture[str]) -> None:
    assert sslip.main(["129.151.20.9"]) == 0
    assert "SITE_ADDRESS=129-151-20-9.sslip.io" in capsys.readouterr().out
    assert sslip.main(["10.0.0.4"]) == 1
    assert "not a public address" in capsys.readouterr().err
    assert sslip.main([]) == 2


def test_certificate_names_are_read_from_the_subject_alt_name() -> None:
    certificate = {
        "subjectAltName": (("DNS", "a.sslip.io"), ("IP Address", "1.2.3.4"), ("DNS", "b"))
    }
    assert broker_cert.names_in(certificate) == ["a.sslip.io", "b"]
    assert broker_cert.names_in({}) == []


def test_the_broker_certificate_is_the_one_caddy_obtained_for_site_address() -> None:
    """The SAN matches the phone's MQTT host because both are SITE_ADDRESS - keep it so."""
    compose = (ROOT / "infra" / "docker-compose.staging.yml").read_text("utf-8")
    assert "MQTT_PUBLIC_HOST: ${SITE_ADDRESS}" in compose
    assert 'pattern="*certificates*/$${SITE_ADDRESS}/$${SITE_ADDRESS}.crt"' in compose
