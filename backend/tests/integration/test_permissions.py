"""Route authorisation harness (B04).

`roles-and-permissions.md`: "Tests: every endpoint has at least one 'denied' test for a
role that must not access it."

The important test here is `test_every_route_declares_its_authorisation`. It walks every
registered route and fails if one declares neither a permission, nor `public_route()`,
nor `self_service_route()`. That is what stops a future endpoint shipping wide open
because someone forgot a dependency — the failure happens when the route is added, not
when it is exploited.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Role
from app.main import create_app
from app.modules.auth.dependencies import (
    is_public,
    is_self_service,
    permission_of,
    require,
)
from app.modules.auth.permissions import (
    ROLE_PERMISSIONS,
    Permission,
    has_permission,
    permissions_for,
)

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "permission-harness-secret-0123456789abcd"

# Paths outside the API contract: operational endpoints for the process manager.
OPERATIONAL_PATHS = frozenset({"/health/live", "/health/ready"})
# FastAPI's own documentation routes.
DOC_PATHS = frozenset({"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"})


def build_app() -> FastAPI:
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )
    return create_app(settings=settings, clock=FakeClock(NOW))


@dataclass(frozen=True)
class MountedRoute:
    """An APIRoute together with the full path it is served at."""

    path: str
    route: APIRoute

    @property
    def methods(self) -> set[str]:
        return self.route.methods or set()


def api_routes(app: FastAPI) -> Iterator[MountedRoute]:
    """Every APIRoute with its full path.

    FastAPI keeps included routers nested (`_IncludedRouter`) rather than flattening
    them, so the prefix has to be accumulated on the way down. Walking the real tree
    matters: an inspection that silently finds nothing would make this whole harness
    pass while checking no routes at all - which `test_the_harness_sees_the_routes`
    exists to catch.
    """

    def walk(routes: Iterable[object], prefix: str) -> Iterator[MountedRoute]:
        for route in routes:
            if isinstance(route, APIRoute):
                yield MountedRoute(prefix + route.path, route)
                continue
            included = getattr(route, "original_router", None)
            if included is not None:
                context = getattr(route, "include_context", None)
                sub_prefix = getattr(context, "prefix", "") or ""
                yield from walk(included.routes, prefix + sub_prefix)

    yield from walk(app.routes, "")


def declaration_for(mounted: MountedRoute) -> str | None:
    """ "permission:<name>", "public", "self-service", or None when undeclared."""
    for dependency in mounted.route.dependant.dependencies:
        call = dependency.call
        permission = permission_of(call)
        if permission is not None:
            return f"permission:{permission}"
        if is_public(call):
            return "public"
        if is_self_service(call):
            return "self-service"
    return None


# --- the harness --------------------------------------------------------------


def test_the_harness_sees_the_routes() -> None:
    """If this fails, every check below is vacuously passing."""
    routes = [r for r in api_routes(build_app()) if r.path not in DOC_PATHS]
    assert len(routes) >= 6, f"only found {len(routes)} routes"


def test_every_route_declares_its_authorisation() -> None:
    """B04 acceptance: a route with no declaration fails the build."""
    undeclared = [
        f"{sorted(mounted.methods)} {mounted.path}"
        for mounted in api_routes(build_app())
        if mounted.path not in DOC_PATHS
        and mounted.path not in OPERATIONAL_PATHS
        and declaration_for(mounted) is None
    ]
    assert not undeclared, (
        "These routes declare no permission, public_route() or self_service_route(). "
        "Add one - an endpoint with no declaration is an endpoint nobody authorised:\n  "
        + "\n  ".join(undeclared)
    )


def test_auth_endpoints_are_declared_as_expected() -> None:
    declarations = {
        (mounted.path, declaration_for(mounted))
        for mounted in api_routes(build_app())
        if mounted.path.startswith("/api/v1")
    }
    assert ("/api/v1/auth/otp/request", "public") in declarations
    assert ("/api/v1/auth/otp/verify", "public") in declarations
    assert ("/api/v1/auth/refresh", "public") in declarations
    assert ("/api/v1/auth/me", "self-service") in declarations
    assert ("/api/v1/devices", "self-service") in declarations


def test_public_routes_stay_a_short_list() -> None:
    """Making something public should be a visible, reviewable change."""
    public = {
        mounted.path for mounted in api_routes(build_app()) if declaration_for(mounted) == "public"
    }
    assert public == {
        "/api/v1/auth/otp/request",
        "/api/v1/auth/otp/verify",
        "/api/v1/auth/refresh",
    }


# --- require() behaviour --------------------------------------------------------


def token_for(role: Role) -> str:
    access, _ = create_access_token(
        user_id=uuid.uuid4(),
        role=str(role),
        secret=JWT_SECRET,
        clock=FakeClock(NOW),
        ttl_seconds=900,
        operator_id=uuid.uuid4(),
    )
    return access


@pytest.fixture
def guarded_app() -> FastAPI:
    """A throwaway app with one guarded route, to test `require` in isolation."""
    app = build_app()
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/probe/assign", dependencies=[Depends(require(Permission.assign))])
    async def probe_assign() -> dict[str, bool]:
        return {"ok": True}

    @router.get("/probe/duty", dependencies=[Depends(require(Permission.duty_manage))])
    async def probe_duty() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(router)
    return app


async def call(app: FastAPI, path: str, role: Role | None) -> int:
    headers = {"Authorization": f"Bearer {token_for(role)}"} if role else {}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path, headers=headers)
    return response.status_code


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Role.supervisor, 200),
        (Role.operator_admin, 200),
        (Role.platform_admin, 200),
        (Role.driver, 403),
        (Role.employee, 403),
        (Role.client_admin, 403),
    ],
)
async def test_assign_permission_matches_the_matrix(
    guarded_app: FastAPI, role: Role, expected: int
) -> None:
    assert await call(guarded_app, "/probe/assign", role) == expected


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Role.driver, 200),
        (Role.supervisor, 403),
        (Role.operator_admin, 403),
        (Role.employee, 403),
    ],
)
async def test_duty_permission_matches_the_matrix(
    guarded_app: FastAPI, role: Role, expected: int
) -> None:
    """ "Go on/off duty, share GPS" is the driver's alone - even admins are denied."""
    assert await call(guarded_app, "/probe/duty", role) == expected


