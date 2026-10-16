"""Zones, and the one thing they are for: knowing which zone a rider lives in (B27).

`employee.zone_id` has been a column since B07 and null in every row since. Three things
in Phase 2 need it to be real: zone-scoped mode settings (`control-model.md` §2), zone
pooling (`allocation-rules.md` §3), and the override preview's "zones left with no
available vehicle" (§3 rule 2).

**Derivation is not an import-time decision.** A zone drawn today has to know who lives
in it today, not from the next CSV upload onwards - so every write to a zone re-derives
the employees it could affect, and `employee.zone_id` is never set by a caller.

Two judgement calls the docs do not make, both made here and tested:

* **A home exactly on a boundary is inside.** PostGIS `ST_Contains` says no for a point
  on the edge, which would drop riders into a crack between two adjacent zones that
  share one. `ST_Covers` says yes, and a rider on the line being in one of the two
  zones is right in every reading.
* **Overlapping zones resolve to the smallest.** Zones may overlap - an operator
  drawing "Noida" and "Sector 62" inside it is doing something reasonable - and the
  more specific answer is the useful one. Ties break on name, so the answer never
  depends on insertion order.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.geo import to_polygon
from app.core.logging import get_logger
from app.domain.errors import Conflict, NotFound
from app.modules.modes.models import ModeSetting
from app.modules.people.models import Employee
from app.modules.tenancy.models import Zone

logger = get_logger(__name__)

#: One statement for the whole operator rather than a query per employee. The subquery
#: is the zone each home falls in, smallest first; `ST_Covers` rather than
#: `ST_Contains` so a home on a boundary belongs to the zone rather than to nothing.
_DERIVE_ALL = text(
    """
    UPDATE employee AS e
    SET zone_id = (
        SELECT z.id
        FROM zone AS z
        WHERE z.operator_id = e.operator_id
          AND z.active
          AND ST_Covers(z.area::geometry, e.home_location::geometry)
        ORDER BY ST_Area(z.area::geography), z.name
        LIMIT 1
    )
    WHERE e.operator_id = :operator_id
      AND e.zone_id IS DISTINCT FROM (
        SELECT z.id
        FROM zone AS z
        WHERE z.operator_id = e.operator_id
          AND z.active
          AND ST_Covers(z.area::geometry, e.home_location::geometry)
        ORDER BY ST_Area(z.area::geography), z.name
        LIMIT 1
      )
    """
)

#: The same question for one home, before the employee row exists.
_ZONE_OF_POINT = text(
    """
    SELECT z.id
    FROM zone AS z
    WHERE z.operator_id = :operator_id
      AND z.active
      AND ST_Covers(z.area::geometry, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
    ORDER BY ST_Area(z.area::geography), z.name
    LIMIT 1
    """
)


class ZoneService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    # --- derivation -------------------------------------------------------------

    async def zone_of(self, operator_id: uuid.UUID, lat: float, lng: float) -> uuid.UUID | None:
        """Which zone this home falls in, or `None` if no active zone covers it.

        `None` is an ordinary answer, not a failure: an operator with no zones drawn
        has every employee outside them, and Phase 1 ran that way throughout.
        """
        found: uuid.UUID | None = await self.session.scalar(
            _ZONE_OF_POINT.bindparams(operator_id=operator_id, lat=lat, lng=lng)
        )
        return found

    async def rederive(self, operator_id: uuid.UUID) -> int:
        """Recompute `zone_id` for every employee of one operator. Returns rows changed.

        Called after any zone write, and by the backfill. Cheap enough to run whole:
        the alternative is working out which employees a redrawn polygon could have
        affected, which means comparing the old and new shapes - and getting that
        wrong leaves a rider silently in the wrong zone, where nothing ever notices.
        """
        result = await self.session.execute(_DERIVE_ALL.bindparams(operator_id=operator_id))
        # `rowcount` is on the DBAPI cursor result; the typed `Result` facade does not
        # declare it, and a `CursorResult` cast here is narrower than silencing it.
        changed = int(cast("CursorResult[Any]", result).rowcount or 0)
        await self.session.flush()
        if changed:
            logger.info("employee_zones_rederived", operator_id=str(operator_id), changed=changed)
        return changed

    # --- CRUD ---------------------------------------------------------------------

    async def list_zones(
        self, operator_id: uuid.UUID, *, include_inactive: bool = False
    ) -> list[tuple[Zone, int]]:
        """Every zone with how many employees it covers."""
        query = (
            select(Zone, func.count(Employee.id))
            .outerjoin(Employee, Employee.zone_id == Zone.id)
            .where(Zone.operator_id == operator_id)
            .group_by(Zone.id)
            .order_by(Zone.name)
        )
        if not include_inactive:
            query = query.where(Zone.active)
        rows = await self.session.execute(query)
        return [(row[0], row[1]) for row in rows]

    async def create(
        self,
        operator_id: uuid.UUID,
        name: str,
        boundary: Sequence[tuple[float, float]],
        *,
        active: bool = True,
    ) -> tuple[Zone, int]:
        if await self._by_name(operator_id, name) is not None:
            raise Conflict("A zone with that name already exists", {"name": name})

        zone = Zone(
            id=uuid.uuid4(),
            operator_id=operator_id,
            name=name,
            area=to_polygon(boundary),
            active=active,
        )
        self.session.add(zone)
        await self.session.flush()
        await self.rederive(operator_id)
        return zone, await self._employee_count(zone.id)

    async def update(
        self,
        operator_id: uuid.UUID,
        zone_id: uuid.UUID,
        *,
        name: str | None = None,
        boundary: Sequence[tuple[float, float]] | None = None,
        active: bool | None = None,
    ) -> tuple[Zone, int]:
        zone = await self._or_404(operator_id, zone_id)

        if name is not None and name != zone.name:
            if await self._by_name(operator_id, name) is not None:
                raise Conflict("A zone with that name already exists", {"name": name})
            zone.name = name
        if boundary is not None:
            zone.area = to_polygon(boundary)
        if active is not None:
            zone.active = active

        await self.session.flush()
        await self.rederive(operator_id)
        return zone, await self._employee_count(zone.id)

    async def delete(self, operator_id: uuid.UUID, zone_id: uuid.UUID) -> None:
        zone = await self._or_404(operator_id, zone_id)

        scoped = await self.session.scalar(
            select(func.count(ModeSetting.id)).where(ModeSetting.zone_id == zone_id)
        )
        if scoped:
            # Deleting would widen that rule from one zone to every zone, which is the
            # opposite of what it says. `mode_setting.zone_id` is ON DELETE SET NULL,
            # so the database would allow it silently.
            raise Conflict(
                "A mode setting is scoped to this zone",
                {"zone_id": str(zone_id), "mode_settings": int(scoped)},
            )

        await self.session.delete(zone)
        await self.session.flush()
        await self.rederive(operator_id)

    # --- loading --------------------------------------------------------------------

    async def _or_404(self, operator_id: uuid.UUID, zone_id: uuid.UUID) -> Zone:
        zone = await self.session.scalar(
            select(Zone).where(Zone.id == zone_id).where(Zone.operator_id == operator_id)
        )
        if zone is None:
            raise NotFound("Zone not found", {"id": str(zone_id)})
        return zone

    async def _by_name(self, operator_id: uuid.UUID, name: str) -> Zone | None:
        found: Zone | None = await self.session.scalar(
            select(Zone).where(Zone.operator_id == operator_id).where(Zone.name == name)
        )
        return found

    async def _employee_count(self, zone_id: uuid.UUID) -> int:
        count = await self.session.scalar(
            select(func.count(Employee.id)).where(Employee.zone_id == zone_id)
        )
        return int(count or 0)
