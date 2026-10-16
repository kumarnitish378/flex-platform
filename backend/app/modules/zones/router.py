"""`/admin/zones` (`api-spec.yaml`) - drawing the areas everything else scopes by (B27)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.core.geo import ring
from app.domain.errors import Forbidden
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.requests.schemas import LatLng
from app.modules.tenancy.models import Zone
from app.modules.zones.schemas import ZoneInput, ZoneOut, ZoneUpdate
from app.modules.zones.service import ZoneService

router = APIRouter(tags=["admin"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _out(zone: Zone, employee_count: int) -> ZoneOut:
    return ZoneOut(
        id=zone.id,
        name=zone.name,
        boundary=[LatLng(lat=lat, lng=lng) for lat, lng in ring(zone.area)],
        active=zone.active,
        employee_count=employee_count,
    )


@router.get(
    "/admin/zones",
    summary="Operational zones, with how many employees each covers",
    dependencies=[Depends(require(Permission.zone_manage))],
)
async def list_zones(
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
    include_inactive: bool = Query(default=False),
) -> dict[str, list[ZoneOut]]:
    rows = await ZoneService(session, clock).list_zones(
        _operator_id(current_user), include_inactive=include_inactive
    )
    return {"items": [_out(zone, count) for zone, count in rows]}


@router.post(
    "/admin/zones",
    status_code=status.HTTP_201_CREATED,
    summary="Draw a zone",
    dependencies=[Depends(require(Permission.zone_manage))],
)
async def create_zone(
    body: ZoneInput, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> ZoneOut:
    """Creating a zone re-derives every employee of the operator.

    So "who is in this zone" is right the moment it exists, rather than from the next
    CSV import onwards - which would make a freshly drawn zone silently empty.
    """
    zone, count = await ZoneService(session, clock).create(
        _operator_id(current_user),
        body.name,
        [(point.lat, point.lng) for point in body.boundary],
        active=body.active,
    )
    return _out(zone, count)


@router.patch(
    "/admin/zones/{zone_id}",
    summary="Rename, redraw or deactivate a zone",
    dependencies=[Depends(require(Permission.zone_manage))],
)
async def update_zone(
    zone_id: uuid.UUID,
    body: ZoneUpdate,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> ZoneOut:
    zone, count = await ZoneService(session, clock).update(
        _operator_id(current_user),
        zone_id,
        name=body.name,
        boundary=(
            [(point.lat, point.lng) for point in body.boundary]
            if body.boundary is not None
            else None
        ),
        active=body.active,
    )
    return _out(zone, count)


@router.delete(
    "/admin/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a zone",
    dependencies=[Depends(require(Permission.zone_manage))],
)
async def delete_zone(
    zone_id: uuid.UUID, session: SessionDep, clock: ClockDep, current_user: CurrentUserDep
) -> Response:
    await ZoneService(session, clock).delete(_operator_id(current_user), zone_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