async def test_a_guarded_route_rejects_anonymous_callers(guarded_app: FastAPI) -> None:
    assert await call(guarded_app, "/probe/assign", None) == 401


async def test_denial_names_the_missing_permission(guarded_app: FastAPI) -> None:
    transport = ASGITransport(app=guarded_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/probe/assign", headers={"Authorization": f"Bearer {token_for(Role.driver)}"}
        )
    body = response.json()
    assert body["code"] == "forbidden"
    assert body["details"]["required"] == str(Permission.assign)
    assert body["details"]["role"] == "driver"


# --- the table itself -----------------------------------------------------------


def test_every_role_has_an_entry() -> None:
    assert set(ROLE_PERMISSIONS) == set(Role)


def test_no_role_is_accidentally_omnipotent() -> None:
    """Only platform_admin may hold everything; a slip elsewhere should be loud."""
    everything = set(Permission)
    for role, granted in ROLE_PERMISSIONS.items():
        if role is not Role.platform_admin:
            assert set(granted) != everything, f"{role} holds every permission"


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        # Rows transcribed from the matrix that are easy to get wrong.
        (Role.supervisor, Permission.vehicle_manage),  # supervisors do status only
        (Role.supervisor, Permission.client_manage),
        (Role.supervisor, Permission.employee_manage),
        (Role.supervisor, Permission.billing_view),
        (Role.client_admin, Permission.assign),
        (Role.client_admin, Permission.live_map_view),
        (Role.client_admin, Permission.override),
        (Role.employee, Permission.request_queue_view),
        (Role.employee, Permission.trip_view),
        (Role.driver, Permission.assign),
        (Role.driver, Permission.request_create),
        (Role.operator_admin, Permission.operator_create),  # platform only
        (Role.operator_admin, Permission.duty_manage),  # drivers only
        (Role.operator_admin, Permission.sim_control),
    ],
)
def test_denied_cells_of_the_matrix(role: Role, permission: Permission) -> None:
    assert not has_permission(role, permission)


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (Role.platform_admin, Permission.operator_create),
        (Role.operator_admin, Permission.vehicle_manage),
        (Role.operator_admin, Permission.zone_manage),
        (Role.supervisor, Permission.vehicle_status_manage),
        (Role.supervisor, Permission.mode_set),
        (Role.supervisor, Permission.automation_pause),
        (Role.supervisor, Permission.override),
        (Role.driver, Permission.duty_manage),
        (Role.driver, Permission.trip_action),
        (Role.driver, Permission.sos_trigger),
        (Role.client_admin, Permission.employee_manage),
        (Role.client_admin, Permission.report_view),
        (Role.employee, Permission.ride_track),
        (Role.employee, Permission.sos_trigger),
    ],
)
def test_allowed_cells_of_the_matrix(role: Role, permission: Permission) -> None:
    assert has_permission(role, permission)


def test_employee_cannot_see_the_dispatch_queue() -> None:
    """The narrowest role must stay narrow."""
    granted = permissions_for(Role.employee)
    assert Permission.live_map_view not in granted
    assert Permission.request_queue_view not in granted
    assert Permission.assign not in granted


def test_unknown_role_gets_nothing() -> None:
    assert permissions_for("not-a-role") == frozenset()  # type: ignore[arg-type]
