"""Employee endpoints and the CSV import (B07)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from geoalchemy2.shape import from_shape, to_shape
from pydantic import BaseModel
from shapely.geometry import Point as ShapelyPoint

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.employee_import import ImportFormatError
from app.domain.errors import Forbidden, ValidationFailed
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.people.schemas import (
    EmployeeInput,
    EmployeeOut,
    EmployeeUpdate,
    ImportReport,
    LatLng,
)
from app.modules.people.service import EmployeeService

router = APIRouter(tags=["admin"])

#: Refuse an oversized upload before reading it into memory.
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _caller_client_id(current_user: CurrentUserDep) -> uuid.UUID | None:
    """A client_admin's token carries a client_id; operator roles carry none."""
    return current_user.claims.client_id


def _changes(payload: BaseModel) -> dict[str, Any]:
    changes: dict[str, Any] = payload.model_dump(exclude_unset=True)
    if not changes:
        raise ValidationFailed("No fields to update")
    return changes


def _employee_out(employee: Any) -> EmployeeOut:
    location = None
    if employee.home_location is not None:
        shape = to_shape(employee.home_location)
        location = LatLng(lat=shape.y, lng=shape.x)
    return EmployeeOut(
        id=employee.id,
        client_id=employee.client_id,
        zone_id=employee.zone_id,
        name=employee.name,
        phone=employee.phone,
        office_id=employee.office_id,
        home_location=location,
        home_landmark=employee.home_landmark,
        priority=employee.priority,
        is_vip=employee.is_vip,
        night_escort_required=employee.night_escort_required,
        active=employee.active,
    )


@router.get(
    "/admin/clients/{client_id}/employees",
    summary="List a client's employees",
    dependencies=[Depends(require(Permission.employee_manage))],
)
async def list_employees(
    client_id: uuid.UUID, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> dict[str, list[EmployeeOut]]:
    employees = await EmployeeService(session, clock).list_employees(
        _operator_id(current_user), client_id, _caller_client_id(current_user)
    )
    return {"items": [_employee_out(e) for e in employees]}


@router.post(
    "/admin/clients/{client_id}/employees",
    status_code=status.HTTP_201_CREATED,
    summary="Add an employee",
    dependencies=[Depends(require(Permission.employee_manage))],
)
async def create_employee(
    client_id: uuid.UUID,
    body: EmployeeInput,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> EmployeeOut:
    data = body.model_dump()
    data["home_location"] = from_shape(
        ShapelyPoint(body.home_location.lng, body.home_location.lat), srid=4326
    )
    employee = await EmployeeService(session, clock).create_employee(
        _operator_id(current_user), client_id, data, _caller_client_id(current_user)
    )
    return _employee_out(employee)


@router.patch(
    "/admin/employees/{employee_id}",
    summary="Update an employee",
    dependencies=[Depends(require(Permission.employee_manage))],
)
async def update_employee(
    employee_id: uuid.UUID,
    body: EmployeeUpdate,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> EmployeeOut:
    changes = _changes(body)
    if "home_location" in changes and body.home_location is not None:
        changes["home_location"] = from_shape(
            ShapelyPoint(body.home_location.lng, body.home_location.lat), srid=4326
        )
    employee = await EmployeeService(session, clock).update_employee(
        _operator_id(current_user), employee_id, changes, _caller_client_id(current_user)
    )
    return _employee_out(employee)


@router.post(
    "/admin/clients/{client_id}/employees/import",
    summary="CSV import (name,phone,office_name,home_lat,home_lng,landmark,priority,is_vip)",
    dependencies=[Depends(require(Permission.employee_manage))],
)
async def import_employees(
    client_id: uuid.UUID,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
    file: Annotated[UploadFile, File()],
    dry_run: Annotated[bool, Query()] = True,
) -> ImportReport:
    """Defaults to a dry run, deliberately: the safe option should need no thought."""
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValidationFailed(
            "The file is too large", {"max_bytes": MAX_UPLOAD_BYTES, "size": len(raw)}
        )

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationFailed("The file must be UTF-8 encoded CSV", {"detail": str(exc)}) from exc

    try:
        report = await EmployeeService(session, clock).import_csv(
            operator_id=_operator_id(current_user),
            client_id=client_id,
            content=content,
            caller_client_id=_caller_client_id(current_user),
            dry_run=dry_run,
        )
    except ImportFormatError as exc:
        raise ValidationFailed(str(exc)) from exc

    return ImportReport.model_validate(report.as_dict())
