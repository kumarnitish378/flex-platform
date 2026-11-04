"""`/admin/config` (`api-spec.yaml`)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.errors import Forbidden
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.config.service import ConfigService

router = APIRouter(tags=["admin"])


def _operator_id(current_user: CurrentUserDep) -> Any:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        # platform_admin holds no operator; it must say which one it is acting on.
        raise Forbidden("This role has no operator scope for config")
    return operator_id


@router.get(
    "/admin/config",
    summary="Operator config key/values",
    dependencies=[Depends(require(Permission.config_manage))],
)
async def get_config(
    session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> dict[str, Any]:
    return await ConfigService(session, clock).all_values(_operator_id(current_user))


@router.patch(
    "/admin/config",
    summary="Update operator config",
    description="Validates ranges from allocation-rules.md; audited.",
    dependencies=[Depends(require(Permission.config_manage))],
)
async def patch_config(
    changes: Annotated[dict[str, Any], Body()],
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> dict[str, Any]:
    return await ConfigService(session, clock).update(
        _operator_id(current_user), changes, changed_by=current_user.claims.user_id
    )
