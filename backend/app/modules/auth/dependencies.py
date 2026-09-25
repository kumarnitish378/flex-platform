"""Route-level authorisation (B04).

`roles-and-permissions.md`: every endpoint declares the permission it needs via a
dependency; no inline role checks (`coding-standards.md` §2 rule 4).

    @router.post("/dispatch/assign", dependencies=[Depends(require(Permission.assign))])

Routes that are genuinely public (login, health) declare `public_route()` instead, so
"no declaration" always means "someone forgot" and the harness in
`tests/integration/test_permissions.py` can say so.

What this layer does **not** do is decide whether the caller may touch a *particular*
row. Holding `request.cancel` does not mean cancelling anyone's request; the service
narrows by `client_id` / `employee_id` / `driver_id` from the active role. Permission
first, scope second, always both.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from app.core.dependencies import CurrentUser, CurrentUserDep
from app.domain.errors import Forbidden
from app.modules.auth.permissions import Permission, has_permission

#: Attribute stamped on a dependency so route inspection can find the declaration.
PERMISSION_ATTR = "__smartcab_permission__"
PUBLIC_ATTR = "__smartcab_public__"
SELF_SERVICE_ATTR = "__smartcab_self_service__"
#: Set alongside PERMISSION_ATTR when a route accepts any of several permissions.
ANY_PERMISSIONS_ATTR = "__smartcab_any_permissions__"

DependencyFn = Callable[..., Coroutine[Any, Any, CurrentUser]]


def require(permission: Permission) -> DependencyFn:
    """A dependency that admits only roles holding `permission`."""

    async def checker(current_user: CurrentUserDep) -> CurrentUser:
        if not has_permission(current_user.active_role, permission):
            raise Forbidden(
                "This role may not perform that action",
                {"required": str(permission), "role": str(current_user.active_role)},
            )
        return current_user

    setattr(checker, PERMISSION_ATTR, permission)
    checker.__name__ = f"require_{permission.name}"
    checker.__doc__ = f"Requires `{permission}`."
    return checker


def require_any(*permissions: Permission) -> DependencyFn:
    """Admits a role holding **any** of these permissions.

    For the rare endpoint that legitimately serves two audiences through different
    permissions - the trip report is read by a supervisor under
    `report.operational.view` and by a client admin under `report.view`. Still one
    explicit declaration, so the harness sees it; the service narrows the *rows* by
    role, which is the part that actually protects anyone.
    """
    if not permissions:
        raise ValueError("require_any needs at least one permission")

    async def checker(current_user: CurrentUserDep) -> CurrentUser:
        if not any(has_permission(current_user.active_role, p) for p in permissions):
            raise Forbidden(
                "This role may not perform that action",
                {
                    "required_any": [str(p) for p in permissions],
                    "role": str(current_user.active_role),
                },
            )
        return current_user

    setattr(checker, PERMISSION_ATTR, permissions[0])
    setattr(checker, ANY_PERMISSIONS_ATTR, permissions)
    checker.__name__ = "require_any_" + "_or_".join(p.name for p in permissions)
    checker.__doc__ = "Requires any of: " + ", ".join(f"`{p}`" for p in permissions)
    return checker


def public_route() -> Callable[..., None]:
    """Marks a route as deliberately unauthenticated.

    An explicit marker rather than an allow-list of paths: the declaration sits next to
    the route, so making something public is a visible edit in review.
    """

    def marker() -> None:
        return None

    setattr(marker, PUBLIC_ATTR, True)
    marker.__name__ = "public_route"
    return marker


def self_service_route() -> Callable[..., None]:
    """Marks a route that needs authentication but no permission.

    `/auth/me`, `/auth/logout` and `/devices` act on the caller's own account, so every
    role may use them and a permission would be meaningless. Still an explicit
    declaration, so the harness can tell "every role" from "nobody thought about it".
    """

    def marker() -> None:
        return None

    setattr(marker, SELF_SERVICE_ATTR, True)
    marker.__name__ = "self_service_route"
    return marker


def is_self_service(dependency: object) -> bool:
    return bool(getattr(dependency, SELF_SERVICE_ATTR, False))


def permission_of(dependency: object) -> Permission | None:
    value = getattr(dependency, PERMISSION_ATTR, None)
    return value if isinstance(value, Permission) else None


def is_public(dependency: object) -> bool:
    return bool(getattr(dependency, PUBLIC_ATTR, False))
