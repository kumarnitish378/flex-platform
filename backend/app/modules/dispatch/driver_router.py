"""`/driver/trips*` and `/driver/stops/*` (`api-spec.yaml`) - DRV-03 and DRV-05 (B15)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import ClockDep, CurrentUserDep, EventsDep, SessionDep
from app.domain.driver_actions import StopAction
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.dispatch.driver_service import DriverEvent, DriverTripService
from app.modules.dispatch.models import Trip
from app.modules.dispatch.router import _trip_out
from app.modules.dispatch.schemas import DriverEventInput, TripOut

router = APIRouter(prefix="/driver", tags=["driver"])


def _service(session: SessionDep, clock: ClockDep, events: EventsDep) -> DriverTripService:
    return DriverTripService(session, clock, events=events)


ServiceDep = Annotated[DriverTripService, Depends(_service)]


def _event(body: DriverEventInput) -> DriverEvent:
    return DriverEvent(
        client_event_id=body.client_event_id,
        occurred_at=body.occurred_at,
        lat=body.lat,
        lng=body.lng,
    )


@router.get(
    "/trips",
    summary="My trips (DRV-03)",
    dependencies=[Depends(require(Permission.trip_view))],
)
async def list_trips(
    service: ServiceDep,
    current_user: CurrentUserDep,
    scope: Annotated[str, Query()] = "active",
) -> dict[str, list[TripOut]]:
    trips = await service.trips(current_user.claims.user_id, scope)
    return {"items": [await _out(service, trip) for trip in trips]}


@router.post(
    "/trips/{trip_id}/start",
    summary="Start the trip (DRV-05)",
    dependencies=[Depends(require(Permission.trip_action))],
)
async def start_trip(
    trip_id: uuid.UUID, body: DriverEventInput, service: ServiceDep, current_user: CurrentUserDep
) -> TripOut:
    trip = await service.start(current_user.claims.user_id, trip_id, _event(body))
    return await _out(service, trip)


@router.post(
    "/trips/{trip_id}/complete",
    summary="Complete the trip (DRV-05)",
    dependencies=[Depends(require(Permission.trip_action))],
)
async def complete_trip(
    trip_id: uuid.UUID, body: DriverEventInput, service: ServiceDep, current_user: CurrentUserDep
) -> TripOut:
    trip = await service.complete(current_user.claims.user_id, trip_id, _event(body))
    return await _out(service, trip)


@router.post(
    "/stops/{stop_id}/{action}",
    summary="Arrived / picked up or dropped / no-show (DRV-05)",
    description="Idempotent via client_event_id. Offline events carry the original occurred_at.",
    dependencies=[Depends(require(Permission.trip_action))],
)
async def stop_action(
    stop_id: uuid.UUID,
    action: StopAction,
    body: DriverEventInput,
    service: ServiceDep,
    current_user: CurrentUserDep,
) -> TripOut:
    trip = await service.stop_action(current_user.claims.user_id, stop_id, action, _event(body))
    return await _out(service, trip)


async def _out(service: DriverTripService, trip: Trip) -> TripOut:
    """Same shape as the dispatch view: one Trip schema, one serialiser."""
    return await _trip_out(service, trip)
