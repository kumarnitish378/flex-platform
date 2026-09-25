"""Going on and off duty, and the MQTT credentials that come with it (B11).

DRV-02: going on duty makes the vehicle assignable and starts GPS; going off duty stops
GPS and is **blocked while a trip is in progress**.

Credentials are issued per duty session, not per vehicle for all time: a driver who hands
the cab over should not still be able to publish as it. The plaintext password is returned
exactly once and only its Mosquitto hash is stored.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.core.settings import Settings
from app.domain.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.domain.mqtt_credentials import (
    VehicleCredential,
    build_acl_file,
    build_password_file,
    generate_password,
    hash_password,
    topic_prefix,
    username_for,
)
from app.domain.state_machines import Actor, VehicleStatus, transition_vehicle
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MqttCredentials:
    host: str
    port: int
    username: str
    password: str
    topic_prefix: str


@dataclass(frozen=True, slots=True)
class DutyState:
    on_duty: bool
    vehicle_id: uuid.UUID | None
    mqtt: MqttCredentials | None


class DutyService:
    def __init__(self, session: AsyncSession, clock: Clock, settings: Settings) -> None:
        self.session = session
        self.clock = clock
        self.settings = settings

    async def set_duty(
        self,
        operator_id: uuid.UUID,
        user_id: uuid.UUID,
        on_duty: bool,
        vehicle_id: uuid.UUID | None = None,
    ) -> DutyState:
        driver = await self._driver_for_user(operator_id, user_id)
        return (
            await self._go_on_duty(operator_id, driver, vehicle_id)
            if on_duty
            else await self._go_off_duty(operator_id, driver)
        )

    async def current(self, operator_id: uuid.UUID, user_id: uuid.UUID) -> DutyState:
        driver = await self._driver_for_user(operator_id, user_id)
        session = await self._open_session(driver.id)
        return DutyState(
            on_duty=session is not None,
            vehicle_id=session.vehicle_id if session else None,
            # Credentials are never re-issued on a read: the password is gone.
            mqtt=None,
        )

    # --- on duty ------------------------------------------------------------

    async def _go_on_duty(
        self, operator_id: uuid.UUID, driver: Driver, vehicle_id: uuid.UUID | None
    ) -> DutyState:
        if not driver.active:
            raise Forbidden("This driver is not active")

        existing = await self._open_session(driver.id)
        if existing is not None:
            raise Conflict("Already on duty", {"vehicle_id": str(existing.vehicle_id)})

        target_id = vehicle_id or driver.default_vehicle_id
        if target_id is None:
            raise ValidationFailed("No vehicle given and this driver has no default vehicle")

        vehicle = await self._vehicle_or_404(operator_id, target_id)

        in_use = await self._open_session_for_vehicle(vehicle.id)
        if in_use is not None:
            raise Conflict("That vehicle is already on duty with another driver")

        # out_of_service -> available is a legal edge, but it belongs to a supervisor:
        # "take vehicle out of service" is theirs, and a driver must not undo it by
        # tapping "go on duty" (roles-and-permissions.md). The state machine allows the
        # edge because supervisors need it; the actor check belongs here.
        if VehicleStatus(vehicle.status) is VehicleStatus.out_of_service:
            raise Conflict(
                "That vehicle is out of service. A supervisor has to return it to "
                "service before it can go on duty.",
                {"vehicle_id": str(vehicle.id)},
            )

        transition_vehicle(
            VehicleStatus(vehicle.status), VehicleStatus.available, actor=Actor.driver
        )
        vehicle.status = VehicleStatus.available
        vehicle.current_driver_id = driver.id

        password = generate_password()
        username = username_for(str(vehicle.id))
        vehicle.mqtt_username = username

        self.session.add(
            DutySession(
                operator_id=operator_id,
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                started_at=self.clock.now(),
                mqtt_password_hash=hash_password(password),
            )
        )
        await self.session.flush()

        logger.info(
            "driver_on_duty",
            driver_id=str(driver.id),
            vehicle_id=str(vehicle.id),
        )
        return DutyState(
            on_duty=True,
            vehicle_id=vehicle.id,
            mqtt=MqttCredentials(
                host=self.settings.mqtt_host,
                port=self.settings.mqtt_port,
                username=username,
                password=password,
                topic_prefix=topic_prefix(str(operator_id), str(vehicle.id)),
            ),
        )

    # --- off duty -----------------------------------------------------------

    async def _go_off_duty(self, operator_id: uuid.UUID, driver: Driver) -> DutyState:
        session = await self._open_session(driver.id)
        if session is None:
            return DutyState(on_duty=False, vehicle_id=None, mqtt=None)

        vehicle = await self._vehicle_or_404(operator_id, session.vehicle_id)

        # DRV-02: "going off duty is blocked while a trip is in progress". The state
        # machine has no on_trip -> off_duty edge, so this is the machine's rule, not a
        # second opinion about it.
        if VehicleStatus(vehicle.status) is VehicleStatus.on_trip:
            raise Conflict(
                "Finish or hand over the current trip before going off duty",
                {"vehicle_id": str(vehicle.id)},
            )

        if VehicleStatus(vehicle.status) is VehicleStatus.available:
            transition_vehicle(VehicleStatus.available, VehicleStatus.off_duty, actor=Actor.driver)
            vehicle.status = VehicleStatus.off_duty

        vehicle.current_driver_id = None
        # The credential dies with the session, so a handed-over phone cannot publish.
        vehicle.mqtt_username = None
        session.ended_at = self.clock.now()
        await self.session.flush()

        logger.info("driver_off_duty", driver_id=str(driver.id), vehicle_id=str(vehicle.id))
        return DutyState(on_duty=False, vehicle_id=None, mqtt=None)

    # --- broker files -------------------------------------------------------

    async def broker_files(self, operator_id: uuid.UUID | None = None) -> tuple[str, str]:
        """Render the password and ACL files for every currently on-duty vehicle.

        Returns the text rather than writing it: where the files live and how the broker
        is told to reload them is deployment configuration, not application logic.
        """
        query = (
            select(DutySession, Vehicle)
            .join(Vehicle, Vehicle.id == DutySession.vehicle_id)
            .where(DutySession.ended_at.is_(None))
        )
        if operator_id is not None:
            query = query.where(DutySession.operator_id == operator_id)

        credentials = [
            VehicleCredential(
                vehicle_id=str(vehicle.id),
                operator_id=str(vehicle.operator_id),
                username=vehicle.mqtt_username or username_for(str(vehicle.id)),
                password_hash=duty.mqtt_password_hash or "",
            )
            for duty, vehicle in (await self.session.execute(query)).all()
        ]
        return build_password_file(credentials), build_acl_file(credentials)

    # --- helpers ------------------------------------------------------------

    async def _driver_for_user(self, operator_id: uuid.UUID, user_id: uuid.UUID) -> Driver:
        driver = (
            (
                await self.session.execute(
                    select(Driver)
                    .where(Driver.operator_id == operator_id)
                    .where(Driver.user_id == user_id)
                )
            )
            .scalars()
            .first()
        )
        if driver is None:
            raise Forbidden("This account is not linked to a driver record")
        return driver

    async def _vehicle_or_404(self, operator_id: uuid.UUID, vehicle_id: uuid.UUID) -> Vehicle:
        vehicle = (
            (
                await self.session.execute(
                    select(Vehicle)
                    .where(Vehicle.operator_id == operator_id)
                    .where(Vehicle.id == vehicle_id)
                )
            )
            .scalars()
            .one_or_none()
        )
        if vehicle is None:
            raise NotFound("Vehicle not found", {"id": str(vehicle_id)})
        return vehicle

    async def _open_session(self, driver_id: uuid.UUID) -> DutySession | None:
        result = await self.session.execute(
            select(DutySession)
            .where(DutySession.driver_id == driver_id)
            .where(DutySession.ended_at.is_(None))
        )
        return result.scalars().one_or_none()

    async def _open_session_for_vehicle(self, vehicle_id: uuid.UUID) -> DutySession | None:
        result = await self.session.execute(
            select(DutySession)
            .where(DutySession.vehicle_id == vehicle_id)
            .where(DutySession.ended_at.is_(None))
        )
        return result.scalars().one_or_none()
