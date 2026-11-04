"""The public edge serves the API and nothing else (R01).

`/metrics` is unauthenticated by design: Prometheus has no token, and giving it one
means a long-lived credential sitting in a scrape config where it will be copied. The
whole safety argument therefore rests on it never being reachable from outside the box,
and `tests/integration/test_permissions.py` exempts it from the permission harness on
exactly that promise.

A promise kept only by a comment in a Caddyfile is a promise that gets broken by the
next person adding a route. This reads the Caddyfile the deployment actually uses and
fails if it ever starts proxying something it should not.

It is a unit test, not an integration test, because it parses a file - no container and
no network. That is what makes it run on every PR.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CADDYFILE = Path(__file__).resolve().parents[2].parent / "infra" / "caddy" / "Caddyfile"

#: Paths the edge is allowed to pass through to the application.
ALLOWED_PREFIXES = ("/api/", "/ws", "/health/")

#: Paths that must never be reachable from the public internet, and why.
FORBIDDEN = {
    "/metrics": (
        "unauthenticated by design; exempted from the permission harness on the "
        "promise that it is unreachable from outside"
    ),
    "/docs": "an API explorer on a system under test is an invitation",
    "/openapi.json": "the contract is in the repository, not on the public edge",
    "/redoc": "same as /docs",
}


@pytest.fixture(scope="module")
def caddyfile() -> str:
    assert CADDYFILE.exists(), f"the deployment's Caddyfile is missing: {CADDYFILE}"
    return CADDYFILE.read_text(encoding="utf-8")


def handled_paths(text: str) -> list[str]:
    """Every path in a `handle`, `handle_path`, `route` or `@matcher path` directive.

    Comments are stripped first, so a path that only appears in the explanation of why
    it is *not* served does not read as a route.
    """
    without_comments = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )
    paths: list[str] = []
    for directive in re.finditer(
        r"^\s*(?:handle|handle_path|route|@\w+\s+path)\s+([^\n{]*)",
        without_comments,
        re.MULTILINE,
    ):
        paths.extend(token for token in directive.group(1).split() if token.startswith("/"))
    return paths


def test_the_caddyfile_proxies_only_allowed_prefixes(caddyfile: str) -> None:
    for path in handled_paths(caddyfile):
        assert path.startswith(ALLOWED_PREFIXES), (
            f"the edge handles {path!r}, which is outside the allow-list "
            f"{ALLOWED_PREFIXES}. Add it deliberately, or remove it."
        )


@pytest.mark.parametrize(("path", "reason"), sorted(FORBIDDEN.items()))
def test_forbidden_paths_are_not_served(caddyfile: str, path: str, reason: str) -> None:
    served = handled_paths(caddyfile)
    assert path not in served, f"{path} must not be reachable from the edge: {reason}"


def test_the_api_and_the_websocket_are_served(caddyfile: str) -> None:
    """The inverse guard: a parser that finds nothing would pass every test above."""
    served = handled_paths(caddyfile)
    assert "/api/*" in served, "the app cannot reach the API"
    assert "/ws" in served, "the realtime hub is not proxied; live tracking would not work"


def test_prometheus_scrapes_the_api_internally(caddyfile: str) -> None:
    """If /metrics is not public, Prometheus must reach it over the compose network.

    Otherwise the dashboards are blank and nobody notices until an incident.
    """
    prometheus = CADDYFILE.parent.parent / "prometheus" / "prometheus.yml"
    config = prometheus.read_text(encoding="utf-8")
    assert "api:8000" in config, "Prometheus must scrape the API by compose service name"
    assert "ingestor:9101" in config, "the GPS counters live in the ingestor process"
    assert "worker:9102" in config, "the sweep counters live in the worker process"


def test_the_api_site_refuses_anything_it_does_not_explicitly_handle(caddyfile: str) -> None:
    """The allow-list only holds if there is a catch-all behind it.

    Caddy falls through unmatched requests, so a site block with handlers and no final
    `handle { respond 404 }` serves nothing for `/metrics` *today* and would serve it
    the moment somebody adds a top-level `reverse_proxy`. The catch-all is what makes
    "only these paths" a property of the file rather than of its current contents, and
    it is what ADR-0025 leans on.
    """
    without_comments = "\n".join(
        line for line in caddyfile.splitlines() if not line.strip().startswith("#")
    )
    # A `handle` with no matcher is the catch-all; it must answer rather than proxy.
    catch_all = re.search(
        r"^\s*handle\s*\{(?P<body>[^}]*)\}", without_comments, re.MULTILINE | re.DOTALL
    )
    assert catch_all is not None, (
        "the API site has no catch-all `handle { ... }`. Without it, every path that is "
        "not explicitly handled falls through to whatever is declared at site level."
    )
    body = catch_all.group("body")
    assert "respond" in body, f"the catch-all must respond, not proxy: {body.strip()!r}"
    assert "404" in body, f"the catch-all should answer 404: {body.strip()!r}"
    assert "reverse_proxy" not in body, "the catch-all must not proxy to the application"
