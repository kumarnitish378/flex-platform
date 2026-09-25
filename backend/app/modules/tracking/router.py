"""`/driver/location` — the HTTPS fallback for GPS (B12).

`mqtt-topics.md`: "If MQTT is unreachable for 60 s, the app sends pings via
POST /driver/location (batch, every 15 s) until MQTT reconnects."

The same `GpsIngestor` handles these as handles MQTT, so the validation rules cannot drift
between the two paths — a driver on a bad connection must not get different treatment
from one on a good one.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.dependencies import ClockDep, CurrentUserDep, SessionDep
from app.domain.errors import Forbidden
from app.domain.gps import MAX_BATCH
from app.modules.auth.dependencies import require
from app.modules.auth.permissions import Permission
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver
from app.modules.tracking.service import GpsIngestor

router = APIRouter(tags=["driver"])


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LocationPingIn(Strict):
    ts: datetime
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    speed_mps: float | None = None
    heading_deg: float | None = None
    accuracy_m: float | None = None
    battery_pct: int | None = None


@router.post(
    "/driver/location",
    status_code=status.HTTP_202_ACCEPTED,
    summary="HTTPS fallback for GPS when MQTT is unavailable (batch)",
    dependencies=[Depends(require(Permission.duty_manage))],
)
async def upload_locations(
    pings: Annotated[list[LocationPingIn], Body(max_length=MAX_BATCH)],
    session: SessionDep,
    clock: ClockDep,
    current_user: CurrentUserDep,
) -> Response:
    """Accept a batch for the caller's own on-duty vehicle.

    The vehicle comes from the open duty session, never from the request body: a driver
    must not be able to post positions for a cab they are not driving.
    """
    operator_id = current_user.claims.operator_id
    if operator_id is None:
        raise Forbidden("This role has no operator scope")

    vehicle_id = await _on_duty_vehicle(session, operator_id, current_user.claims.user_id)

    ingestor = GpsIngestor(session, clock)
    payload: dict[str, Any] = {
        "batch": [
            {
                "v": 1,
                "ts": ping.ts.isoformat(),
                "lat": ping.lat,
                "lng": ping.lng,
                "spd": ping.speed_mps,
                "hdg": ping.heading_deg,
                "acc": ping.accuracy_m,
                "bat": ping.battery_pct,
                "src": "app",
            }
            for ping in pings
        ]
    }
    await ingestor.ingest(vehicle_id, operator_id, payload)
    # Always persist: the next call may be 15 seconds away, and an HTTPS fallback is
    # already a sign the connection is unreliable.
    await ingestor.flush()
    return Response(status_code=status.HTTP_202_ACCEPTED)


async def _on_duty_vehicle(session: Any, operator_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID:
    driver = (
        (
            await session.execute(
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

    vehicle_id: uuid.UUID | None = (
        (
            await session.execute(
                select(DutySession.vehicle_id)
                .where(DutySession.driver_id == driver.id)
                .where(DutySession.ended_at.is_(None))
            )
        )
        .scalars()
        .one_or_none()
    )
    if vehicle_id is None:
        # non-functional.md: driver GPS is collected only while on duty.
        raise Forbidden("Go on duty before sending locations")
    return vehicle_id
