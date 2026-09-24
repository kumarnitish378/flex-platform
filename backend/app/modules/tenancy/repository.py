"""Tenancy repositories."""

from __future__ import annotations

import uuid

from app.core.repository import Repository, TenantRepository
from app.modules.tenancy.models import Client, ClientPolicy, Office, Operator, Zone


class OperatorRepository(Repository[Operator]):
    """Operators are the tenant boundary, so this one is not tenant-scoped itself."""

    model = Operator


class ClientRepository(TenantRepository[Client]):
    model = Client


class OfficeRepository(TenantRepository[Office]):
    model = Office

    async def list_for_client(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> list[Office]:
        result = await self.session.execute(
            self.scoped(operator_id).where(Office.client_id == client_id)
        )
        return list(result.scalars().all())


class ClientPolicyRepository(TenantRepository[ClientPolicy]):
    model = ClientPolicy

    async def for_client(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> ClientPolicy | None:
        result = await self.session.execute(
            self.scoped(operator_id).where(ClientPolicy.client_id == client_id)
        )
        return result.scalars().one_or_none()


class ZoneRepository(TenantRepository[Zone]):
    model = Zone

    async def active(self, operator_id: uuid.UUID) -> list[Zone]:
        result = await self.session.execute(
            self.scoped(operator_id).where(Zone.active.is_(True)).order_by(Zone.name)
        )
        return list(result.scalars().all())
