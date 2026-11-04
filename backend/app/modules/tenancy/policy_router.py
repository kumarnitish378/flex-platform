"""`/admin/clients/{client_id}/policy` (`api-spec.yaml`, B28)."""

from __future__ import annotations

import uuid
from datetime import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.errors import Forbidden
from app.domain.policy import EffectivePolicy
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.tenancy.models import ClientPolicy
from app.modules.tenancy.policy_service import ClientPolicyService

router = APIRouter(tags=["admin"])


class ClientPolicyInput(BaseModel):
    """Every field optional; `null` clears an override.

    `extra="forbid"` matters more here than elsewhere: a mistyped field name on a
    **safety** setting would otherwise be accepted and do nothing.
    """

    model_config = ConfigDict(extra="forbid")

    pooling_allowed: bool | None = None
    employee_opt_out_allowed: bool | None = None
    night_safety_enabled: bool | None = None
    night_start: time | None = None
    night_end: time | None = None
    max_detour_factor: float | None = Field(default=None, ge=1.0, le=3.0)
    max_detour_minutes: int | None = Field(default=None, ge=0, le=60)
    pickup_window_minutes: int | None = Field(default=None, ge=0, le=30)
    no_show_wait_minutes: int | None = Field(default=None, ge=1, le=15)


class EffectiveOut(BaseModel):
    """What the platform will actually apply, after the stricter-value rule."""

    max_detour_factor: float
    max_detour_minutes: float
    pickup_window_minutes: int
    no_show_wait_minutes: int
    night_safety_enabled: bool
    night_start: time
    night_end: time
    night_safety_positions: str


class ClientPolicyOut(BaseModel):
    client_id: uuid.UUID
    pooling_allowed: bool
    employee_opt_out_allowed: bool
    night_safety_enabled: bool
    night_start: time | None = None
    night_end: time | None = None
    max_detour_factor: float | None = None
    max_detour_minutes: int | None = None
    pickup_window_minutes: int | None = None
    no_show_wait_minutes: int | None = None
    effective: EffectiveOut


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _out(
    client_id: uuid.UUID, policy: ClientPolicy | None, effective: EffectivePolicy
) -> ClientPolicyOut:
    return ClientPolicyOut(
        client_id=client_id,
        pooling_allowed=policy.pooling_allowed if policy else True,
        employee_opt_out_allowed=policy.employee_opt_out_allowed if policy else False,
        night_safety_enabled=policy.night_safety_enabled if policy else False,
        night_start=policy.night_start if policy else None,
        night_end=policy.night_end if policy else None,
        max_detour_factor=(
            float(policy.max_detour_factor)
            if policy and policy.max_detour_factor is not None
            else None
        ),
        max_detour_minutes=policy.max_detour_minutes if policy else None,
        pickup_window_minutes=policy.pickup_window_minutes if policy else None,
        no_show_wait_minutes=policy.no_show_wait_minutes if policy else None,
        effective=EffectiveOut(
            max_detour_factor=effective.max_detour_factor,
            max_detour_minutes=effective.max_detour_minutes,
            pickup_window_minutes=effective.pickup_window_minutes,
            no_show_wait_minutes=effective.no_show_wait_minutes,
            night_safety_enabled=effective.night_safety_enabled,
            night_start=effective.night_start,
            night_end=effective.night_end,
            night_safety_positions=effective.night_safety_positions,
        ),
    )


@router.get(
    "/admin/clients/{client_id}/policy",
    summary="What this client's own rules are, and what they resolve to",
    dependencies=[Depends(require(Permission.client_policy_manage))],
)
async def get_policy(
    client_id: uuid.UUID, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> ClientPolicyOut:
    """Both halves, deliberately.

    An admin who types a laxer detour limit than the operator's, sees it saved, and is
    never told it is not being applied has been misled by the screen. `effective` is
    what the platform will do.
    """
    operator_id = _operator_id(current_user)
    service = ClientPolicyService(session, clock)
    return _out(
        client_id,
        await service.row(operator_id, client_id),
        await service.for_client(operator_id, client_id),
    )


@router.put(
    "/admin/clients/{client_id}/policy",
    summary="Set this client's policy",
    dependencies=[Depends(require(Permission.client_policy_manage))],
)
async def put_policy(
    client_id: uuid.UUID,
    body: ClientPolicyInput,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> ClientPolicyOut:
    operator_id = _operator_id(current_user)
    service = ClientPolicyService(session, clock)
    # Only the fields the caller sent: a `null` clears an override, and an omitted
    # field leaves it alone. The two are different requests.
    policy = await service.put(
        operator_id, client_id, body.model_dump(include=body.model_fields_set)
    )
    return _out(client_id, policy, await service.for_client(operator_id, client_id))
