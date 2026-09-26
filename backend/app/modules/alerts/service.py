"""Alerts: raising them, listing them, and closing them (B17, EMP-08, DRV-06).

An alert is the product admitting something needs a human. Three things follow from that:

* **Raising one is never blocked.** An SOS from a rider in trouble must not fail because
  the trip id was wrong or the vehicle is unknown. Everything except the operator and the
  position is optional.
* **Nobody is told twice about the same thing.** A vehicle that has been quiet for ten
  minutes is one alert, not twenty. Deduplication is on the open alert, so acknowledging
  and then going quiet again does raise a new one.
* **SOS goes out before anything else.** It is published to the supervisor channel
  immediately (B17 acceptance: within 2 seconds), and the notification is high priority.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.events import Event, EventPublisher, NullEventPublisher, operator_channel
from app.core.logging import get_logger
from app.domain.enums import AlertSeverity, AlertStatus, AlertType
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.notifications import NotificationType
from app.domain.state_machines import (
    TERMINAL_TRIP_STATUSES,
    Actor,
    RequestContext,
    RequestStatus,
    StopStatus,
    TripStatus,
    VehicleStatus,
    transition_request,
    transition_stop,
    transition_trip,
    transition_vehicle,
)
from app.modules.alerts.models import Alert
from app.modules.config.service import ConfigService
from app.modules.fleet.models import Vehicle
from app.modules.notifications.service import Audience, NotificationService

logger = get_logger(__name__)

#: DRV-06: what a driver can report.
ISSUE_TYPES = ("breakdown", "accident", "traffic_block", "rider_issue", "other")

#: DRV-06: "breakdown marks the vehicle `out_of_service` pending supervisor confirmation".
ISSUE_TAKES_VEHICLE_OFF_ROAD = frozenset({"breakdown", "accident"})

#: How severe each alert type is. Kept as a table so a new type cannot default to silence.
SEVERITY: dict[AlertType, AlertSeverity] = {
    AlertType.sos: AlertSeverity.critical,
    AlertType.driver_issue: AlertSeverity.warning,
    AlertType.request_near_expiry: AlertSeverity.warning,
    # Manual phase: informational. The supervisor decides, so this is a prompt, not a
    # failure (`allocation-rules.md` section 2 rule 4, OQ-12).
    AlertType.vip_no_vehicle: AlertSeverity.info,
    AlertType.failsafe: AlertSeverity.warning,
    AlertType.stale_vehicle: AlertSeverity.warning,
    AlertType.mode_prompt: AlertSeverity.info,
    AlertType.system: AlertSeverity.warning,
}

OPEN_STATUSES = (AlertStatus.open, AlertStatus.acknowledged)


@dataclass(frozen=True, slots=True)
class StaleSweep:
    raised: int = 0


class AlertService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        events: EventPublisher | None = None,
        notifications: NotificationService | None = None,
        config: ConfigService | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.events = events or NullEventPublisher()
        self.notifications = notifications or NotificationService(session, clock)
        self.config = config or ConfigService(session, clock)

    # --- raising ---------------------------------------------------------------------

    async def raise_alert(
        self,
        operator_id: uuid.UUID,
        alert_type: AlertType,
        data: dict[str, Any] | None = None,
        request_id: uuid.UUID | None = None,
        trip_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        dedupe: bool = False,
    ) -> Alert | None:
        """Record an alert and tell the people who can act on it.

        With `dedupe`, an existing open alert of the same type for the same subject wins
        and `None` comes back: a vehicle quiet for ten minutes is one alert, not twenty.
        """
        if dedupe and await self._already_open(operator_id, alert_type, vehicle_id, request_id):
            return None

        alert = Alert(
            operator_id=operator_id,
            type=alert_type,
            severity=SEVERITY.get(alert_type, AlertSeverity.warning),
            request_id=request_id,
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            data=data,
            status=AlertStatus.open,
        )
        self.session.add(alert)
        await self.session.flush()

        await self.events.publish(
            Event(
                f"alert.{alert_type}",
                operator_channel(operator_id, "alerts"),
                {
                    "alert_id": str(alert.id),
                    "type": str(alert_type),
                    "severity": alert.severity,
                    "trip_id": str(trip_id) if trip_id else None,
                    "vehicle_id": str(vehicle_id) if vehicle_id else None,
                    **(data or {}),
                },
            )
        )
        logger.info(
            "alert_raised",
            alert_id=str(alert.id),
            alert_type=str(alert_type),
            severity=alert.severity,
        )
        return alert

    async def sos(
        self,
        operator_id: uuid.UUID,
        user_id: uuid.UUID,
        lat: float,
        lng: float,
        trip_id: uuid.UUID | None = None,
    ) -> Alert:
        """EMP-08: an emergency, with live location, to supervisor and operator admin.

        Deliberately the most forgiving path in the codebase. Nothing about the trip is
        validated: someone pressing this button is not in a position to have got the
        payload right, and a refused SOS is the worst failure this product can have.
        """
        alert = await self.raise_alert(
            operator_id,
            AlertType.sos,
            data={"lat": lat, "lng": lng, "raised_by": str(user_id)},
            trip_id=trip_id,
        )
        assert alert is not None  # never deduplicated
        await self.notifications.notify(
            NotificationType.sos,
            Audience(operator_id=operator_id),
            {"alert_id": str(alert.id), "trip_id": str(trip_id) if trip_id else None},
        )
        return alert

    async def driver_issue(
        self,
        operator_id: uuid.UUID,
        driver_user_id: uuid.UUID,
        issue_type: str,
        note: str | None = None,
        trip_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> Alert:
        """DRV-06. A breakdown or accident also takes the vehicle off the road."""
        if issue_type not in ISSUE_TYPES:
            raise ValidationFailed(
                f"Unknown issue type: {issue_type}", {"allowed": list(ISSUE_TYPES)}
            )

        alert = await self.raise_alert(
            operator_id,
            AlertType.driver_issue,
            data={
                "issue_type": issue_type,
                "note": note,
                "lat": lat,
                "lng": lng,
                "reported_by": str(driver_user_id),
            },
            trip_id=trip_id,
            vehicle_id=vehicle_id,
        )
        assert alert is not None

        if issue_type in ISSUE_TAKES_VEHICLE_OFF_ROAD and vehicle_id is not None:
            await self._take_off_road(vehicle_id)
            await self._abort_the_trip(vehicle_id)

        # DRV-06 says "supervisor is alerted", which is the alert itself plus the event on
        # the operator's alerts channel. No push: a breakdown is urgent for whoever is
        # watching the board, not a reason to wake every supervisor's phone.
        return alert

    async def _take_off_road(self, vehicle_id: uuid.UUID) -> None:
        """DRV-06: "pending supervisor confirmation" - the driver reports, we act.

        A broken-down cab must stop being a dispatch candidate immediately; waiting for a
        supervisor to confirm would keep assigning riders to a vehicle on a hard shoulder.
        """
        vehicle = await self.session.scalar(select(Vehicle).where(Vehicle.id == vehicle_id))
        if vehicle is None or vehicle.status == str(VehicleStatus.out_of_service):
            return
        transition = transition_vehicle(
            VehicleStatus(vehicle.status), VehicleStatus.out_of_service, actor=Actor.driver
        )
        vehicle.status = transition.to_status
        logger.info("vehicle_out_of_service", vehicle_id=str(vehicle_id), reason="driver_issue")

    async def _abort_the_trip(self, vehicle_id: uuid.UUID) -> None:
        """`trip-lifecycle.md`: `in_progress --> aborted: breakdown / emergency`.

        Taking the cab off the road is not enough on its own. Without this the trip stays
        open, and the driver of a cab on the hard shoulder can go on marking stops
        arrived and completing the ride - which the S05 scenario showed happening.

        Riders who had not been collected go back on the queue for the supervisor to
        reassign, which is the `assigned -> queued` edge the state machine already has.
        A rider already **in** the broken cab has no such edge and is left on the aborted
        trip: `trip-lifecycle.md` says they "get new handling by supervisor" without
        saying what that is, and inventing a transition here would be guessing (OQ-27).
        """
        from app.modules.dispatch.models import Trip, TripStop
        from app.modules.requests.models import RideRequest

        trip = await self.session.scalar(
            select(Trip)
            .where(Trip.vehicle_id == vehicle_id)
            .where(Trip.status.notin_([str(item) for item in TERMINAL_TRIP_STATUSES]))
        )
        if trip is None:
            return

        # `trip-lifecycle.md` section 2 distinguishes the two by whether the trip had
        # started: `cancelled` is "before start", `aborted` is "stopped mid-way". A cab
        # that breaks down in the depot cancels its trip; one that breaks down carrying
        # riders aborts it.
        current = TripStatus(trip.status)
        ending = TripStatus.aborted if current is TripStatus.in_progress else TripStatus.cancelled
        trip.status = transition_trip(current, ending, actor=Actor.driver).to_status

        stops = (
            (await self.session.execute(select(TripStop).where(TripStop.trip_id == trip.id)))
            .scalars()
            .all()
        )
        stranded: list[uuid.UUID] = []
        for stop in stops:
            if stop.status in {str(StopStatus.done), str(StopStatus.skipped)}:
                continue
            stop.status = transition_stop(
                StopStatus(stop.status), StopStatus.skipped, actor=Actor.system
            ).to_status
            if stop.request_id is not None:
                stranded.append(stop.request_id)

        requeued = 0
        for request_id in set(stranded):
            request = await self.session.scalar(
                select(RideRequest).where(RideRequest.id == request_id)
            )
            if request is None or request.status != str(RequestStatus.assigned):
                continue
            request.status = transition_request(
                RequestStatus.assigned,
                RequestStatus.queued,
                RequestContext(actor=Actor.system, reason="vehicle_breakdown"),
            ).to_status
            request.trip_id = None
            requeued += 1

        logger.info(
            "trip_ended_by_driver_issue",
            trip_id=str(trip.id),
            vehicle_id=str(vehicle_id),
            reason="driver_issue",
            ended_as=str(ending),
            requeued=requeued,
        )

    async def vip_without_vehicle(
        self, operator_id: uuid.UUID, request_id: uuid.UUID
    ) -> Alert | None:
        """`allocation-rules.md` section 2 rule 4: alert, never auto-assign a normal cab."""
        return await self.raise_alert(
            operator_id,
            AlertType.vip_no_vehicle,
            data={"request_id": str(request_id)},
            request_id=request_id,
            dedupe=True,
        )

    async def vehicle_on_duty_for(self, driver_user_id: uuid.UUID) -> uuid.UUID | None:
        """The cab this driver is signed into right now.

        Resolved here rather than taken from the request body: a driver reporting a
        breakdown must not be able to take another driver's vehicle off the road.
        """
        from app.modules.fleet.duty_models import DutySession
        from app.modules.fleet.models import Driver

        vehicle_id: uuid.UUID | None = await self.session.scalar(
            select(DutySession.vehicle_id)
            .join(Driver, Driver.id == DutySession.driver_id)
            .where(Driver.user_id == driver_user_id)
            .where(DutySession.ended_at.is_(None))
        )
        return vehicle_id

    # --- the stale-vehicle sweep ---------------------------------------------------

    async def sweep_stale_vehicles(self, operator_id: uuid.UUID | None = None) -> StaleSweep:
        """One alert per on-duty vehicle that has gone quiet (SUP-01).

        Clock-driven due work, like the expiry and ETA sweeps, so `/simctl/clock` runs it.
        """
        from app.modules.fleet.duty_models import DutySession
        from app.modules.tracking.service import GpsIngestor

        query = select(DutySession.operator_id, DutySession.vehicle_id).where(
            DutySession.ended_at.is_(None)
        )
        if operator_id is not None:
            query = query.where(DutySession.operator_id == operator_id)
        on_duty = list((await self.session.execute(query)).all())

        raised = 0
        ingestor = GpsIngestor(self.session, self.clock)
        for operator, _vehicle in {(row[0], row[1]) for row in on_duty}:
            stale_after = int(await self.config.get(operator, "stale_gps_seconds"))
            for vehicle_id in await ingestor.stale_vehicles(operator, stale_after):
                alert = await self.raise_alert(
                    operator,
                    AlertType.stale_vehicle,
                    data={"stale_after_seconds": stale_after},
                    vehicle_id=vehicle_id,
                    dedupe=True,
                )
                raised += 1 if alert is not None else 0

        if raised:
            logger.info("stale_vehicle_sweep", raised=raised)
        return StaleSweep(raised=raised)

    # --- reading and closing ----------------------------------------------------------

    async def list_alerts(self, operator_id: uuid.UUID, status: str | None = None) -> list[Alert]:
        """Newest first: a supervisor's alert list is read from the top."""
        query = (
            select(Alert).where(Alert.operator_id == operator_id).order_by(Alert.created_at.desc())
        )
        if status is not None:
            query = query.where(Alert.status == status)
        return list((await self.session.execute(query)).scalars().all())

    async def acknowledge(
        self, operator_id: uuid.UUID, alert_id: uuid.UUID, user_id: uuid.UUID
    ) -> Alert:
        alert = await self._alert(operator_id, alert_id)
        if alert.status == str(AlertStatus.resolved):
            raise Conflict("A resolved alert cannot be acknowledged", {"status": alert.status})
        if alert.status == str(AlertStatus.acknowledged):
            return alert

        alert.status = AlertStatus.acknowledged
        alert.acknowledged_by = user_id
        await self._announce_change(alert)
        return alert

    async def resolve(
        self, operator_id: uuid.UUID, alert_id: uuid.UUID, user_id: uuid.UUID
    ) -> Alert:
        alert = await self._alert(operator_id, alert_id)
        if alert.status == str(AlertStatus.resolved):
            return alert

        alert.status = AlertStatus.resolved
        alert.resolved_at = self.clock.now()
        if alert.acknowledged_by is None:
            # Resolving without acknowledging first is normal for a quick fix; record who.
            alert.acknowledged_by = user_id
        await self._announce_change(alert)
        return alert

    async def _announce_change(self, alert: Alert) -> None:
        await self.session.flush()
        await self.events.publish(
            Event(
                "alert.resolved" if alert.status == str(AlertStatus.resolved) else "alert.updated",
                operator_channel(alert.operator_id, "alerts"),
                {"alert_id": str(alert.id), "status": alert.status},
            )
        )

    async def _alert(self, operator_id: uuid.UUID, alert_id: uuid.UUID) -> Alert:
        alert = await self.session.scalar(
            select(Alert).where(Alert.id == alert_id).where(Alert.operator_id == operator_id)
        )
        if alert is None:
            # Another operator's alert is a 404, not a 403.
            raise NotFound("Alert not found")
        return alert

    async def _already_open(
        self,
        operator_id: uuid.UUID,
        alert_type: AlertType,
        vehicle_id: uuid.UUID | None,
        request_id: uuid.UUID | None,
    ) -> bool:
        query = (
            select(Alert.id)
            .where(Alert.operator_id == operator_id)
            .where(Alert.type == str(alert_type))
            .where(Alert.status.in_([str(status) for status in OPEN_STATUSES]))
        )
        query = (
            query.where(Alert.vehicle_id == vehicle_id)
            if vehicle_id is not None
            else query.where(Alert.request_id == request_id)
        )
        return await self.session.scalar(query) is not None
