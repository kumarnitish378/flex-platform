"""Repository base classes.

`coding-standards.md` §2 rule 3: repository methods take `operator_id` explicitly and a
base helper adds the filter. The point is that forgetting the filter must be hard, not
merely discouraged — `TenantRepository` has no way to build a query without it.

Repositories do data access only. Use-case logic, transactions and events belong in the
service layer (rule 1).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, delete, func, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Entity, TenantEntity
from app.domain.errors import NotFound


class Repository[ModelT: Entity]:
    """Data access for a table with no tenant column (operators, users, OTP)."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def get_or_raise(self, entity_id: uuid.UUID) -> ModelT:
        entity = await self.get(entity_id)
        if entity is None:
            raise NotFound(f"{self.model.__name__} not found", {"id": str(entity_id)})
        return entity

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def list_all(self, limit: int = 50, offset: int = 0) -> Sequence[ModelT]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return result.scalars().all()


class TenantRepository[TenantModelT: TenantEntity]:
    """Data access for a tenant table. Every read and write is scoped to one operator.

    There is no unscoped query method on purpose. A caller that wants "all operators"
    has to write that query itself, in the open, rather than by forgetting an argument.
    """

    model: type[TenantModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def scoped(self, operator_id: uuid.UUID) -> Select[tuple[TenantModelT]]:
        """A SELECT already filtered to one operator. Build every query from this."""
        return select(self.model).where(self.model.operator_id == operator_id)

    async def get(self, operator_id: uuid.UUID, entity_id: uuid.UUID) -> TenantModelT | None:
        """Fetch by id **within** an operator.

        Deliberately not `session.get`: that would find the row regardless of tenant and
        leave the check to the caller. A wrong id and a foreign id return the same
        `None`, so a probe cannot distinguish "does not exist" from "not yours".
        """
        result = await self.session.execute(
            self.scoped(operator_id).where(self.model.id == entity_id)
        )
        return result.scalars().one_or_none()

    async def get_or_raise(self, operator_id: uuid.UUID, entity_id: uuid.UUID) -> TenantModelT:
        entity = await self.get(operator_id, entity_id)
        if entity is None:
            raise NotFound(f"{self.model.__name__} not found", {"id": str(entity_id)})
        return entity

    async def add(self, entity: TenantModelT) -> TenantModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def list(
        self,
        operator_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        **filters: Any,
    ) -> Sequence[TenantModelT]:
        query = self.scoped(operator_id)
        for column, value in filters.items():
            query = query.where(getattr(self.model, column) == value)
        result = await self.session.execute(query.limit(limit).offset(offset))
        return result.scalars().all()

    async def count(self, operator_id: uuid.UUID, **filters: Any) -> int:
        query = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.operator_id == operator_id)
        )
        for column, value in filters.items():
            query = query.where(getattr(self.model, column) == value)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def delete(self, operator_id: uuid.UUID, entity_id: uuid.UUID) -> bool:
        """Delete within an operator. Returns False if the row is absent or foreign."""
        result: CursorResult[Any] = await self.session.execute(  # type: ignore[assignment]
            delete(self.model)
            .where(self.model.operator_id == operator_id)
            .where(self.model.id == entity_id)
        )
        return bool(result.rowcount)
