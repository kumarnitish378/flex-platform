"""The night escort gate (owner decision 3, 2026-11-01; OQ-10; `domain/night_escort.py`).

The platform **flags**; a supervisor **confirms**; nothing is arranged automatically. A flagged trip
shows on the dispatch board and trip detail, raises an `escort_required` alert, and cannot be
started by the driver until a supervisor has attested `escort_arranged` or `male_co_rider_present`.
Who confirmed, when and on what basis is on the trip and in its event history.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.enums import ActorType, AlertType
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.night_escort import EscortBasis, escort_required
from app.domain.policy import EffectivePolicy
from app.domain.state_machines import RequestStatus, TripStatus
from app.domain.timeofday import local_time
from app.modules.alerts.models import Alert
from app.modules.alerts.service import AlertService
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip, TripEvent
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Operator
from app.modules.tenancy.policy_service import ClientPolicyService

logger = get_logger(__name__)

#: Trips that have not left yet. After that the gate has done its job.
NOT_STARTED = (TripStatus.planned, TripStatus.dispatched)
#: Requests that count as "in the cab" for the only-rider test.
RIDING = (RequestStatus.assigned, RequestStatus.picked_up)


@dataclass(frozen=True, slots=True)
class EscortStatus:
    required: bool
    confirmed: bool
    basis: str | None = None
    confirmed_by: uuid.UUID | None = None
    confirmed_at: datetime | None = None
    note: str | None = None

    @property
    def blocks_start(self) -> bool:
        return self.required and not self.confirmed


class EscortService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        config: ConfigService | None = None,
        alerts: AlertService | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.config = config or ConfigService(session, clock)
        self.alerts = alerts or AlertService(session, clock)

    # --- the question ---------------------------------------------------------------

    async def assess(self, trips: Iterable[Trip]) -> dict[uuid.UUID, EscortStatus]:
        """One status per trip, in a handful of queries however many trips there are."""
        trips = list(trips)
        if not trips:
            return {}
        rows = (
            await self.session.execute(
                select(RideRequest.trip_id, Employee.gender, Employee.client_id)
                .join(Employee, Employee.id == RideRequest.employee_id)
                .where(RideRequest.trip_id.in_([trip.id for trip in trips]))
                .where(RideRequest.status.in_([str(status) for status in RIDING]))
            )
        ).all()
        riders: dict[uuid.UUID, list[tuple[str | None, uuid.UUID]]] = {}
        for trip_id, gender, client_id in rows:
            riders.setdefault(trip_id, []).append((gender, client_id))

        now = self.clock.now()
        policies: dict[uuid.UUID, dict[uuid.UUID, EffectivePolicy]] = {}
        zones: dict[uuid.UUID, str] = {}
        result: dict[uuid.UUID, EscortStatus] = {}
        for trip in trips:
            operator_id = trip.operator_id
            if operator_id not in zones:
                zones[operator_id] = str(
                    await self.session.scalar(
                        select(Operator.timezone).where(Operator.id == operator_id)
                    )
                    or "UTC"
                )
                client_ids = {
                    client
                    for other in trips
                    if other.operator_id == operator_id
                    for _, client in riders.get(other.id, [])
                }
                policies[operator_id] = await ClientPolicyService(
                    self.session, self.clock, self.config
                ).effective(operator_id, client_ids)
            on_trip = riders.get(trip.id, [])
            needs = False
            if TripStatus(trip.status) in NOT_STARTED and len(on_trip) == 1:
                gender, client_id = on_trip[0]
                policy = policies[operator_id].get(client_id)
                if policy is not None:
                    needs = escort_required(
                        enabled=policy.night_safety_enabled,
                        local_time=local_time(now, zones[operator_id]),
                        night_start=policy.night_start,
                        night_end=policy.night_end,
                        genders=[gender],
                    )
            result[trip.id] = EscortStatus(
                required=needs,
                confirmed=trip.escort_basis is not None,
                basis=trip.escort_basis,
                confirmed_by=trip.escort_confirmed_by,
                confirmed_at=trip.escort_confirmed_at,
                note=trip.escort_note,
            )
        return result

    async def require_cleared(self, trip: Trip) -> None:
        """Refuse to start a flagged trip nobody has confirmed (the driver's start calls this)."""
        status = (await self.assess([trip]))[trip.id]
        if status.blocks_start:
            # No alert is raised here: the refusal rolls this request back. The sweep owns alerts.
            raise Conflict(
                "A woman would be the only rider in the cab at night. A supervisor has to confirm "
                "an escort is arranged, or a male co-rider is present, before this trip starts.",
                {"reason": "escort_confirmation_required", "trip_id": str(trip.id)},
            )

    # --- the supervisor's confirmation ---------------------------------------------------

    async def confirm(
        self,
        operator_id: uuid.UUID,
        user_id: uuid.UUID,
        trip_id: uuid.UUID,
        basis: str,
        note: str | None = None,
    ) -> Trip:
        try:
            chosen = EscortBasis(basis)
        except ValueError:
            raise ValidationFailed(
                "basis must be escort_arranged or male_co_rider_present", {"basis": basis}
            ) from None

        trip = await self.session.scalar(
            select(Trip).where(Trip.id == trip_id).where(Trip.operator_id == operator_id)
        )
        if trip is None:
            raise NotFound("Trip not found")
        if TripStatus(trip.status) not in NOT_STARTED:
            raise Conflict("The trip has already started", {"trip_status": trip.status})
        if not (await self.assess([trip]))[trip.id].required:
            raise Conflict(
                "This trip does not need an escort confirmation",
                {"reason": "escort_not_required"},
            )

        now = self.clock.now()
        trip.escort_basis = str(chosen)
        trip.escort_confirmed_by = user_id
        trip.escort_confirmed_at = now
        trip.escort_note = note
        self.session.add(
            TripEvent(
                operator_id=operator_id,
                trip_id=trip.id,
                from_status=trip.status,
                to_status=trip.status,
                actor_type=ActorType.supervisor,
                actor_user_id=user_id,
                reason=f"escort_confirmed:{chosen}",
                at=now,
            )
        )
        await self.session.flush()
        await self.sweep(operator_id)
        logger.info(
            "escort_confirmed",
            trip_id=str(trip.id),
            confirmed_by=str(user_id),
            basis=str(chosen),
        )
        return trip

    # --- alerts ----------------------------------------------------------------------------

    async def sweep(self, operator_id: uuid.UUID | None = None) -> tuple[int, int]:
        """Raise an alert per flagged, unconfirmed trip; resolve it once it no longer applies.

        Due work like the stale-vehicle sweep: a clock jump into the night window must flag the
        trips the window has just caught.
        """
        query = select(Trip).where(Trip.status.in_([str(status) for status in NOT_STARTED]))
        if operator_id is not None:
            query = query.where(Trip.operator_id == operator_id)
        trips = list((await self.session.execute(query)).scalars())
        statuses = await self.assess(trips)

        raised = cleared = 0
        for trip in trips:
            status = statuses[trip.id]
            open_alerts = list(
                (
                    await self.session.execute(
                        select(Alert)
                        .where(Alert.operator_id == trip.operator_id)
                        .where(Alert.type == str(AlertType.escort_required))
                        .where(Alert.trip_id == trip.id)
                        .where(Alert.status != "resolved")
                    )
                ).scalars()
            )
            if status.blocks_start and not open_alerts:
                await self.alerts.raise_alert(
                    trip.operator_id,
                    AlertType.escort_required,
                    data={"reason": "woman_only_rider_at_night"},
                    trip_id=trip.id,
                    vehicle_id=trip.vehicle_id,
                )
                raised += 1
            elif not status.blocks_start:
                for alert in open_alerts:
                    alert.status = "resolved"
                    alert.resolved_at = self.clock.now()
                    await self.alerts.announce_change(alert)
                    cleared += 1
        if raised or cleared:
            await self.session.flush()
        return raised, cleared
