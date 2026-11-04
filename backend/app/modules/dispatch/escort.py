"""The night escort gate (owner decisions 2026-11-01 and 11-02; OQ-10; `domain/night_escort.py`).

The platform **flags**; a supervisor **confirms**; nothing is arranged automatically. A flagged trip
shows on the dispatch board and trip detail, raises an `escort_required` alert, and cannot be
started by the driver until a supervisor has attested what the reason needs:

* `lone_rider` (a woman alone in the cab): `escort_arranged` or `male_co_rider_present`;
* `last_out` (a woman is the last rider left on a shared trip home): `escort_arranged` only - a man
  who shared the earlier part of the trip is gone by then.

Who confirmed, when and on what basis is on the trip and in its event history. The flag is worked
out from the trip as it is planned, so it appears when the trip is assigned, not when it is about
to leave.
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
from app.domain.enums import ActorType, AlertType, Direction
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.night_escort import EscortBasis, EscortReason, accepted_bases, escort_reason
from app.domain.policy import EffectivePolicy
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, TripStatus
from app.domain.timeofday import local_time
from app.modules.alerts.models import Alert
from app.modules.alerts.service import AlertService
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip, TripEvent, TripStop
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Operator
from app.modules.tenancy.policy_service import ClientPolicyService

logger = get_logger(__name__)

#: Trips that have not left yet. After that the gate has done its job.
NOT_STARTED = (TripStatus.planned, TripStatus.dispatched)
#: Requests that count as "in the cab" for the escort rules.
RIDING = (RequestStatus.assigned, RequestStatus.picked_up)

ALERT_DATA = {
    EscortReason.lone_rider: "woman_only_rider_at_night",
    EscortReason.last_out: "woman_last_out_at_night",
}
EXPLANATION = {
    EscortReason.lone_rider: (
        "A woman would be the only rider in the cab at night. A supervisor has to confirm an "
        "escort is arranged, or a male co-rider is present, before this trip starts."
    ),
    EscortReason.last_out: (
        "A woman would be the last rider left in the cab on the way home at night. A supervisor "
        "has to confirm an escort is arranged before this trip starts."
    ),
}


@dataclass(frozen=True, slots=True)
class EscortStatus:
    reason: EscortReason | None
    confirmed: bool
    basis: str | None = None
    confirmed_by: uuid.UUID | None = None
    confirmed_at: datetime | None = None
    note: str | None = None

    @property
    def required(self) -> bool:
        return self.reason is not None

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
        ids = [trip.id for trip in trips]
        rows = (
            await self.session.execute(
                select(RideRequest.trip_id, RideRequest.id, Employee.gender, Employee.client_id)
                .join(Employee, Employee.id == RideRequest.employee_id)
                .where(RideRequest.trip_id.in_(ids))
                .where(RideRequest.status.in_([str(status) for status in RIDING]))
            )
        ).all()
        riders: dict[uuid.UUID, dict[uuid.UUID, tuple[str | None, uuid.UUID]]] = {}
        for trip_id, request_id, gender, client_id in rows:
            riders.setdefault(trip_id, {})[request_id] = (gender, client_id)

        # The order people get out, from the planned stops: the last of them is "last out".
        drop_order: dict[uuid.UUID, list[uuid.UUID]] = {}
        stops = (
            await self.session.execute(
                select(TripStop.trip_id, TripStop.request_id)
                .where(TripStop.trip_id.in_(ids))
                .where(TripStop.stop_type == str(StopKind.drop))
                .where(TripStop.status != str(StopStatus.skipped))
                .order_by(TripStop.trip_id, TripStop.sequence)
            )
        ).all()
        for trip_id, request_id in stops:
            drop_order.setdefault(trip_id, []).append(request_id)

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
                    for _, client in riders.get(other.id, {}).values()
                }
                policies[operator_id] = await ClientPolicyService(
                    self.session, self.clock, self.config
                ).effective(operator_id, client_ids)

            on_trip = riders.get(trip.id, {})
            reason: EscortReason | None = None
            if TripStatus(trip.status) in NOT_STARTED and on_trip:
                ordered = [rid for rid in drop_order.get(trip.id, []) if rid in on_trip]
                # A rider with no drop stop yet (mid-planning) goes last: the cautious reading.
                ordered += [rid for rid in on_trip if rid not in ordered]
                # The strictest night policy among the riders decides: any client with the switch
                # on and the window open flags the trip.
                for rid in ordered:
                    policy = policies[operator_id].get(on_trip[rid][1])
                    if policy is None:
                        continue
                    found = escort_reason(
                        enabled=policy.night_safety_enabled,
                        local_time=local_time(now, zones[operator_id]),
                        night_start=policy.night_start,
                        night_end=policy.night_end,
                        direction=Direction(trip.direction),
                        genders_in_drop_order=[on_trip[r][0] for r in ordered],
                    )
                    if found is not None:
                        reason = found
                        break
            # A confirmation answers the reason it was given for: a trip that has since become a
            # different problem (a man who vouched for a lone woman got out, she is now last out)
            # has to be confirmed again.
            confirmed = trip.escort_basis is not None and (
                reason is None or EscortBasis(trip.escort_basis) in accepted_bases(reason)
            )
            result[trip.id] = EscortStatus(
                reason=reason,
                confirmed=confirmed,
                basis=trip.escort_basis,
                confirmed_by=trip.escort_confirmed_by,
                confirmed_at=trip.escort_confirmed_at,
                note=trip.escort_note,
            )
        return result

    async def require_cleared(self, trip: Trip) -> None:
        """Refuse to start a flagged trip nobody has confirmed (the driver's start calls this)."""
        status = (await self.assess([trip]))[trip.id]
        if status.blocks_start and status.reason is not None:
            # No alert is raised here: the refusal rolls this request back. The sweep owns alerts.
            raise Conflict(
                EXPLANATION[status.reason],
                {
                    "reason": "escort_confirmation_required",
                    "escort_reason": str(status.reason),
                    "trip_id": str(trip.id),
                },
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
        reason = (await self.assess([trip]))[trip.id].reason
        if reason is None:
            raise Conflict(
                "This trip does not need an escort confirmation",
                {"reason": "escort_not_required"},
            )
        if chosen not in accepted_bases(reason):
            raise ValidationFailed(
                "A male co-rider cannot clear this: the woman is the last rider left in the cab "
                "after he has been dropped. Arrange an escort.",
                {"basis": basis, "escort_reason": str(reason)},
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
        await self.sync([trip])
        logger.info(
            "escort_confirmed",
            trip_id=str(trip.id),
            confirmed_by=str(user_id),
            basis=str(chosen),
            escort_reason=str(reason),
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
        return await self.sync(list((await self.session.execute(query)).scalars()))

    async def sync(self, trips: list[Trip]) -> tuple[int, int]:
        """Bring the alerts for these trips in line with what is true now.

        Called when a trip is planned or changed (so the flag exists at planning time, not up to
        thirty seconds later), when it is confirmed, and by the periodic sweep.
        """
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
            if status.blocks_start and status.reason is not None and not open_alerts:
                await self.alerts.raise_alert(
                    trip.operator_id,
                    AlertType.escort_required,
                    data={"reason": ALERT_DATA[status.reason]},
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
