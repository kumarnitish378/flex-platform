"""Employee repositories."""

from __future__ import annotations

import uuid

from app.core.repository import TenantRepository
from app.modules.people.models import Employee, SavedPlace


class EmployeeRepository(TenantRepository[Employee]):
    model = Employee

    async def by_phone(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, phone: str
    ) -> Employee | None:
        result = await self.session.execute(
            self.scoped(operator_id)
            .where(Employee.client_id == client_id)
            .where(Employee.phone == phone)
        )
        return result.scalars().one_or_none()

    async def active_for_client(
        self, operator_id: uuid.UUID, client_id: uuid.UUID
    ) -> list[Employee]:
        result = await self.session.execute(
            self.scoped(operator_id)
            .where(Employee.client_id == client_id)
            .where(Employee.active.is_(True))
            .order_by(Employee.name)
        )
        return list(result.scalars().all())


class SavedPlaceRepository(TenantRepository[SavedPlace]):
    model = SavedPlace
