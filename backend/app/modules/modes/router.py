"""`/admin/mode-settings` and `/dispatch/requests/{id}/mode` (`api-spec.yaml`, B24)."""

from __future__ import annotations

import uuid
from datetime import time
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.enums import Direction
from app.domain.errors import Forbidden, NotFound
from app.domain.modes import Mode
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.modes.models import ModeSetting
from app.modules.modes.service import ModeService, ModeSettingInput
from app.modules.requests.models import RideRequest

router = APIRouter(tags=["admin"])


class ModeSettingBody(BaseModel):
    """Every scoping field optional; `None` means "any"."""

    mode: Mode
    client_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    direction: Direction | None = None
    weekdays: list[int] | None = None
    start_time: time | None = None
    end_time: time | None = None
    note: str | None = None

    def to_input(self) -> ModeSettingInput:
        return ModeSettingInput(
            mode=self.mode,
            client_id=self.client_id,
            zone_id=self.zone_id,
            direction=self.direction,
            weekdays=self.weekdays,
            start_time=self.start_time,
            end_time=self.end_time,
            note=self.note,
        )


class ModeSettingOut(ModeSettingBody):
    id: uuid.UUID
    updated_at: Any = None


class ModeSettingsOut(BaseModel):
    items: list[ModeSettingOut] = Field(default_factory=list)
    #: Pairs of ids at equal specificity that could both match one request. §2 resolves
    #: them by update time; the screen warns rather than the API refusing.
    overlapping: list[list[uuid.UUID]] = Field(default_factory=list)


class ModeResolutionOut(BaseModel):
    mode: Mode
    reason: str
    setting_id: uuid.UUID | None = None


def _operator_id(current_user: CurrentUserDep) -> Any:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope for mode settings")
    return operator_id


@router.get(
    "/admin/mode-settings",
    summary="Mode settings for this operator, with any overlapping pairs",
    dependencies=[Depends(require(Permission.config_manage))],
)
async def list_mode_settings(
    session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> ModeSettingsOut:
    service = ModeService(session, clock)
    operator_id = _operator_id(current_user)
    settings = await service.list_settings(operator_id)
    pairs = await service.overlapping(operator_id)
    return ModeSettingsOut(
        items=[_out(setting) for setting in settings],
        overlapping=[[first, second] for first, second in pairs],
    )


@router.post(
    "/admin/mode-settings",
    summary="Create a mode setting",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require(Permission.config_manage))],
)
async def create_mode_setting(
    body: ModeSettingBody, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> ModeSettingOut:
    setting = await ModeService(session, clock).create(_operator_id(current_user), body.to_input())
    return _out(setting)


@router.put(
    "/admin/mode-settings/{setting_id}",
    summary="Replace a mode setting",
    dependencies=[Depends(require(Permission.config_manage))],
)
async def update_mode_setting(
    setting_id: uuid.UUID,
    body: ModeSettingBody,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> ModeSettingOut:
    setting = await ModeService(session, clock).update(
        _operator_id(current_user), setting_id, body.to_input()
    )
    return _out(setting)


@router.delete(
    "/admin/mode-settings/{setting_id}",
    summary="Delete a mode setting",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require(Permission.config_manage))],
)
async def delete_mode_setting(
    setting_id: uuid.UUID, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> Response:
    await ModeService(session, clock).delete(_operator_id(current_user), setting_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/dispatch/requests/{request_id}/mode",
    summary="Which mode governs this request, and why",
    tags=["dispatch"],
    dependencies=[Depends(require(Permission.assign))],
)
async def resolved_mode(
    request_id: uuid.UUID, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> ModeResolutionOut:
    operator_id = _operator_id(current_user)
    request = await session.get(RideRequest, request_id)
    if request is None or request.operator_id != operator_id:
        raise NotFound("Ride request not found")

    resolution = await ModeService(session, clock).resolve_for_request(request)
    return ModeResolutionOut(
        mode=resolution.mode,
        reason=str(resolution.reason),
        setting_id=resolution.setting_id,
    )


def _out(setting: ModeSetting) -> ModeSettingOut:
    return ModeSettingOut(
        id=setting.id,
        mode=Mode(setting.mode),
        client_id=setting.client_id,
        zone_id=setting.zone_id,
        direction=Direction(setting.direction) if setting.direction else None,
        weekdays=list(setting.weekdays) if setting.weekdays else None,
        start_time=setting.start_time,
        end_time=setting.end_time,
        note=setting.note,
        updated_at=setting.updated_at,
    )
