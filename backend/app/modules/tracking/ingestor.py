"""The MQTT GPS ingestor process (B12, ADR-0005).

A separate process, not a thread inside the API: GPS is a firehose with a completely
different failure mode from HTTP, and `architecture.md` section 3.2 puts it on its own so
a slow request cannot delay a ping and a restart of one does not take out the other.

Run it with `make ingestor`.

Topic and payload rules live in `mqtt-topics.md`; validation lives in `app/domain/gps.py`.
This module is only plumbing: subscribe, resolve the vehicle from the topic, hand the
payload to the ingestor, flush on a timer.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import signal
import uuid
from typing import Any

from app.core.clock import SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.logging import configure_logging, get_logger
from app.core.redis import create_redis
from app.core.settings import Settings, get_settings
from app.modules.tracking.service import FLUSH_INTERVAL_SECONDS, GpsIngestor

logger = get_logger(__name__)

#: mqtt-topics.md: the ingestor subscribes across every operator and vehicle.
GPS_TOPIC = "sc/v1/op/+/veh/+/gps"
STATUS_TOPIC = "sc/v1/op/+/veh/+/status"


def parse_topic(topic: str) -> tuple[uuid.UUID, uuid.UUID] | None:
    """`sc/v1/op/{operator}/veh/{vehicle}/gps` -> (operator_id, vehicle_id)."""
    parts = topic.split("/")
    if len(parts) != 7 or parts[0] != "sc" or parts[2] != "op" or parts[4] != "veh":
        return None
    try:
        return uuid.UUID(parts[3]), uuid.UUID(parts[5])
    except ValueError:
        return None


async def run(settings: Settings | None = None) -> None:
    """Consume until interrupted."""
    import aiomqtt

    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    redis = create_redis(settings)
    clock = SystemClock()

    stopping = asyncio.Event()
    _install_signal_handlers(stopping)

    logger.info("ingestor_starting", host=settings.mqtt_host, port=settings.mqtt_port)
    try:
        async with (
            aiomqtt.Client(
                hostname=settings.mqtt_host,
                port=settings.mqtt_port,
                username=settings.mqtt_ingestor_user or None,
                password=settings.mqtt_ingestor_password or None,
                identifier="smartcab-ingestor",
            ) as client,
            session_factory() as session,
        ):
            ingestor = GpsIngestor(session, clock, redis)
            await client.subscribe(GPS_TOPIC, qos=0)
            logger.info("ingestor_subscribed", topic=GPS_TOPIC)

            flusher = asyncio.create_task(_flush_loop(ingestor, session, stopping))
            try:
                async for message in client.messages:
                    if stopping.is_set():
                        break
                    await _handle(ingestor, message)
            finally:
                stopping.set()
                flusher.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await flusher
                # Never lose what is already buffered.
                await ingestor.flush()
                await session.commit()
    finally:
        await redis.aclose()
        await engine.dispose()
        logger.info("ingestor_stopped")


async def _handle(ingestor: GpsIngestor, message: Any) -> None:
    parsed = parse_topic(str(message.topic))
    if parsed is None:
        logger.warning("ingestor_bad_topic", topic=str(message.topic))
        return
    operator_id, vehicle_id = parsed

    try:
        payload = json.loads(message.payload)
    except (TypeError, ValueError):
        logger.warning("ingestor_bad_payload", vehicle_id=str(vehicle_id))
        return

    # One bad vehicle must never stop the stream for the other 199.
    try:
        await ingestor.ingest(vehicle_id, operator_id, payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "ingestor_handler_failed", vehicle_id=str(vehicle_id), error=type(exc).__name__
        )


async def _flush_loop(ingestor: GpsIngestor, session: Any, stopping: asyncio.Event) -> None:
    """Flush on a timer so a quiet vehicle's last ping is not held indefinitely."""
    while not stopping.is_set():
        await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
        try:
            if await ingestor.flush():
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("ingestor_flush_failed", error=type(exc).__name__)


def _install_signal_handlers(stopping: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):  # Windows lacks add_signal_handler
            loop.add_signal_handler(sig, stopping.set)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
