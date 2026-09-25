"""`/driver/duty` (`api-spec.yaml`, DRV-02)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep, SettingsDep
from app.domain.errors import Forbidden
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.fleet.duty_service import DutyService

router = APIRouter(tags=["driver"])


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DutyInput(Strict):
    on_duty: bool
    vehicle_id: uuid.UUID | None = None


class MqttOut(Strict):
    host: str
    port: int
    username: str
    password: str
    topic_prefix: str


class DutyStateOut(Strict):
    on_duty: bool
    vehicle_id: uuid.UUID | None = None
    mqtt: MqttOut | None = None


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _out(state: object) -> DutyStateOut:
    mqtt = getattr(state, "mqtt", None)
    return DutyStateOut(
        on_duty=state.on_duty,  # type: ignore[attr-defined]
        vehicle_id=state.vehicle_id,  # type: ignore[attr-defined]
        mqtt=(
            MqttOut(
                host=mqtt.host,
                port=mqtt.port,
                username=mqtt.username,
                password=mqtt.password,
                topic_prefix=mqtt.topic_prefix,
            )
            if mqtt
            else None
        ),
    )


@router.post(
    "/driver/duty",
    summary="Go on or off duty",
    dependencies=[Depends(require(Permission.duty_manage))],
)
async def set_duty(
    body: DutyInput,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> DutyStateOut:
    """The MQTT password is returned here and nowhere else - it is not stored."""
    state = await DutyService(session, clock, settings).set_duty(
        operator_id=_operator_id(current_user),
        user_id=current_user.claims.user_id,
        on_duty=body.on_duty,
        vehicle_id=body.vehicle_id,
    )
    return _out(state)


@router.get(
    "/driver/duty",
    summary="Current duty state",
    dependencies=[Depends(require(Permission.duty_manage))],
)
async def get_duty(
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> DutyStateOut:
    state = await DutyService(session, clock, settings).current(
        _operator_id(current_user), current_user.claims.user_id
    )
    return _out(state)
