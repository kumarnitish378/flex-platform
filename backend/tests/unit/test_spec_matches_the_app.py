"""`api-spec.yaml` and the app serve the same paths (CLAUDE.md hard rule 1).

The spec is the contract: change it first, regenerate the Dart client, then implement.
Drift in either direction is a quiet failure.

* **Promised and not served** is a lie to whoever reads the spec, and to the generated
  client, which gets a method that always 404s. `GET /dispatch/trips` sat in the spec
  unimplemented for three milestones while OQ-26 named it as a known cost.
* **Served and not promised** is worse in a different way: the endpoint exists, is
  reachable, and has no contract - so the app cannot call it, nothing generates a client
  for it, and nobody reviews its shape. `GET /driver/duty` was in that state.

Paths marked `x-phase: 2` in the spec are declared deliberately ahead of the code that
will serve them, the way the Phase 2 config keys are.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.core.settings import Settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = REPO_ROOT / "docs" / "03-architecture" / "api-spec.yaml"
API_PREFIX = "/api/v1"
METHODS = {"get", "post", "put", "patch", "delete"}

#: Served deliberately and correctly absent from the contract: operational endpoints that
#: are not part of the product's API. `/simctl/*` is sim-only (ADR-0008) and does appear
#: in the spec; health checks are infrastructure.
NOT_PRODUCT_API = ("/health", "/docs", "/openapi", "/redoc")


def declared() -> set[tuple[str, str]]:
    """Paths the spec promises, excluding those explicitly deferred to Phase 2."""
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    found: set[tuple[str, str]] = set()
    for path, item in (spec.get("paths") or {}).items():
        if item.get("x-phase") == 2:
            continue
        found |= {(method.upper(), path) for method in item if method.lower() in METHODS}
    return found


def served() -> set[tuple[str, str]]:
    """Paths the app actually serves, from its own generated OpenAPI.

    Generated rather than walked: `app.routes` keeps included routers as opaque objects
    in this FastAPI version, so walking it silently found four routes out of fifty-one -
    an audit that quietly sees nothing is worse than no audit.
    """
    app = create_app(
        settings=Settings(
            app_env="sim",
            database_url="postgresql+asyncpg://unused:unused@localhost/unused",
            jwt_secret="spec-audit-only-secret-0123456789",
            simctl_enabled=True,
        )
    )
    return {
        (method.upper(), path.removeprefix(API_PREFIX))
        for path, item in app.openapi()["paths"].items()
        for method in item
        if method.lower() in METHODS and not path.startswith(NOT_PRODUCT_API)
    }


def normalise(path: str) -> str:
    """`/trips/{trip_id}` and `/trips/{id}` name the same endpoint."""
    return re.sub(r"\{[^}]+\}", "{}", path)


def test_every_promised_path_is_served() -> None:
    missing = sorted(
        (method, path)
        for method, path in declared()
        if (method, normalise(path)) not in {(m, normalise(p)) for m, p in served()}
    )

    assert not missing, (
        f"the spec promises these and the app does not serve them: {missing}. "
        "Implement them, or mark the path `x-phase: 2` if it is deliberately ahead of "
        "the code. The generated client turns a promise into a method that 404s."
    )


def test_every_served_path_is_promised() -> None:
    extra = sorted(
        (method, path)
        for method, path in served()
        if (method, normalise(path)) not in {(m, normalise(p)) for m, p in declared()}
    )

    assert not extra, (
        f"the app serves these and the spec does not describe them: {extra}. "
        "The contract is the spec (hard rule 1) - an endpoint with no contract cannot be "
        "called by the app, because nothing generates a client for it."
    )


def test_the_audit_sees_a_real_app() -> None:
    """Both assertions above pass vacuously if either side comes back empty."""
    assert len(declared()) > 40
    assert len(served()) > 40
    assert ("POST", "/ride-requests") in served()
