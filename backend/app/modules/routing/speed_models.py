"""`road_speed_profile`: speeds learned from our own trips (B37, OQ-22).

Keyed `(osm_way_id, slot)` as `data-model.md` specifies. Phase 3 writes only the
whole-service-area aggregate, under `osm_way_id = 0` (see `domain/speed_profile.py` for why
per-way profiles need map matching that `approx` does not have); the key already has room
for them.

`distance_m` and `seconds` are the running totals the speed is derived from. They are in
the table, rather than only the derived `speed_kph`, so a later run can fold new trips in
exactly instead of averaging an average.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, SmallInteger, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RoadSpeedProfile(Base):
    __tablename__ = "road_speed_profile"

    osm_way_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    #: Hour of the week, local time: Monday 00:00-00:59 is 0, Sunday 23:00-23:59 is 167.
    slot: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    #: Effective speed in `approx` frame: great-circle metres x road factor over seconds.
    speed_kph: Mapped[float] = mapped_column(Float, nullable=False)
    #: Legs that went into it.
    samples: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SpeedProfileState(Base):
    """One row: how far through the completed trips the learner has read."""

    __tablename__ = "speed_profile_state"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    processed_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
