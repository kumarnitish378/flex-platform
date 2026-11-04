"""Admin use cases for the fleet and the customer records (B06).

Everything here takes `operator_id` from the caller's token and passes it to a
`TenantRepository`, so a request can only ever touch its own operator's rows.

Cross-references (a vehicle's default driver, an office's client) are checked **within
the tenant** before being stored. Without that, an admin could point their office at
another operator's client by guessing a UUID — the foreign key would happily allow it.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.enums import CLIENT_SCOPED_ROLES, Role
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.modules.auth.models import AppUser, UserRole
from app.modules.fleet.models import Driver, Vehicle
from app.modules.tenancy.models import Client, Office

logger = get_logger(__name__)


class AdminService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    # --- clients ------------------------------------------------------------

    async def list_clients(self, operator_id: uuid.UUID) -> list[Client]:
        result = await self.session.execute(
            select(Client).where(Client.operator_id == operator_id).order_by(Client.name)
        )
        return list(result.scalars().all())

    async def create_client(self, operator_id: uuid.UUID, data: dict[str, Any]) -> Client:
        await self._reject_duplicate(
            Client, operator_id, Client.name == data["name"], "A client with that name exists"
        )
        client = Client(operator_id=operator_id, **data)
        self.session.add(client)
        await self.session.flush()
        logger.info("client_created", operator_id=str(operator_id), client_id=str(client.id))
        return client

    # --- offices ------------------------------------------------------------

    async def list_offices(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> list[Office]:
        await self._client_or_404(operator_id, client_id)
        result = await self.session.execute(
            select(Office)
            .where(Office.operator_id == operator_id)
            .where(Office.client_id == client_id)
            .order_by(Office.name)
        )
        return list(result.scalars().all())

    async def create_office(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, data: dict[str, Any]
    ) -> Office:
        await self._client_or_404(operator_id, client_id)
        office = Office(operator_id=operator_id, client_id=client_id, **data)
        self.session.add(office)
        await self.session.flush()
        return office

    # --- vehicles -----------------------------------------------------------

    async def list_vehicles(
        self, operator_id: uuid.UUID, status: str | None = None
    ) -> list[Vehicle]:
        query = select(Vehicle).where(Vehicle.operator_id == operator_id)
        if status is not None:
            query = query.where(Vehicle.status == status)
        result = await self.session.execute(query.order_by(Vehicle.registration_no))
        return list(result.scalars().all())

    async def create_vehicle(self, operator_id: uuid.UUID, data: dict[str, Any]) -> Vehicle:
        await self._reject_duplicate(
            Vehicle,
            operator_id,
            Vehicle.registration_no == data["registration_no"],
            "A vehicle with that registration exists",
        )
        vehicle = Vehicle(operator_id=operator_id, **data)
        self.session.add(vehicle)
        await self.session.flush()
        logger.info("vehicle_created", operator_id=str(operator_id), vehicle_id=str(vehicle.id))
        return vehicle

    async def update_vehicle(
        self, operator_id: uuid.UUID, vehicle_id: uuid.UUID, changes: dict[str, Any]
    ) -> Vehicle:
        vehicle: Vehicle = await self._one_or_404(Vehicle, operator_id, vehicle_id, "Vehicle")

        if "registration_no" in changes and changes["registration_no"] != vehicle.registration_no:
            await self._reject_duplicate(
                Vehicle,
                operator_id,
                Vehicle.registration_no == changes["registration_no"],
                "A vehicle with that registration exists",
            )
        if changes.get("current_driver_id") is not None:
            await self._one_or_404(Driver, operator_id, changes["current_driver_id"], "Driver")

        for field, value in changes.items():
            setattr(vehicle, field, value)
        await self.session.flush()
        return vehicle

    # --- drivers ------------------------------------------------------------

    async def list_drivers(self, operator_id: uuid.UUID) -> list[Driver]:
        result = await self.session.execute(
            select(Driver).where(Driver.operator_id == operator_id).order_by(Driver.name)
        )
        return list(result.scalars().all())

    async def create_driver(self, operator_id: uuid.UUID, data: dict[str, Any]) -> Driver:
        await self._reject_duplicate(
            Driver, operator_id, Driver.phone == data["phone"], "A driver with that phone exists"
        )
        if data.get("default_vehicle_id") is not None:
            await self._one_or_404(Vehicle, operator_id, data["default_vehicle_id"], "Vehicle")

        driver = Driver(operator_id=operator_id, **data)
        self.session.add(driver)
        await self.session.flush()
        logger.info("driver_created", operator_id=str(operator_id), driver_id=str(driver.id))
        return driver

    async def update_driver(
        self, operator_id: uuid.UUID, driver_id: uuid.UUID, changes: dict[str, Any]
    ) -> Driver:
        driver: Driver = await self._one_or_404(Driver, operator_id, driver_id, "Driver")

        if "phone" in changes and changes["phone"] != driver.phone:
            await self._reject_duplicate(
                Driver,
                operator_id,
                Driver.phone == changes["phone"],
                "A driver with that phone exists",
            )
        if changes.get("default_vehicle_id") is not None:
            await self._one_or_404(Vehicle, operator_id, changes["default_vehicle_id"], "Vehicle")

        for field, value in changes.items():
            setattr(driver, field, value)
        await self.session.flush()
        return driver

    # --- users --------------------------------------------------------------

    async def invite_user(
        self,
        operator_id: uuid.UUID,
        phone: str,
        name: str,
        role: Role,
        client_id: uuid.UUID | None = None,
    ) -> AppUser:
        """Grant a role to a phone number, creating the user if they are new.

        There is no invitation token: login is phone + OTP, so "inviting" someone is
        exactly "giving that number a role". They log in whenever they like.
        """
        if role in CLIENT_SCOPED_ROLES and client_id is None:
            raise ValidationFailed(f"{role} requires a client_id", {"role": str(role)})
        if role not in CLIENT_SCOPED_ROLES and client_id is not None:
            raise ValidationFailed(f"{role} must not have a client_id", {"role": str(role)})
        if client_id is not None:
            await self._client_or_404(operator_id, client_id)

        user = (
            (await self.session.execute(select(AppUser).where(AppUser.phone == phone)))
            .scalars()
            .one_or_none()
        )

        if user is None:
            user = AppUser(phone=phone, name=name)
            self.session.add(user)
            await self.session.flush()

        existing = (
            (
                await self.session.execute(
                    select(UserRole)
                    .where(UserRole.user_id == user.id)
                    .where(UserRole.role == role)
                    .where(UserRole.operator_id == operator_id)
                    .where(UserRole.client_id == client_id)
                )
            )
            .scalars()
            .one_or_none()
        )

        if existing is not None:
            raise Conflict(
                "That user already holds this role", {"role": str(role), "phone_known": True}
            )

        self.session.add(
            UserRole(user_id=user.id, role=role, operator_id=operator_id, client_id=client_id)
        )
        await self.session.flush()
        logger.info(
            "user_invited", operator_id=str(operator_id), user_id=str(user.id), role=str(role)
        )
        return user

    # --- helpers ------------------------------------------------------------

    async def _client_or_404(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> Client:
        found: Client = await self._one_or_404(Client, operator_id, client_id, "Client")
        return found

    async def _one_or_404(
        self, model: Any, operator_id: uuid.UUID, entity_id: uuid.UUID, label: str
    ) -> Any:
        """Fetch within the tenant. A foreign id reads as "not found", never as found."""
        result = await self.session.execute(
            select(model).where(model.operator_id == operator_id).where(model.id == entity_id)
        )
        entity = result.scalars().one_or_none()
        if entity is None:
            raise NotFound(f"{label} not found", {"id": str(entity_id)})
        return entity

    async def _reject_duplicate(
        self, model: Any, operator_id: uuid.UUID, condition: Any, message: str
    ) -> None:
        existing = await self.session.execute(
            select(model).where(model.operator_id == operator_id).where(condition)
        )
        if existing.scalars().first() is not None:
            raise Conflict(message)
