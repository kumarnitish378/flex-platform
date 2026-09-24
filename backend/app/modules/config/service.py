"""Reading and changing operator configuration (B05).

Every business number in the platform is read through `get`, so a caller never needs a
literal (CLAUDE.md hard rule 4). Unset keys fall back to the documented default rather
than being seeded on operator creation — that way changing a default in
`allocation-rules.md` reaches existing operators too, instead of only new ones.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain import config_keys
from app.domain.config_keys import CONFIG_KEYS
from app.domain.errors import ValidationFailed
from app.modules.config.models import OperatorConfig, OperatorConfigHistory

logger = get_logger(__name__)


class ConfigService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    async def all_values(self, operator_id: uuid.UUID) -> dict[str, Any]:
        """Defaults overlaid with whatever this operator has set."""
        values = config_keys.defaults()
        values.update(await self._stored(operator_id))
        return values

    async def get(self, operator_id: uuid.UUID, key: str) -> Any:
        """One value, falling back to its default."""
        if key not in CONFIG_KEYS:
            raise ValidationFailed(f"Unknown config key: {key}", {"key": key})
        stored = await self._stored(operator_id)
        return stored.get(key, config_keys.defaults()[key])

    async def _stored(self, operator_id: uuid.UUID) -> dict[str, Any]:
        result = await self.session.execute(
            select(OperatorConfig).where(OperatorConfig.operator_id == operator_id)
        )
        return {row.key: row.value for row in result.scalars().all()}

    async def update(
        self,
        operator_id: uuid.UUID,
        changes: dict[str, Any],
        changed_by: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Validate and apply a patch atomically, writing history for each change.

        Validation happens for the whole patch before anything is written, so an invalid
        third key cannot leave the first two applied.
        """
        if not changes:
            raise ValidationFailed("No config values supplied")

        validated = config_keys.validate_all(changes)

        existing = {
            row.key: row
            for row in (
                await self.session.execute(
                    select(OperatorConfig)
                    .where(OperatorConfig.operator_id == operator_id)
                    .where(OperatorConfig.key.in_(validated))
                )
            ).scalars()
        }

        for key, new_value in validated.items():
            row = existing.get(key)
            old_value = row.value if row else None

            if row is not None and row.value == new_value:
                continue  # no change, no history row

            if row is None:
                row = OperatorConfig(
                    operator_id=operator_id, key=key, value=new_value, updated_by=changed_by
                )
                self.session.add(row)
                version = 1
            else:
                row.value = new_value
                row.updated_by = changed_by
                row.version += 1
                version = row.version

            self.session.add(
                OperatorConfigHistory(
                    operator_id=operator_id,
                    key=key,
                    old_value=old_value,
                    new_value=new_value,
                    version=version,
                    changed_by=changed_by,
                )
            )
            logger.info(
                "config_changed",
                operator_id=str(operator_id),
                key=key,
                old=old_value,
                new=new_value,
                version=version,
            )

        await self.session.flush()
        return await self.all_values(operator_id)

    async def history(
        self, operator_id: uuid.UUID, key: str | None = None, limit: int = 50
    ) -> list[OperatorConfigHistory]:
        query = (
            select(OperatorConfigHistory)
            .where(OperatorConfigHistory.operator_id == operator_id)
            .order_by(OperatorConfigHistory.created_at.desc())
            .limit(limit)
        )
        if key is not None:
            query = query.where(OperatorConfigHistory.key == key)
        result = await self.session.execute(query)
        return list(result.scalars().all())
