"""`/alerts*`, `/sos` and `/driver/issues` (`api-spec.yaml`) - B17."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import ClockDep, CurrentUserDep, EventsDep, PushDep, SessionDep
from app.domain.errors import Forbidden
from app.modules.alerts.models import Alert
from app.modules.alerts.schemas import AlertOut, DriverIssueInput, SosInput
from app.modules.alerts.service import AlertService
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.notifications.service import NotificationService

router = APIRouter(tags=["alerts"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _service(
    session: SessionDep, clock: ClockDep, events: EventsDep, push: PushDep
) -> AlertService:
    return AlertService(
        session, clock, events=events, notifications=NotificationService(session, clock, push)
    )


ServiceDep = Annotated[AlertService, Depends(_service)]


@router.post(
    "/sos",
    status_code=status.HTTP_201_CREATED,
    summary="Raise an emergency alert (EMP-08)",
    dependencies=[Depends(require(Permission.sos_trigger))],
)
async def raise_sos(body: SosInput, service: ServiceDep, current_user: CurrentUserDep) -> AlertOut:
    alert = await service.sos(
        operator_id=_operator_id(current_user),
        user_id=current_user.claims.user_id,
        lat=body.lat,
        lng=body.lng,
        trip_id=body.trip_id,
    )
    return _out(alert)


@router.post(
    "/driver/issues",
    status_code=status.HTTP_201_CREATED,
    summary="Report a breakdown, accident, traffic block or rider issue (DRV-06)",
    dependencies=[Depends(require(Permission.driver_issue_report))],
)
async def report_issue(
    body: DriverIssueInput, service: ServiceDep, current_user: CurrentUserDep
) -> AlertOut:
    operator_id = _operator_id(current_user)
    # The vehicle comes from the driver's open duty session, never from the body: a
    # driver must not be able to take someone else's cab off the road.
    vehicle_id = await service.vehicle_on_duty_for(current_user.claims.user_id)
    alert = await service.driver_issue(
        operator_id=operator_id,
        driver_user_id=current_user.claims.user_id,
        issue_type=body.type,
        note=body.note,
        trip_id=body.trip_id,
        vehicle_id=vehicle_id,
        lat=body.lat,
        lng=body.lng,
    )
    return _out(alert)


@router.get(
    "/alerts",
    summary="Alerts for the operator, newest first",
    dependencies=[Depends(require(Permission.request_queue_view))],
)
async def list_alerts(
    service: ServiceDep,
    current_user: CurrentUserDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> dict[str, list[AlertOut]]:
    alerts = await service.list_alerts(_operator_id(current_user), status_filter)
    return {"items": [_out(alert) for alert in alerts]}


@router.post(
    "/alerts/{alert_id}/{action}",
    summary="Acknowledge or resolve an alert",
    dependencies=[Depends(require(Permission.request_queue_view))],
)
async def act_on_alert(
    alert_id: uuid.UUID,
    action: Literal["acknowledge", "resolve"],
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> AlertOut:
    operator_id = _operator_id(current_user)
    user_id = current_user.claims.user_id
    if action == "acknowledge":
        alert = await service.acknowledge(operator_id, alert_id, user_id)
    else:
        alert = await service.resolve(operator_id, alert_id, user_id)
    return _out(alert)


def _out(alert: Alert) -> AlertOut:
    return AlertOut(
        id=alert.id,
        type=alert.type,
        severity=alert.severity,
        status=alert.status,
        created_at=alert.created_at,
        request_id=alert.request_id,
        trip_id=alert.trip_id,
        vehicle_id=alert.vehicle_id,
        data=alert.data or {},
    )
