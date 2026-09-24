"""M01 acceptance: a default run must make zero requests to a public OSM host.

This is the rule that protects donated infrastructure from a simulator that issues
thousands of route lookups per run (ADR-0010 rule 6). Two layers are checked: the network
really stays silent, and pointing the simulator at a public host fails loudly rather than
quietly working.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from sim.cli import main
from sim.engine import Engine
from sim.geo import LatLng
from sim.routing import (
    PUBLIC_OSM_HOSTS,
    ApproxRouting,
    OsrmRouting,
    PublicServerRefusedError,
    build_routing,
)
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
NOW = datetime(2026, 10, 5, 6, 30, tzinfo=UTC)
ORIGIN = LatLng(28.5703, 77.3218)
DESTINATION = LatLng(28.5123, 77.3910)


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Fail the test if anything opens an HTTP connection."""
    attempted: list[str] = []

    def forbid(self: object, *args: object, **kwargs: object) -> None:
        attempted.append(str(args[0]) if args else "unknown")
        raise AssertionError(f"the simulator made an HTTP request: {attempted[-1]}")

    monkeypatch.setattr(httpx.Client, "get", forbid)
    monkeypatch.setattr(httpx.Client, "request", forbid)
    monkeypatch.setattr(httpx.Client, "send", forbid)
    return attempted


def test_default_run_makes_no_http_requests(no_network: list[str]) -> None:
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    engine = Engine(scenario)
    summary = engine.run()
    assert summary.routing == "approx"
    assert no_network == []


def test_default_cli_run_makes_no_http_requests(no_network: list[str]) -> None:
    assert main(["run", str(SCENARIOS / "smoke_tiny.yaml")]) == 0
    assert no_network == []


def test_many_routes_make_no_http_requests(no_network: list[str]) -> None:
    """The realistic shape of the risk: thousands of lookups in one run."""
    routing = ApproxRouting()
    for _ in range(5000):
        routing.route(ORIGIN, DESTINATION, NOW)
    assert no_network == []


@pytest.mark.parametrize("host", sorted(PUBLIC_OSM_HOSTS))
def test_public_hosts_are_refused(host: str) -> None:
    with pytest.raises(PublicServerRefusedError, match="must not call the public OSM server"):
        OsrmRouting(f"https://{host}")


def test_public_host_refused_with_a_path_and_port() -> None:
    with pytest.raises(PublicServerRefusedError):
        OsrmRouting("https://router.project-osrm.org:443/route/v1")


def test_self_hosted_osrm_is_allowed() -> None:
    routing = OsrmRouting("http://localhost:5000")
    assert routing.name == "osrm"
    routing.close()


def test_build_routing_defaults_to_approx() -> None:
    assert build_routing("approx").name == "approx"


def test_build_routing_osrm_requires_a_url() -> None:
    with pytest.raises(PublicServerRefusedError, match="self-hosted"):
        build_routing("osrm", None)


def test_build_routing_refuses_a_public_url() -> None:
    with pytest.raises(PublicServerRefusedError):
        build_routing("osrm", "https://router.project-osrm.org")
