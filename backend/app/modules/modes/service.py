"""Reading and writing mode settings, and resolving one request's mode (B24).

The precedence itself is pure and lives in `domain/modes.py`. This is the part that
needs a database: loading an operator's rules, turning a `RideRequest` into the facts
the resolver matches on, and the CRUD the admin screen drives.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.enums import Direction
from app.domain.errors import NotFound, ValidationFailed
from app.domain.modes import (
    Mode,
    ModeScope,
    RequestScope,
    Resolution,
    overlaps,
    resolve_mode,
)
from app.domain.timeofday import local as local_time
from app.modules.modes.models import ModeSetting
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import Operator

logger = get_logger(__name__)

#: ISO weekdays. Monday = 1 ... Sunday = 7, matching `datetime.isoweekday()`.
MIN_WEEKDAY = 1
MAX_WEEKDAY = 7


@dataclass(frozen=True, slots=True)
class ModeSettingInput:
    """What an admin can set. Every scoping field is optional; `None` means "any"."""

    mode: Mode
    client_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    direction: Direction | None = None
    weekdays: list[int] | None = None
    start_time: time | None = None
    end_time: time | None = None
    note: str | None = None


class ModeService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    # --- resolution ---------------------------------------------------------

    async def resolve_for_request(self, request: RideRequest) -> Resolution:
        """Which mode governs this request, and why (`control-model.md` §2).

        The `at` passed to the resolver is the **requested** time, not now: a rule for
        "evenings" must govern a ride booked at lunchtime for 19:00, or an operator who
        scoped semi-auto to the evening peak would find their morning bookings
        governed by it and their evening ones not.
        """
        employee = await self.session.get(Employee, request.employee_id)
        if employee is None:
            raise NotFound("Employee not found")

        operator = await self.session.get(Operator, request.operator_id)
        paused = bool(operator.automation_paused) if operator is not None else False
        timezone = operator.timezone if operator is not None else "UTC"

        return resolve_mode(
            await self.scopes(request.operator_id),
            RequestScope(
                client_id=request.client_id,
                direction=Direction(request.direction),
                zone_id=employee.zone_id,
                is_vip=bool(employee.is_vip),
            ),
            # Converted to the operator's wall clock, because a window written
            # "18:00-21:00" means their evening and not UTC's. Comparing the stored
            # instant directly made an Indian operator's evening rule govern 23:30 to
            # 02:30 local - found in B28, where the same mistake in the night-safety
            # window would have been five and a half hours of silent exposure.
            local_time(request.requested_time, timezone),
            automation_paused=paused,
            operator_default=await self.operator_default(request.operator_id),
        )

    async def operator_default(self, operator_id: uuid.UUID) -> Mode:
        """`control-model.md` §2 level 8: required, initial value `manual`.

        Stored as the catch-all setting - the row that scopes nothing. An operator with
        no settings at all is on `manual`, which is Phase 1's behaviour and the right
        thing to inherit: a deployment that upgrades must not silently start assigning.
        """
        del operator_id
        return Mode.manual

    async def scopes(self, operator_id: uuid.UUID) -> list[ModeScope]:
        """Every setting for this operator, as pure data the resolver understands."""
        rows = (
            (
                await self.session.execute(
                    select(ModeSetting).where(ModeSetting.operator_id == operator_id)
                )
            )
            .scalars()
            .all()
        )
        return [_scope_of(row) for row in rows]

    # --- CRUD ---------------------------------------------------------------

    async def list_settings(self, operator_id: uuid.UUID) -> list[ModeSetting]:
        return list(
            (
                await self.session.execute(
                    select(ModeSetting)
                    .where(ModeSetting.operator_id == operator_id)
                    .order_by(ModeSetting.created_at)
                )
            )
            .scalars()
            .all()
        )

    async def create(self, operator_id: uuid.UUID, data: ModeSettingInput) -> ModeSetting:
        _validate(data)
        setting = ModeSetting(
            id=uuid.uuid4(),
            operator_id=operator_id,
            mode=str(data.mode),
            client_id=data.client_id,
            zone_id=data.zone_id,
            direction=str(data.direction) if data.direction else None,
            weekdays=sorted(set(data.weekdays)) if data.weekdays else None,
            start_time=data.start_time,
            end_time=data.end_time,
            note=data.note,
        )
        self.session.add(setting)
        await self.session.flush()
        logger.info(
            "mode_setting_created",
            setting_id=str(setting.id),
            mode=str(data.mode),
            client_id=str(data.client_id) if data.client_id else None,
        )
        return setting

    async def update(
        self, operator_id: uuid.UUID, setting_id: uuid.UUID, data: ModeSettingInput
    ) -> ModeSetting:
        _validate(data)
        setting = await self._setting(operator_id, setting_id)
        setting.mode = str(data.mode)
        setting.client_id = data.client_id
        setting.zone_id = data.zone_id
        setting.direction = str(data.direction) if data.direction else None
        setting.weekdays = sorted(set(data.weekdays)) if data.weekdays else None
        setting.start_time = data.start_time
        setting.end_time = data.end_time
        setting.note = data.note
        # `updated_at` moves, and §2 breaks ties on it - so editing a rule promotes it
        # above an equally specific sibling. That is the documented behaviour, and the
        # overlap warning is what tells an admin it happened.
        setting.updated_at = self.clock.now()
        await self.session.flush()
        return setting

    async def delete(self, operator_id: uuid.UUID, setting_id: uuid.UUID) -> None:
        setting = await self._setting(operator_id, setting_id)
        await self.session.delete(setting)
        await self.session.flush()

    async def overlapping(self, operator_id: uuid.UUID) -> list[tuple[uuid.UUID, uuid.UUID]]:
        """Pairs that could both match one request, at the same specificity.

        Reported rather than refused: §2 resolves them deterministically, and an
        overlap is often deliberate while a rule is being migrated. The admin screen
        warns (B24's acceptance criterion).
        """
        return overlaps(await self.scopes(operator_id))

    async def _setting(self, operator_id: uuid.UUID, setting_id: uuid.UUID) -> ModeSetting:
        setting = (
            (
                await self.session.execute(
                    select(ModeSetting)
                    .where(ModeSetting.operator_id == operator_id)
                    .where(ModeSetting.id == setting_id)
                )
            )
            .scalars()
            .first()
        )
        if setting is None:
            raise NotFound("Mode setting not found")
        return setting


def _validate(data: ModeSettingInput) -> None:
    """Refuse the shapes `domain/modes.py` would have to guess at."""
    if (data.start_time is None) != (data.end_time is None):
        raise ValidationFailed(
            "A time window needs both a start and an end, or neither",
            # Rendered here too, not only by the handler: a detail that reads
            # "18:00:00" is useful to a client, and `str(datetime.time(18, 0))` is
            # what the handler would fall back to anyway.
            {
                "start_time": data.start_time.isoformat() if data.start_time else None,
                "end_time": data.end_time.isoformat() if data.end_time else None,
            },
        )
    for day in data.weekdays or []:
        if not MIN_WEEKDAY <= day <= MAX_WEEKDAY:
            raise ValidationFailed(
                f"weekdays are {MIN_WEEKDAY}-{MAX_WEEKDAY} (Monday to Sunday), got {day}",
                {"weekdays": data.weekdays},
            )


def _scope_of(row: ModeSetting) -> ModeScope:
    return ModeScope(
        id=row.id,
        mode=Mode(row.mode),
        updated_at=row.updated_at,
        client_id=row.client_id,
        zone_id=row.zone_id,
        direction=Direction(row.direction) if row.direction else None,
        weekdays=frozenset(row.weekdays) if row.weekdays else None,
        start_time=row.start_time,
        end_time=row.end_time,
    )
