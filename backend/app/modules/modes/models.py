"""The `mode_setting` table (`control-model.md` §2, `data-model.md`).

One row is one scoping rule. **Every scoping column is nullable, and `NULL` means
"any"** - which is why there is no unique constraint across them: two rules scoped the
same way are legal, §2 resolves them by update time, and the admin screen warns. A
constraint here would refuse the overlap the spec explicitly tolerates.
"""

from __future__ import annotations

import uuid
from datetime import time

from sqlalchemy import ARRAY, CheckConstraint, Enum, ForeignKey, SmallInteger, Time
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import TenantEntity, tenant_index
from app.domain.enums import Direction
from app.domain.modes import Mode


class ModeSetting(TenantEntity):
    """Which mode applies to requests matching this scope."""

    __tablename__ = "mode_setting"
    __table_args__ = (
        tenant_index("mode_setting", "client_id"),
        tenant_index("mode_setting", "zone_id"),
        # A window needs both ends or neither. A half-written one is the kind of rule
        # that behaves plausibly and wrongly - `domain/modes.py` treats it as no window
        # at all, and this stops it being stored in the first place.
        CheckConstraint(
            "(start_time IS NULL) = (end_time IS NULL)",
            name="ck_mode_setting_window_complete",
        ),
    )

    mode: Mapped[str] = mapped_column(
        Enum(Mode, native_enum=False, length=20), nullable=False, default=Mode.manual
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client.id", ondelete="CASCADE")
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("zone.id", ondelete="CASCADE")
    )
    direction: Mapped[str | None] = mapped_column(Enum(Direction, native_enum=False, length=20))
    #: ISO weekdays, Monday = 1 ... Sunday = 7. `NULL` or empty means every day.
    #: An array rather than a bitmask: `{1,2,3,4,5}` is readable in `psql`, and the
    #: admin screen renders it without decoding anything.
    weekdays: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    #: Why this rule exists, in the operator's words. Rules outlive the person who
    #: wrote them, and "semi-auto for Acme evenings" with no reason is a rule nobody
    #: dares delete.
    note: Mapped[str | None] = mapped_column()
