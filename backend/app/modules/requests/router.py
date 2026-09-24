"""`/ride-requests*` (`api-spec.yaml`)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from geoalchemy2.shape import to_shape

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.enums import Role
from app.domain.errors import Forbidden
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.requests.schemas import (
    CancelInput,
    LatLng,
    RideRequestInput,
    RideRequestOut,
)
from app.modules.requests.service import RideRequestService

router = APIRouter(tags=["employee"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _out(request: Any, employee_name: str | None = None) -> RideRequestOut:
    shape = to_shape(request.location)
    return RideRequestOut(
        id=request.id,
        employee_id=request.employee_id,
        employee_name=employee_name,
        client_id=request.client_id,
        direction=request.direction,
        office_id=request.office_id,
        location=LatLng(lat=shape.y, lng=shape.x),
        landmark=request.landmark,
        requested_time=request.requested_time,
        urgency=request.urgency,
        no_sharing=request.no_sharing,
        status=request.status,
        # Waiting starts when the request was made, which is what the supervisor's
        # timer counts from.
        waiting_since=request.created_at,
        trip_id=request.trip_id,
        locked=request.is_locked,
        cancel_reason=request.cancel_reason,
        expires_at=request.expires_at,
    )


@router.post(
    "/ride-requests",
    status_code=status.HTTP_201_CREATED,
    summary="Create ride request (employee for self; supervisor/client_admin on behalf)",
    dependencies=[Depends(require(Permission.request_create))],
)
async def create_request(
    body: RideRequestInput,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> RideRequestOut:
    request = await RideRequestService(session, clock).create(
        operator_id=_operator_id(current_user),
        actor_role=current_user.active_role,
        actor_user_id=current_user.claims.user_id,
        direction=body.direction,
        requested_time=body.requested_time,
        employee_id=body.employee_id,
        location=(body.location.lat, body.location.lng) if body.location else None,
        landmark=body.landmark,
        urgency=body.urgency,
        no_sharing=body.no_sharing,
        caller_client_id=current_user.claims.client_id,
    )
    return _out(request)


@router.get(
    "/ride-requests/mine",
    summary="My ride requests",
    dependencies=[Depends(require(Permission.ride_track))],
)
async def list_mine(
    session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> dict[str, list[RideRequestOut]]:
    service = RideRequestService(session, clock)
    operator_id = _operator_id(current_user)
    employee_id = await _caller_employee_id(service, current_user, operator_id)
    if employee_id is None:
        raise Forbidden("This account is not linked to an employee record")
    requests = await service.list_mine(operator_id, employee_id)
    return {"items": [_out(r) for r in requests]}


@router.get(
    "/ride-requests/{request_id}",
    summary="Get a ride request",
    dependencies=[Depends(require(Permission.request_cancel))],
)
async def get_request(
    request_id: uuid.UUID,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> RideRequestOut:
    service = RideRequestService(session, clock)
    operator_id = _operator_id(current_user)
    request = await service.get(
        operator_id,
        request_id,
        caller_employee_id=await _caller_employee_id(service, current_user, operator_id),
        caller_client_id=current_user.claims.client_id,
    )
    return _out(request)


@router.post(
    "/ride-requests/{request_id}/cancel",
    summary="Cancel a ride request",
    dependencies=[Depends(require(Permission.request_cancel))],
)
async def cancel_request(
    request_id: uuid.UUID,
    body: CancelInput,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> RideRequestOut:
    service = RideRequestService(session, clock)
    operator_id = _operator_id(current_user)
    request = await service.cancel(
        operator_id=operator_id,
        request_id=request_id,
        actor_role=current_user.active_role,
        actor_user_id=current_user.claims.user_id,
        reason=body.reason,
        caller_employee_id=await _caller_employee_id(service, current_user, operator_id),
        caller_client_id=current_user.claims.client_id,
    )
    return _out(request)


async def _caller_employee_id(
    service: RideRequestService, current_user: CurrentUserDep, operator_id: uuid.UUID
) -> uuid.UUID | None:
    """The employee record behind the token, for the `employee` role only.

    Returned only for riders: it is what narrows every read to "my own requests".
    Operator-level roles get `None` and are scoped by operator (and client) instead.
    """
    if current_user.active_role is not Role.employee:
        return None
    employee = await service.employee_for_user(operator_id, current_user.claims.user_id)
    return employee.id if employee else None
