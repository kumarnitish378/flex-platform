"""`/dispatch/*` (`api-spec.yaml`) - the supervisor's board (B14)."""

from __future__ import annotations

import uuid
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import ClockDep, CurrentUserDep, EtaDep, EventsDep, SessionDep
from app.core.geo import coords
from app.domain.enums import Direction
from app.domain.errors import Forbidden
from app.domain.state_machines import Actor
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.schemas import (
    AddedMinutes,
    AssignInput,
    AutomationInput,
    AutomationOut,
    CandidateOut,
    TripOut,
    TripStopOut,
    VehicleLiveOut,
)
from app.modules.dispatch.service import Candidate, DispatchService, VehicleLive
from app.modules.requests.router import _out as _request_out
from app.modules.requests.schemas import LatLng, RideRequestOut

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _service(
    session: SessionDep, clock: ClockDep, eta: EtaDep, events: EventsDep
) -> DispatchService:
    return DispatchService(session, clock, eta, events=events)


ServiceDep = Annotated[DispatchService, Depends(_service)]


@router.get(
    "/requests",
    summary="Pending and active requests for the operator",
    dependencies=[Depends(require(Permission.request_queue_view))],
)
async def list_requests(
    service: ServiceDep,
    current_user: CurrentUserDep,
    status: Annotated[list[str] | None, Query()] = None,
    client_id: uuid.UUID | None = None,
) -> dict[str, list[RideRequestOut]]:
    requests = await service.requests(_operator_id(current_user), status, client_id)
    return {"items": [_request_out(request) for request in requests]}


@router.get(
    "/vehicles",
    summary="Snapshot of vehicles with live position and state",
    dependencies=[Depends(require(Permission.live_map_view))],
)
async def list_vehicles(
    service: ServiceDep, current_user: CurrentUserDep
) -> dict[str, list[VehicleLiveOut]]:
    vehicles = await service.live_vehicles(_operator_id(current_user))
    return {"items": [_vehicle_out(vehicle) for vehicle in vehicles]}


@router.get(
    "/requests/{request_id}/candidates",
    summary="Candidate vehicles with ETA and load, best first",
    dependencies=[Depends(require(Permission.assign))],
)
async def list_candidates(
    request_id: uuid.UUID, service: ServiceDep, current_user: CurrentUserDep
) -> dict[str, list[CandidateOut]]:
    candidates = await service.candidates(_operator_id(current_user), request_id)
    return {"items": [_candidate_out(candidate) for candidate in candidates]}


@router.post(
    "/assign",
    summary="Manually assign a request to a vehicle (new trip) or to an existing trip",
    dependencies=[Depends(require(Permission.assign))],
)
async def assign(body: AssignInput, service: ServiceDep, current_user: CurrentUserDep) -> TripOut:
    trip = await service.assign(
        operator_id=_operator_id(current_user),
        request_id=body.request_id,
        vehicle_id=body.vehicle_id,
        actor=Actor(str(current_user.active_role)),
        actor_user_id=current_user.claims.user_id,
        trip_id=body.trip_id,
        reason_code=body.reason_code,
        note=body.note,
    )
    return await _trip_out(service, trip)


@router.get(
    "/automation",
    summary="Whether automatic assignment is paused",
    dependencies=[Depends(require(Permission.request_queue_view))],
)
async def get_automation(service: ServiceDep, current_user: CurrentUserDep) -> AutomationOut:
    paused = await service.automation_paused(_operator_id(current_user))
    return AutomationOut(automation_paused=paused)


@router.put(
    "/automation",
    summary="Pause or resume all automatic assignment (SUP-05)",
    dependencies=[Depends(require(Permission.automation_pause))],
)
async def set_automation(
    body: AutomationInput, service: ServiceDep, current_user: CurrentUserDep
) -> AutomationOut:
    paused = await service.set_automation_paused(
        _operator_id(current_user), body.automation_paused, body.reason_code, body.note
    )
    return AutomationOut(automation_paused=paused)


# --- serialisation -------------------------------------------------------------------


def _latlng(location: object) -> LatLng:
    latitude, longitude = coords(location)
    return LatLng(lat=latitude, lng=longitude)


def _vehicle_out(live: VehicleLive) -> VehicleLiveOut:
    return VehicleLiveOut(
        id=live.vehicle.id,
        registration_no=live.vehicle.registration_no,
        model=live.vehicle.model,
        vehicle_type=live.vehicle.vehicle_type,
        seat_capacity=live.vehicle.seat_capacity,
        status=live.vehicle.status,
        position=(
            LatLng(lat=live.position.lat, lng=live.position.lng)
            if live.position is not None
            else None
        ),
        position_at=live.position.recorded_at if live.position is not None else None,
        stale=live.stale,
        active_trip_id=live.active_trip_id,
        seats_free=live.seats_free,
    )


def _candidate_out(candidate: Candidate) -> CandidateOut:
    return CandidateOut(
        vehicle_id=candidate.vehicle.id,
        registration_no=candidate.vehicle.registration_no,
        trip_id=candidate.trip_id,
        eta_to_pickup_seconds=int(candidate.eta_to_pickup_seconds),
        eta_approximate=candidate.eta_approximate,
        seats_free_after=candidate.seats_free_after,
        added_minutes_existing=[
            AddedMinutes(request_id=request_id, minutes=round(minutes, 1))
            for request_id, minutes in candidate.added_minutes.items()
        ],
        new_trip=candidate.new_trip,
        violations=[str(violation) for violation in candidate.violations],
    )


class HasStops(Protocol):
    """Anything that can list a trip's stops - the dispatch and driver services both can."""

    async def stops_of(self, trip_id: uuid.UUID) -> list[TripStop]: ...


async def _trip_out(service: HasStops, trip: Trip) -> TripOut:
    stops = await service.stops_of(trip.id)
    return TripOut(
        id=trip.id,
        vehicle_id=trip.vehicle_id,
        driver_id=trip.driver_id,
        direction=Direction(trip.direction),
        office_id=trip.office_id,
        status=trip.status,
        pooling_blocked=trip.pooling_blocked,
        mode_used=trip.mode_used,
        stops=[
            TripStopOut(
                id=stop.id,
                sequence=stop.sequence,
                stop_type=stop.stop_type,
                request_id=stop.request_id,
                location=_latlng(stop.location),
                status=stop.status,
                planned_eta=stop.planned_eta,
                latest_eta=stop.latest_eta,
                eta_approximate=stop.eta_approximate,
                arrived_at=stop.arrived_at,
                done_at=stop.done_at,
            )
            for stop in stops
        ],
    )
