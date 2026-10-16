"""`/dispatch/*` (`api-spec.yaml`) - the supervisor's board (B14)."""

from __future__ import annotations

import uuid
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.dependencies import (
    ClockDep,
    CurrentUserDep,
    EtaDep,
    EventsDep,
    PushDep,
    SessionDep,
)
from app.core.geo import coords
from app.domain.enums import Direction
from app.domain.errors import Forbidden
from app.domain.state_machines import Actor
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.override_service import Impact, OverrideService
from app.modules.dispatch.schemas import (
    AddedMinutes,
    AffectedRequestOut,
    AssignInput,
    AutomationInput,
    AutomationOut,
    CandidateOut,
    ImpactOut,
    OverrideInput,
    OverrideResultOut,
    TripOut,
    TripStopOut,
    VehicleLiveOut,
)
from app.modules.dispatch.semi_auto import SemiAutoService, SupervisorDecision
from app.modules.dispatch.service import Candidate, DispatchService, VehicleLive
from app.modules.notifications.service import NotificationService
from app.modules.requests.router import _out as _request_out
from app.modules.requests.schemas import LatLng, RideRequestOut

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


def _operator_id(current_user: CurrentUserDep) -> uuid.UUID:
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")
    return operator_id


def _service(
    session: SessionDep, clock: ClockDep, eta: EtaDep, events: EventsDep, push: PushDep
) -> DispatchService:
    return DispatchService(
        session,
        clock,
        eta,
        events=events,
        notifications=NotificationService(session, clock, push),
    )


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


@router.get(
    "/requests/{request_id}/suggestions",
    summary="The system's top recommendations for this request",
    dependencies=[Depends(require(Permission.assign))],
)
async def list_suggestions(
    request_id: uuid.UUID,
    service: ServiceDep,
    current_user: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=10)] = 3,
) -> dict[str, list[CandidateOut]]:
    """Scored candidates that break no hard rule, best first.

    Deliberately not the first three of `/candidates`: that list includes vehicles with
    violations so a supervisor can see the only cab within reach is over the limit. A
    suggestion is the system recommending something, and `allocation-rules.md` §2 makes
    the rules filters there.
    """
    suggestions = await service.suggestions(_operator_id(current_user), request_id, limit=limit)
    return {"items": [_candidate_out(candidate) for candidate in suggestions]}


class SuggestionDecisionBody(BaseModel):
    decision: SupervisorDecision
    #: Required for `choose_other`, ignored otherwise.
    vehicle_id: uuid.UUID | None = None
    reason_code: str | None = None
    note: str | None = None


class SuggestionDecisionOut(BaseModel):
    suggestion_id: uuid.UUID
    decision: SupervisorDecision
    status: str
    trip_id: uuid.UUID | None = None


@router.post(
    "/suggestions/{suggestion_id}/decision",
    summary="Approve, change or reject one of the system's suggestions",
    dependencies=[Depends(require(Permission.assign))],
)
async def decide_on_suggestion(
    suggestion_id: uuid.UUID,
    body: SuggestionDecisionBody,
    service: ServiceDep,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> SuggestionDecisionOut:
    """`control-model.md` §1's "one-tap approve or override", as three decisions.

    `choose_other` is recorded as a rejection of what was offered, with the chosen
    vehicle noted - it is a different ride, and counting it as acceptance would let the
    Phase 2 metric flatter itself.
    """
    result = await SemiAutoService(session, clock, service).decide_on(
        operator_id=_operator_id(current_user),
        suggestion_id=suggestion_id,
        decision=body.decision,
        actor=Actor(str(current_user.active_role)),
        actor_user_id=current_user.claims.user_id,
        vehicle_id=body.vehicle_id,
        note=body.note,
    )
    return SuggestionDecisionOut(
        suggestion_id=result.suggestion_id,
        decision=result.decision,
        status=str(result.status),
        trip_id=result.trip_id,
    )


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


@router.post(
    "/overrides",
    summary="Apply one of the override actions (control-model.md §3)",
    dependencies=[Depends(require(Permission.override))],
)
async def apply_override(
    body: OverrideInput,
    service: ServiceDep,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> OverrideResultOut:
    """Every override carries a reason, an expiry and an `override_log` row (§3 rules 3, 5, 6).

    The impact is computed before anything changes, because rule 4 cannot decide which
    reason codes are allowed until it knows whether a hard rule is being waived.
    """
    result = await OverrideService(session, clock, service).apply(
        operator_id=_operator_id(current_user),
        command=body.to_command(),
        actor=Actor(str(current_user.active_role)),
        actor_user_id=current_user.claims.user_id,
    )
    return OverrideResultOut(
        override_id=result.override_id,
        impact=_impact_out(result.impact),
        expires_at=result.expires_at,
        trip_id=result.trip_id,
    )


@router.post(
    "/overrides/preview",
    summary="What an override would do, without doing it (§3 rule 2)",
    dependencies=[Depends(require(Permission.override))],
)
async def preview_override(
    body: OverrideInput,
    service: ServiceDep,
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> ImpactOut:
    impact = await OverrideService(session, clock, service).preview(
        operator_id=_operator_id(current_user), command=body.to_command()
    )
    return _impact_out(impact)


@router.get(
    "/trips",
    summary="Every trip for the operator, with stops - one read for a whole board",
    dependencies=[Depends(require(Permission.request_queue_view))],
)
async def list_trips(
    service: ServiceDep,
    current_user: CurrentUserDep,
    status: Annotated[list[str] | None, Query()] = None,
) -> dict[str, list[TripOut]]:
    operator_id = _operator_id(current_user)
    trips = await service.trips(operator_id, status)
    # One stop query for every trip, not one per trip: see `stops_by_trip`.
    stops = await service.stops_by_trip([trip.id for trip in trips])
    return {"items": [_trip_with_stops(trip, stops.get(trip.id, [])) for trip in trips]}


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


def _impact_out(impact: Impact) -> ImpactOut:
    return ImpactOut(
        affected_requests=[
            AffectedRequestOut(
                request_id=affected.request_id,
                employee_name=affected.employee_name,
                added_minutes=affected.added_minutes,
                eta_change_minutes=affected.eta_change_minutes,
                requeued=affected.requeued,
            )
            for affected in impact.affected_requests
        ],
        zones_without_available_vehicle=impact.zones_without_available_vehicle,
        hard_rule_violations=[breach.summary for breach in impact.hard_rule_violations],
    )


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
        gps_age_seconds=candidate.gps_age_seconds,
        added_minutes_existing=[
            AddedMinutes(request_id=request_id, minutes=round(minutes, 1))
            for request_id, minutes in candidate.added_minutes.items()
        ],
        new_trip=candidate.new_trip,
        # Phase 1 declared both and left them empty; B22 and B23 fill them.
        cost=round(candidate.cost, 2) if candidate.cost is not None else None,
        reasons=candidate.reasons,
        violations=[str(violation) for violation in candidate.violations],
    )


class HasStops(Protocol):
    """Anything that can list a trip's stops - the dispatch and driver services both can."""

    async def stops_of(self, trip_id: uuid.UUID) -> list[TripStop]: ...


async def _trip_out(service: HasStops, trip: Trip) -> TripOut:
    return _trip_with_stops(trip, await service.stops_of(trip.id))


def _trip_with_stops(trip: Trip, stops: list[TripStop]) -> TripOut:
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
