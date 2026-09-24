"""`/admin/*` for clients, offices, vehicles, drivers and user invites (B06)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from geoalchemy2.shape import from_shape, to_shape
from pydantic import BaseModel
from shapely.geometry import Point as ShapelyPoint

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.enums import CLIENT_SCOPED_ROLES, Role
from app.domain.errors import Forbidden, ValidationFailed
from app.domain.state_machines import VehicleStatus
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.fleet.schemas import (
    ClientInput,
    ClientOut,
    DriverInput,
    DriverOut,
    DriverUpdate,
    InvitedUser,
    LatLng,
    OfficeInput,
    OfficeOut,
    UserInvite,
    VehicleInput,
    VehicleOut,
    VehicleUpdate,
)
from app.modules.fleet.service import AdminService

router = APIRouter(tags=["admin"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _changes(payload: BaseModel) -> dict[str, Any]:
    """Only the fields actually sent, so a PATCH cannot null out what it omitted."""
    changes: dict[str, Any] = payload.model_dump(exclude_unset=True)
    if not changes:
        raise ValidationFailed("No fields to update")
    return changes


def _point(location: LatLng) -> Any:
    return from_shape(ShapelyPoint(location.lng, location.lat), srid=4326)


def _latlng(value: Any) -> LatLng:
    shape = to_shape(value)
    return LatLng(lat=shape.y, lng=shape.x)


# --- clients ------------------------------------------------------------------


@router.get(
    "/admin/clients",
    summary="List clients",
    dependencies=[Depends(require(Permission.client_manage))],
)
async def list_clients(
    session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> dict[str, list[ClientOut]]:
    clients = await AdminService(session, clock).list_clients(_operator_id(current_user))
    return {
        "items": [
            ClientOut(
                id=c.id, name=c.name, contact_name=c.contact_name, contact_phone=c.contact_phone
            )
            for c in clients
        ]
    }


@router.post(
    "/admin/clients",
    status_code=status.HTTP_201_CREATED,
    summary="Create a client",
    dependencies=[Depends(require(Permission.client_manage))],
)
async def create_client(
    body: ClientInput, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> ClientOut:
    client = await AdminService(session, clock).create_client(
        _operator_id(current_user), body.model_dump()
    )
    return ClientOut(
        id=client.id,
        name=client.name,
        contact_name=client.contact_name,
        contact_phone=client.contact_phone,
    )


# --- offices --------------------------------------------------------------------


@router.get(
    "/admin/clients/{client_id}/offices",
    summary="List a client's offices",
    dependencies=[Depends(require(Permission.client_manage))],
)
async def list_offices(
    client_id: uuid.UUID, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> dict[str, list[OfficeOut]]:
    offices = await AdminService(session, clock).list_offices(_operator_id(current_user), client_id)
    return {
        "items": [
            OfficeOut(
                id=o.id,
                client_id=o.client_id,
                name=o.name,
                location=_latlng(o.location),
                address_text=o.address_text,
            )
            for o in offices
        ]
    }


@router.post(
    "/admin/clients/{client_id}/offices",
    status_code=status.HTTP_201_CREATED,
    summary="Create an office",
    dependencies=[Depends(require(Permission.client_manage))],
)
async def create_office(
    client_id: uuid.UUID,
    body: OfficeInput,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> OfficeOut:
    data = body.model_dump()
    data["location"] = _point(body.location)
    office = await AdminService(session, clock).create_office(
        _operator_id(current_user), client_id, data
    )
    return OfficeOut(
        id=office.id,
        client_id=office.client_id,
        name=office.name,
        location=body.location,
        address_text=office.address_text,
    )


# --- vehicles ----------------------------------------------------------------------


def _vehicle_out(vehicle: Any) -> VehicleOut:
    return VehicleOut(
        id=vehicle.id,
        registration_no=vehicle.registration_no,
        model=vehicle.model,
        vehicle_type=vehicle.vehicle_type,
        seat_capacity=vehicle.seat_capacity,
        tracker_type=vehicle.tracker_type,
        status=vehicle.status,
        current_driver_id=vehicle.current_driver_id,
    )


@router.get(
    "/admin/vehicles",
    summary="List vehicles",
    dependencies=[Depends(require(Permission.vehicle_status_manage))],
)
async def list_vehicles(
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
    vehicle_status: Annotated[VehicleStatus | None, Query(alias="status")] = None,
) -> dict[str, list[VehicleOut]]:
    vehicles = await AdminService(session, clock).list_vehicles(
        _operator_id(current_user), vehicle_status
    )
    return {"items": [_vehicle_out(v) for v in vehicles]}


@router.post(
    "/admin/vehicles",
    status_code=status.HTTP_201_CREATED,
    summary="Add a vehicle",
    dependencies=[Depends(require(Permission.vehicle_manage))],
)
async def create_vehicle(
    body: VehicleInput, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> VehicleOut:
    vehicle = await AdminService(session, clock).create_vehicle(
        _operator_id(current_user), body.model_dump()
    )
    return _vehicle_out(vehicle)


@router.patch(
    "/admin/vehicles/{vehicle_id}",
    summary="Update a vehicle",
    # Supervisors may change status only; the service-level split is enforced below.
    dependencies=[Depends(require(Permission.vehicle_status_manage))],
)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    body: VehicleUpdate,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> VehicleOut:
    changes = _changes(body)

    # "Manage vehicles: supervisor = status only" (roles-and-permissions.md). The
    # permission above admits supervisors, so the field-level limit lives here.
    if current_user.active_role is Role.supervisor:
        not_allowed = set(changes) - {"status"}
        if not_allowed:
            raise Forbidden(
                "A supervisor may change vehicle status only",
                {"fields": sorted(not_allowed)},
            )

    vehicle = await AdminService(session, clock).update_vehicle(
        _operator_id(current_user), vehicle_id, changes
    )
    return _vehicle_out(vehicle)


# --- drivers -------------------------------------------------------------------------


def _driver_out(driver: Any) -> DriverOut:
    return DriverOut(
        id=driver.id,
        name=driver.name,
        phone=driver.phone,
        licence_last4=driver.licence_last4,
        default_vehicle_id=driver.default_vehicle_id,
        active=driver.active,
    )


@router.get(
    "/admin/drivers",
    summary="List drivers",
    dependencies=[Depends(require(Permission.operator_user_manage))],
)
async def list_drivers(
    session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> dict[str, list[DriverOut]]:
    drivers = await AdminService(session, clock).list_drivers(_operator_id(current_user))
    return {"items": [_driver_out(d) for d in drivers]}


@router.post(
    "/admin/drivers",
    status_code=status.HTTP_201_CREATED,
    summary="Add a driver",
    dependencies=[Depends(require(Permission.operator_user_manage))],
)
async def create_driver(
    body: DriverInput, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> DriverOut:
    driver = await AdminService(session, clock).create_driver(
        _operator_id(current_user), body.model_dump()
    )
    return _driver_out(driver)


@router.patch(
    "/admin/drivers/{driver_id}",
    summary="Update a driver",
    dependencies=[Depends(require(Permission.operator_user_manage))],
)
async def update_driver(
    driver_id: uuid.UUID,
    body: DriverUpdate,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> DriverOut:
    driver = await AdminService(session, clock).update_driver(
        _operator_id(current_user), driver_id, _changes(body)
    )
    return _driver_out(driver)


# --- users -----------------------------------------------------------------------------


@router.post(
    "/admin/users/invite",
    status_code=status.HTTP_201_CREATED,
    summary="Invite supervisor, client_admin or operator_admin by phone",
    dependencies=[Depends(require(Permission.operator_user_manage))],
)
async def invite_user(
    body: UserInvite, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> InvitedUser:
    if body.role not in (Role.supervisor, Role.client_admin, Role.operator_admin):
        raise ValidationFailed(
            "Only supervisor, client_admin and operator_admin can be invited",
            {"role": str(body.role)},
        )

    user = await AdminService(session, clock).invite_user(
        operator_id=_operator_id(current_user),
        phone=body.phone,
        name=body.name,
        role=body.role,
        client_id=body.client_id if body.role in CLIENT_SCOPED_ROLES else None,
    )
    return InvitedUser(
        user_id=user.id,
        phone=user.phone,
        name=user.name,
        role=body.role,
        client_id=body.client_id if body.role in CLIENT_SCOPED_ROLES else None,
    )
