"""`/ride-requests/{id}/rating` and `/reports/trips` (`api-spec.yaml`) - B18."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.enums import Role
from app.domain.errors import Forbidden
from app.modules.auth.dependencies import require, require_any
from app.modules.auth.permissions import Permission
from app.modules.reports.schemas import RatingInput, RatingOut, TripReportOut
from app.modules.reports.service import ReportService

router = APIRouter(tags=["reports"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _service(session: SessionDep, clock: ClockDep) -> ReportService:
    return ReportService(session, clock)


ServiceDep = Annotated[ReportService, Depends(_service)]


@router.post(
    "/ride-requests/{request_id}/rating",
    status_code=status.HTTP_201_CREATED,
    summary="Rate a finished ride (EMP-07)",
    dependencies=[Depends(require(Permission.ride_track))],
)
async def rate_ride(
    request_id: uuid.UUID,
    body: RatingInput,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> RatingOut:
    operator_id = _operator_id(current_user)
    employee_id = await service.employee_for_user(operator_id, current_user.claims.user_id)
    if employee_id is None:
        raise Forbidden("This account is not linked to an employee record")

    rating = await service.rate(
        operator_id=operator_id,
        request_id=request_id,
        employee_id=employee_id,
        rating=body.rating,
        comment=body.comment,
    )
    return RatingOut(request_id=rating.request_id, rating=rating.rating, comment=rating.comment)


@router.get(
    "/reports/trips",
    summary="Trips, waits, no-shows and cancellations for a period (OPA-05)",
    # The endpoint answers JSON or CSV, so the return type is a union FastAPI cannot
    # turn into one response model. The JSON shape is declared here instead.
    response_model=TripReportOut,
    response_model_exclude_none=False,
    dependencies=[Depends(require_any(Permission.report_view, Permission.report_operational_view))],
)
async def trip_report(
    service: ServiceDep,
    current_user: CurrentUserDep,
    start: Annotated[date, Query(alias="from")],
    end: Annotated[date, Query(alias="to")],
    client_id: uuid.UUID | None = None,
    report_format: Annotated[Literal["json", "csv"], Query(alias="format")] = "json",
) -> Any:
    operator_id = _operator_id(current_user)

    # A client admin sees their own client and no other, whatever they ask for. The
    # permission lets them through the door; this decides which rows exist for them.
    if current_user.active_role is Role.client_admin:
        client_id = current_user.claims.client_id

    report = await service.trip_report(operator_id, start, end, client_id)

    if report_format == "csv":
        return Response(
            content=report.as_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="trips_{start}_{end}.csv"'},
        )
    return TripReportOut(**report.as_dict())
