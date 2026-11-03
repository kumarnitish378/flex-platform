"""Load test against the RUNNING stack: a pilot-sized peak, made only of the calls the apps make.

    python scripts/loadtest.py                      # 35 cabs, 300 riders over a 120-minute peak
    python scripts/loadtest.py --minutes 20         # the same 300 riders in 20 minutes (6x denser)
    python scripts/loadtest.py --cabs 5 --riders 20 --minutes 3      # a quick shake-down
    make loadtest                                   # = the first line, after `make loadtest-seed`

Needs the stack up (`make phone-dev`), the load-test data (`make loadtest-seed`) and the
`websockets` package (part of `uvicorn[standard]`). It plays, in real time:

* **35 driver phones** - go on duty (staggered), publish GPS over MQTT by the phone's rule (a ping
  per 5 m moved, at most one a second, and a heartbeat every 60 s when still), poll their trips,
  start, drive to each stop, arrive, finish, complete;
* **300 riders** - request a ride at a time drawn from a peak-shaped curve over the window, hold a
  WebSocket on their own channel, then on their trip's channel once a cab is assigned, and poll the
  request every 15 s as a backgrounded app would;
* **2 supervisors** - read the queue and the map every 5 s, hold the live-vehicle WebSocket, and
  assign the nearest free cab to each waiting request after a human-sized pause.

It measures, from the clients' side: API latency per endpoint (p50 / p95 / p99), how late each GPS
ping reached the supervisor's WebSocket (**fan-out delay**), how late the ingestor accepted it
(**ingestor lag**, read back from `location_ping`: `received_at - recorded_at`), how long a rider
waited to be told about their cab (**assignment notification**), and every error. The server's own
latency histogram is scraped from `/metrics` before and after for comparison. Targets are from
`docs/01-requirements/non-functional.md`.

Exit code 0 only when every target is met and nothing failed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import random
import re
import sys
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Self

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app import loadtest_seed as world

EARTH = 6_371_000.0
OFFICE = (world.OFFICE[1], world.OFFICE[2])
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# Targets: docs/01-requirements/non-functional.md
API_P95_TARGET_S = 0.300
LOCATION_VISIBLE_TARGET_S = 10.0
ASSIGNMENT_NOTIFY_TARGET_S = 10.0

TERMINAL = {"dropped", "cancelled", "expired", "no_show"}


def metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    dlat = math.radians(b[0] - a[0])
    dlng = math.radians(b[1] - a[1])
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(a[0]))
        * math.cos(math.radians(b[0]))
        * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH * math.asin(math.sqrt(h))


def toward(
    here: tuple[float, float], target: tuple[float, float], step_m: float
) -> tuple[float, float]:
    distance = metres(here, target)
    if distance <= step_m:
        return target
    f = step_m / distance
    return (here[0] + (target[0] - here[0]) * f, here[1] + (target[1] - here[1]) * f)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def parse_ts(text: str) -> float:
    return datetime.fromisoformat(text).timestamp()


# --- measurements --------------------------------------------------------------------------


@dataclass
class Stats:
    latency: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    statuses: Counter[tuple[str, str]] = field(default_factory=Counter)
    errors: Counter[str] = field(default_factory=Counter)
    error_samples: dict[str, str] = field(default_factory=dict)
    fanout_supervisor: list[float] = field(default_factory=list)
    fanout_rider: list[float] = field(default_factory=list)
    notify: list[float] = field(default_factory=list)
    assign_wait: list[float] = field(default_factory=list)
    counters: Counter[str] = field(default_factory=Counter)

    def error(self, kind: str, detail: str = "") -> None:
        self.errors[kind] += 1
        self.error_samples.setdefault(kind, detail[:300])


def label(method: str, path: str) -> str:
    return f"{method} {UUID_RE.sub('{id}', path.split('?')[0])}"


# --- one logged-in person ------------------------------------------------------------------


class Actor:
    def __init__(
        self, name: str, phone: str, http: httpx.AsyncClient, stats: Stats
    ) -> None:
        self.name, self.phone, self.http, self.stats = name, phone, http, stats
        self.access = ""
        self.refresh_token = ""
        self.user_id = ""
        self.operator_id = ""

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access}"}

    async def login(self) -> None:
        status, body = await self.call(
            "POST", "/auth/test-login", json={"phone": self.phone}, auth=False
        )
        if status != 200 or not isinstance(body, dict):
            raise RuntimeError(f"login {self.phone} -> {status}")
        self.access, self.refresh_token = body["access_token"], body["refresh_token"]
        _, me = await self.call("GET", "/auth/me")
        if isinstance(me, dict):
            self.user_id = me.get("id") or me.get("user_id") or ""
            roles = me.get("roles") or []
            self.operator_id = next(
                (r["operator_id"] for r in roles if r.get("operator_id")), ""
            )

    async def refresh(self) -> bool:
        status, body = await self.call(
            "POST",
            "/auth/refresh",
            json={"refresh_token": self.refresh_token},
            auth=False,
        )
        if status == 200 and isinstance(body, dict):
            self.access, self.refresh_token = (
                body["access_token"],
                body["refresh_token"],
            )
            return True
        return False

    async def call(
        self,
        method: str,
        path: str,
        expect: tuple[int, ...] = (200, 201, 204),
        auth: bool = True,
        retry_on_401: bool = True,
        **kw: Any,
    ) -> tuple[int, Any]:
        """One request, timed. Unexpected statuses and transport failures are counted, not raised."""
        name = label(method, path)
        started = time.perf_counter()
        try:
            response = await self.http.request(
                method, path, headers=self.headers() if auth else None, **kw
            )
        except httpx.HTTPError as exc:
            # A kept-alive connection the server has already closed (uvicorn drops idle ones after
            # 5 s) fails on first use. Every HTTP client retries that once for a read; counted, not
            # an error. A write is never retried: it may have been applied.
            if (
                method == "GET"
                and isinstance(exc, httpx.ReadError | httpx.RemoteProtocolError)
                and retry_on_401
            ):
                self.stats.counters["get_retried_after_reset"] += 1
                return await self.call(method, path, expect, auth, False, **kw)
            self.stats.statuses[(name, type(exc).__name__)] += 1
            self.stats.error("transport", f"{name}: {type(exc).__name__} {exc}")
            return 0, None
        elapsed = time.perf_counter() - started
        self.stats.latency[name].append(elapsed)
        self.stats.statuses[(name, str(response.status_code))] += 1
        if (
            response.status_code == 401
            and auth
            and retry_on_401
            and await self.refresh()
        ):
            return await self.call(method, path, expect, auth, False, **kw)
        body: Any = None
        if response.content and "json" in response.headers.get("content-type", ""):
            body = response.json()
        if response.status_code not in expect:
            self.stats.error(
                f"http_{response.status_code}", f"{name}: {response.text[:200]}"
            )
        return response.status_code, body


def event_body(position: tuple[float, float]) -> dict[str, Any]:
    return {
        "client_event_id": str(uuid.uuid4()),
        "occurred_at": datetime.now(UTC).isoformat(),
        "lat": position[0],
        "lng": position[1],
    }


# --- WebSocket ----------------------------------------------------------------------------------


async def ws_session(
    api: str,
    actor: Actor,
    channels: list[str],
    on_event: Any,
    stats: Stats,
    stop: asyncio.Event,
    extra: asyncio.Queue[list[str]] | None = None,
) -> None:
    """Hold `/ws` for an actor, reconnect on failure, hand every event frame to `on_event`."""
    from websockets.asyncio.client import connect

    url = api.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    wanted = list(channels)
    while not stop.is_set():
        helpers: list[asyncio.Task[None]] = []
        try:
            async with connect(
                url, additional_headers=actor.headers(), open_timeout=15, max_size=2**20
            ) as ws:
                await ws.send(json.dumps({"type": "subscribe", "channels": wanted}))
                stats.counters["ws_connects"] += 1

                async def subscribe_more(ws: Any = ws) -> None:
                    assert extra is not None
                    while True:
                        more = await extra.get()
                        wanted.extend(more)
                        await ws.send(
                            json.dumps({"type": "subscribe", "channels": more})
                        )

                async def close_when_stopped(ws: Any = ws) -> None:
                    await stop.wait()
                    await ws.close()

                helpers.append(asyncio.create_task(close_when_stopped()))
                if extra is not None:
                    helpers.append(asyncio.create_task(subscribe_more()))

                # `async for`, never `wait_for(ws.recv(), t)`: cancelling a recv() in
                # websockets 17 on Python 3.14 silently discards the frame it was reading.
                async for raw in ws:
                    received = time.time()
                    frame = json.loads(raw)
                    if frame.get("type") == "event":
                        await on_event(frame, received)
                    elif frame.get("type") == "subscribed" and frame.get("refused"):
                        stats.error("ws_refused", f"{actor.name}: {frame['refused']}")
                    elif frame.get("type") == "error":
                        stats.error("ws_error", str(frame))
            if stop.is_set():
                return
        except Exception as exc:  # noqa: BLE001 - a dropped socket is a measurement, not a crash
            if stop.is_set():
                return
            stats.counters["ws_drops"] += 1
            stats.error("ws_dropped", f"{actor.name}: {type(exc).__name__} {exc}")
            await actor.refresh()
            await asyncio.sleep(2)
        finally:
            for task in helpers:
                task.cancel()
            await asyncio.gather(*helpers, return_exceptions=True)


# --- the people -----------------------------------------------------------------------------------


@dataclass
class Shared:
    api: str
    http: httpx.AsyncClient
    stats: Stats
    stop: asyncio.Event
    started: float
    speed_mps: float
    #: request id -> monotonic-clock-free wall time the supervisor's assign call returned
    assigned_at: dict[str, float] = field(default_factory=dict)
    created_at: dict[str, float] = field(default_factory=dict)
    published: Counter[str] = field(default_factory=Counter)
    riders_done: int = 0
    outcomes: Counter[str] = field(default_factory=Counter)


class PahoPublisher:
    """A phone's MQTT connection: paho on its own thread, reconnecting by itself.

    Not aiomqtt: that needs `add_reader`, which only Windows' selector loop has, and the selector
    loop cannot watch more than 512 sockets.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        client_id: str,
        tls: bool = False,
    ) -> None:
        import paho.mqtt.client as paho

        self._client = paho.Client(
            paho.CallbackAPIVersion.VERSION2, client_id=client_id
        )
        self._client.username_pw_set(username, password)
        if tls:
            self._client.tls_set()
        self._client.reconnect_delay_set(min_delay=1, max_delay=10)
        self._address = (host, port)

    async def __aenter__(self) -> Self:
        await asyncio.to_thread(self._client.connect, *self._address, 30)
        self._client.loop_start()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    async def publish(self, topic: str, payload: str, qos: int = 0) -> None:
        info = self._client.publish(topic, payload, qos=qos)
        if info.rc != 0:
            raise RuntimeError(f"publish refused: rc={info.rc}")


async def driver_agent(number: int, shared: Shared, delay: float) -> None:
    stats = shared.stats
    await asyncio.sleep(delay)
    me = Actor(f"driver{number}", world.driver_phone(number), shared.http, stats)
    await me.login()
    rng = random.Random(number)
    # Cabs wait at the office, where every trip of the peak ends: starting a second run within
    # the ingestor's memory of the first must not look like a 2 km teleport (impossible_jump).
    here = (
        OFFICE[0] + rng.uniform(-0.0005, 0.0005),
        OFFICE[1] + rng.uniform(-0.0005, 0.0005),
    )
    status, duty = await me.call("POST", "/driver/duty", json={"on_duty": True})
    if status != 200 or not duty or not duty.get("mqtt"):
        stats.error("driver_no_duty", f"driver {number}: {status} {duty}")
        return
    mqtt, gps = duty["mqtt"], duty.get("gps") or {}
    filter_m = float(gps.get("distance_filter_m", 5))
    heartbeat = float(gps.get("heartbeat_seconds", 60))
    topic = f"{mqtt['topic_prefix']}/gps"
    stats.counters["drivers_on_duty"] += 1

    trip_id: str | None = None
    route: list[dict[str, Any]] = []
    last_poll = 0.0
    last_pub_pos, last_pub_at = (0.0, 0.0), 0.0

    async def drive(client: Any, target: tuple[float, float]) -> None:
        nonlocal here, last_pub_pos, last_pub_at
        while here != target and not shared.stop.is_set():
            tick = time.monotonic()
            here = toward(here, target, shared.speed_mps)
            await publish(client)
            await asyncio.sleep(max(0.0, 1.0 - (time.monotonic() - tick)))

    async def publish(client: Any) -> None:
        nonlocal last_pub_pos, last_pub_at
        now = time.monotonic()
        moved = metres(last_pub_pos, here) if last_pub_at else 1e9
        if moved < filter_m and now - last_pub_at < heartbeat:
            return
        payload = {
            "v": 1,
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "lat": here[0],
            "lng": here[1],
            "spd": shared.speed_mps if moved >= filter_m else 0.0,
            "acc": 5.0,
            "src": "app",
        }
        try:
            await client.publish(topic, json.dumps(payload), qos=0)
        except Exception as exc:  # noqa: BLE001
            stats.error("mqtt_publish", f"driver {number}: {type(exc).__name__} {exc}")
            return
        last_pub_pos, last_pub_at = here, now
        shared.published[str(duty["vehicle_id"])] += 1
        stats.counters["gps_published"] += 1

    try:
        async with PahoPublisher(
            mqtt["host"],
            int(mqtt["port"]),
            mqtt["username"],
            mqtt["password"],
            f"lt-{number}-{uuid.uuid4().hex[:6]}",
            bool(mqtt.get("tls")),
        ) as client:
            await publish(client)
            while not shared.stop.is_set():
                await publish(client)
                if trip_id is None and time.monotonic() - last_poll >= 8:
                    last_poll = time.monotonic()
                    # A freshly assigned trip is `planned`: only scope=upcoming lists it.
                    st, body = await me.call("GET", "/driver/trips?scope=upcoming")
                    mine = [t for t in (body or {}).get("items", []) if st == 200]
                    if mine:
                        trip = mine[0]
                        trip_id = trip["id"]
                        if trip["status"] in ("planned", "dispatched"):
                            await me.call(
                                "POST",
                                f"/driver/trips/{trip_id}/start",
                                json=event_body(here),
                            )
                        route = sorted(trip["stops"], key=lambda s: s["sequence"])
                if trip_id is not None:
                    for stop in route:
                        if stop.get("status") in ("done", "skipped"):
                            continue
                        target = (stop["location"]["lat"], stop["location"]["lng"])
                        await drive(client, target)
                        await me.call(
                            "POST",
                            f"/driver/stops/{stop['id']}/arrived",
                            json=event_body(here),
                        )
                        await asyncio.sleep(5)
                        await me.call(
                            "POST",
                            f"/driver/stops/{stop['id']}/done",
                            json=event_body(here),
                        )
                    await me.call(
                        "POST",
                        f"/driver/trips/{trip_id}/complete",
                        json=event_body(here),
                    )
                    stats.counters["trips_completed"] += 1
                    trip_id, route = None, []
                await asyncio.sleep(0.5)
    except Exception as exc:  # noqa: BLE001
        stats.error("driver_mqtt", f"driver {number}: {type(exc).__name__} {exc}")
    finally:
        if trip_id is not None:
            await me.call(
                "POST",
                f"/driver/trips/{trip_id}/complete",
                expect=(200, 204, 409),
                json=event_body(here),
            )
        await me.call(
            "POST", "/driver/duty", expect=(200, 409), json={"on_duty": False}
        )


async def rider_agent(number: int, shared: Shared, at: float) -> None:
    stats = shared.stats
    await asyncio.sleep(max(0.0, shared.started + at - time.monotonic()))
    if shared.stop.is_set():
        return
    me = Actor(f"rider{number}", world.rider_phone(number), shared.http, stats)
    await me.login()
    home = world.rider_home(number)
    when = (datetime.now(UTC) + timedelta(minutes=20)).isoformat()
    created = time.time()
    status, body = await me.call(
        "POST",
        "/ride-requests",
        json={
            "direction": "to_office",
            "requested_time": when,
            "location": {"lat": home[0], "lng": home[1]},
            "landmark": f"load test {number}",
        },
    )
    if status != 201 or not body:
        shared.outcomes["request_failed"] += 1
        shared.riders_done += 1
        return
    request_id = body["id"]
    shared.created_at[request_id] = created
    shared.outcomes["requested"] += 1

    channels = [f"user.{me.user_id}"] if me.user_id else []
    extra: asyncio.Queue[list[str]] = asyncio.Queue()
    watching: set[str] = set()
    ws_stop = asyncio.Event()

    async def on_event(frame: dict[str, Any], received: float) -> None:
        name, data = frame.get("event"), frame.get("data") or {}
        if name == "vehicle.location" and data.get("ts"):
            stats.fanout_rider.append(received - parse_ts(data["ts"]))
        elif name == "request.assigned" and data.get("request_id") == request_id:
            sent = shared.assigned_at.get(request_id)
            if sent is not None:
                stats.notify.append(received - sent)
            # The event must never arrive ahead of the data it announces.
            st, now = await me.call("GET", f"/ride-requests/{request_id}")
            if st == 200 and now and now.get("status") in ("requested", "queued"):
                stats.counters["event_before_data"] += 1
            trip = data.get("trip_id")
            if trip and trip not in watching:
                watching.add(trip)
                await extra.put([f"trip.{trip}"])

    ws_task = (
        asyncio.create_task(
            ws_session(shared.api, me, channels, on_event, stats, ws_stop, extra)
        )
        if channels
        else None
    )
    final = "unfinished"
    try:
        while not shared.stop.is_set():
            await asyncio.sleep(15)
            st, now = await me.call("GET", f"/ride-requests/{request_id}")
            if st != 200 or not now:
                continue
            if now["status"] in TERMINAL:
                final = now["status"]
                break
            trip = now.get("trip_id")
            if trip and trip not in watching:
                watching.add(trip)
                await extra.put([f"trip.{trip}"])
    finally:
        ws_stop.set()
        if ws_task is not None:
            await asyncio.gather(ws_task, return_exceptions=True)
        shared.outcomes[final] += 1
        shared.riders_done += 1


async def supervisor_agent(number: int, shared: Shared, total: int) -> None:
    stats = shared.stats
    me = Actor(f"sup{number}", world.SUPERVISORS[number - 1], shared.http, stats)
    await me.login()
    channels = [
        f"operator.{me.operator_id}.vehicles",
        f"operator.{me.operator_id}.requests",
    ]
    stats.counters["supervisors"] += 1

    async def on_event(frame: dict[str, Any], received: float) -> None:
        if frame.get("event") == "vehicle.location":
            ts = (frame.get("data") or {}).get("ts")
            if ts:
                stats.fanout_supervisor.append(received - parse_ts(ts))
        stats.counters[f"sup_events_{frame.get('event')}"] += 1

    ws_task = asyncio.create_task(
        ws_session(shared.api, me, channels, on_event, stats, shared.stop)
    )
    seen: dict[str, float] = {}
    claimed: dict[str, float] = {}
    handled: set[str] = set()
    rng = random.Random(number)
    last_board = 0.0
    try:
        while not shared.stop.is_set():
            cycle = time.monotonic()
            st, queue = await me.call(
                "GET",
                "/dispatch/requests?status=requested&status=queued&status=suggested",
            )
            st2, fleet = await me.call("GET", "/dispatch/vehicles")
            if cycle - last_board >= 30:
                last_board = cycle
                await me.call("GET", "/dispatch/trips")
                await me.call("GET", "/alerts?status=open")
            if st == 200 and st2 == 200 and queue and fleet:
                free = [
                    v
                    for v in fleet["items"]
                    if v["status"] == "available"
                    and v.get("position")
                    and not v.get("stale")
                    and v.get("active_trip_id") is None
                    and claimed.get(v["id"], 0) < cycle
                ]
                waiting = sorted(queue["items"], key=lambda r: r["waiting_since"])
                for request in waiting:
                    rid = request["id"]
                    # Two supervisors split the queue by request, as two desks would.
                    if int(uuid.UUID(rid).int % 2) != number % 2 or rid in handled:
                        continue
                    first_seen = seen.setdefault(rid, cycle)
                    if cycle - first_seen < rng.uniform(3, 15):
                        continue
                    if not free:
                        break
                    spot = (request["location"]["lat"], request["location"]["lng"])
                    pick = min(
                        free,
                        key=lambda v: metres(
                            (v["position"]["lat"], v["position"]["lng"]), spot
                        ),
                    )
                    free.remove(pick)
                    started = time.time()
                    # Stamped before the call: the rider's event can land before the call returns,
                    # and the time the supervisor waited for the assign is part of the delay.
                    shared.assigned_at[rid] = started
                    code, _ = await me.call(
                        "POST",
                        "/dispatch/assign",
                        expect=(200, 201, 409, 422),
                        json={"request_id": rid, "vehicle_id": pick["id"]},
                    )
                    if code in (200, 201):
                        handled.add(rid)
                        claimed[pick["id"]] = cycle + 20
                        stats.assign_wait.append(
                            started - shared.created_at.get(rid, started)
                        )
                        stats.counters["assigned"] += 1
                    else:
                        stats.counters["assign_refused"] += 1
            await asyncio.sleep(max(0.0, 5.0 - (time.monotonic() - cycle)))
    finally:
        await asyncio.gather(ws_task, return_exceptions=True)


# --- server side ---------------------------------------------------------------------------------


def parse_histogram(text: str) -> tuple[dict[float, float], Counter[str]]:
    """Total HTTP duration buckets (all routes but the probes) and the 5xx count."""
    buckets: dict[float, float] = defaultdict(float)
    codes: Counter[str] = Counter()
    for line in text.splitlines():
        if line.startswith("smartcab_http_request_duration_seconds_bucket"):
            if 'route="/metrics"' in line or "/health" in line:
                continue
            le = re.search(r'le="([^"]+)"', line)
            if le:
                bound = float("inf") if le.group(1) == "+Inf" else float(le.group(1))
                buckets[bound] += float(line.rsplit(" ", 1)[1])
        elif line.startswith("smartcab_http_requests_total"):
            status = re.search(r'status="(\d+)"', line)
            if status and 'route="/metrics"' not in line:
                codes[status.group(1)[0] + "xx"] += float(line.rsplit(" ", 1)[1])
    return dict(buckets), codes


def bucket_quantile(
    before: dict[float, float], after: dict[float, float], q: float
) -> float:
    delta = sorted((le, after.get(le, 0) - before.get(le, 0)) for le in after)
    total = delta[-1][1] if delta else 0
    if total <= 0:
        return float("nan")
    for le, cumulative in delta:
        if cumulative >= q * total:
            return le
    return float("inf")


async def ingest_lag(start: datetime, operator_id: uuid.UUID) -> dict[str, float]:
    """`received_at - recorded_at` for this run's pings, straight from the table."""
    from app.core.db import create_engine
    from app.core.settings import Settings
    from sqlalchemy import text

    engine = create_engine(Settings())
    try:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "SELECT count(*), "
                        "percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM received_at - recorded_at)), "
                        "percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM received_at - recorded_at)), "
                        "percentile_cont(0.99) WITHIN GROUP (ORDER BY extract(epoch FROM received_at - recorded_at)), "
                        "max(extract(epoch FROM received_at - recorded_at)) "
                        "FROM location_ping WHERE operator_id = :op AND recorded_at >= :since"
                    ),
                    {"op": operator_id, "since": start},
                )
            ).one()
    finally:
        await engine.dispose()
    return {
        "rows": float(row[0]),
        "p50": float(row[1] or 0),
        "p95": float(row[2] or 0),
        "p99": float(row[3] or 0),
        "max": float(row[4] or 0),
    }


async def clean_slate(http: httpx.AsyncClient, cabs: int, riders: int) -> str:
    """A run that was interrupted leaves cabs on duty, trips open and riders waiting. Tidy up.

    Uses the same API the apps do, with its own throwaway `Stats`, so none of it is measured.
    """
    scratch = Stats()
    cancelled = trips = off_duty = 0

    async def tidy_rider(number: int) -> int:
        rider = Actor("clean-rider", world.rider_phone(number), http, scratch)
        await rider.login()
        _, mine = await rider.call("GET", "/ride-requests/mine?active=true")
        done = 0
        for item in (mine or {}).get("items", []):
            code, _ = await rider.call(
                "POST",
                f"/ride-requests/{item['id']}/cancel",
                expect=(200, 204, 409),
                json={"reason": "load test cleanup"},
            )
            done += code in (200, 204)
        return done

    # Twenty at a time: the whole pilot-sized roster in a few seconds, not a thundering herd.
    for first in range(1, min(riders, world.RIDERS) + 1, 20):
        batch = range(first, min(first + 20, min(riders, world.RIDERS) + 1))
        cancelled += sum(await asyncio.gather(*(tidy_rider(n) for n in batch)))

    for number in range(1, min(cabs, world.CABS) + 1):
        driver = Actor("clean-driver", world.driver_phone(number), http, scratch)
        await driver.login()
        _, duty = await driver.call("GET", "/driver/duty")
        if not (duty or {}).get("on_duty"):
            continue
        _, mine = await driver.call("GET", "/driver/trips?scope=active")
        for trip in (mine or {}).get("items", []):
            await driver.call(
                "POST",
                f"/driver/trips/{trip['id']}/complete",
                expect=(200, 204, 409),
                json=event_body(OFFICE),
            )
            trips += 1
        await driver.call(
            "POST", "/driver/duty", expect=(200, 409), json={"on_duty": False}
        )
        off_duty += 1
    return f"{cancelled} stale request(s) cancelled, {trips} trip(s) closed, {off_duty} cab(s) taken off duty"


# --- the run -----------------------------------------------------------------------------------------


def fmt_ms(seconds: float) -> str:
    return "n/a" if math.isnan(seconds) else f"{seconds * 1000:.0f}"


def summary(values: list[float]) -> dict[str, float]:
    return {
        "n": float(len(values)),
        "p50": percentile(values, 0.5),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": max(values) if values else float("nan"),
    }


async def main_async(args: argparse.Namespace) -> int:
    api = args.api.rstrip("/")
    root = api.rsplit("/api/", 1)[0]
    stats = Stats()
    limits = httpx.Limits(max_connections=400, max_keepalive_connections=200)
    async with httpx.AsyncClient(base_url=api, timeout=30, limits=limits) as http:
        health = await http.get(f"{root}/health/live")
        if health.status_code != 200:
            print(
                f"FAIL  the API is not up: {root}/health/live -> {health.status_code}"
            )
            return 1

        probe = Actor("probe", world.SUPERVISORS[0], http, stats)
        try:
            await probe.login()
        except RuntimeError as exc:
            print(f"FAIL  {exc}\n      run `make loadtest-seed` first")
            return 1
        print("Clean slate:", await clean_slate(http, args.cabs, args.riders))
        stats.latency.clear()
        stats.statuses.clear()

        before_text = (await http.get(f"{root}/metrics")).text
        hist_before, codes_before = parse_histogram(before_text)

        stop = asyncio.Event()
        window = args.minutes * 60.0
        shared = Shared(
            api=api,
            http=http,
            stats=stats,
            stop=stop,
            started=time.monotonic(),
            speed_mps=args.speed_kph / 3.6,
        )
        wall_start = datetime.now(UTC)
        rng = random.Random(args.seed)
        arrivals = sorted(
            rng.triangular(0, window, window * 0.5) for _ in range(args.riders)
        )
        print(
            f"Load test: {args.cabs} cabs, {args.riders} riders over {args.minutes:g} min "
            f"(peak at {args.minutes / 2:g} min), {args.supervisors} supervisors, {args.speed_kph:g} km/h"
        )

        drivers = [
            asyncio.create_task(driver_agent(n, shared, delay=n * 60.0 / args.cabs / 2))
            for n in range(1, args.cabs + 1)
        ]
        supervisors = [
            asyncio.create_task(supervisor_agent(n, shared, args.riders))
            for n in range(1, args.supervisors + 1)
        ]
        await asyncio.sleep(
            60.0 / 2 + 5
        )  # let the fleet come on duty before the first request
        shared.started = time.monotonic()
        riders = [
            asyncio.create_task(rider_agent(n, shared, at))
            for n, at in enumerate(arrivals, start=1)
        ]

        deadline = shared.started + window + args.grace_minutes * 60.0
        last_report = 0.0
        announced: set[str] = set()
        while shared.riders_done < args.riders and time.monotonic() < deadline:
            await asyncio.sleep(5)
            if time.monotonic() - last_report >= 60:
                last_report = time.monotonic()
                for kind, sample in stats.error_samples.items():
                    if kind not in announced:
                        announced.add(kind)
                        print(f"  ! {kind}: {sample}", flush=True)
                elapsed = (time.monotonic() - shared.started) / 60
                print(
                    f"  t+{elapsed:5.1f} min  requested {shared.outcomes['requested']:3d}  "
                    f"done {shared.riders_done:3d}  assigned {stats.counters['assigned']:3d}  "
                    f"trips {stats.counters['trips_completed']:3d}  errors {sum(stats.errors.values())}",
                    flush=True,
                )
        timed_out = shared.riders_done < args.riders
        stop.set()
        await asyncio.gather(*riders, *drivers, *supervisors, return_exceptions=True)
        wall_end = datetime.now(UTC)

        after_text = (await http.get(f"{root}/metrics")).text
        hist_after, codes_after = parse_histogram(after_text)
        server_p50 = bucket_quantile(hist_before, hist_after, 0.5)
        server_p95 = bucket_quantile(hist_before, hist_after, 0.95)
        server_5xx = codes_after["5xx"] - codes_before["5xx"]
        server_total = sum(codes_after.values()) - sum(codes_before.values())

    await asyncio.sleep(6)  # the ingestor's last flush
    lag = await ingest_lag(wall_start, uuid.UUID(probe.operator_id))
    return report(
        args,
        stats,
        shared,
        lag,
        server_p50,
        server_p95,
        server_5xx,
        server_total,
        timed_out,
        wall_start,
        wall_end,
    )


def report(
    args: argparse.Namespace,
    stats: Stats,
    shared: Shared,
    lag: dict[str, float],
    server_p50: float,
    server_p95: float,
    server_5xx: float,
    server_total: float,
    timed_out: bool,
    wall_start: datetime,
    wall_end: datetime,
) -> int:
    published = int(stats.counters["gps_published"])
    persisted = int(lag["rows"])
    all_calls = [
        v
        for name, values in stats.latency.items()
        if name != "POST /auth/test-login"  # dev-only; the real login is an OTP
        for v in values
    ]
    overall = summary(all_calls)
    sup = summary(stats.fanout_supervisor)
    rid = summary(stats.fanout_rider)
    notify = summary(stats.notify)
    wait = summary(stats.assign_wait)
    results: list[tuple[str, bool, str]] = []

    print("\n=== API latency, as the apps saw it (ms) ===")
    print(f"{'endpoint':52}{'n':>8}{'p50':>7}{'p95':>7}{'p99':>7}{'max':>8}")
    for name, values in sorted(stats.latency.items(), key=lambda kv: -len(kv[1])):
        s = summary(values)
        print(
            f"{name:52}{int(s['n']):8d}{fmt_ms(s['p50']):>7}{fmt_ms(s['p95']):>7}{fmt_ms(s['p99']):>7}{fmt_ms(s['max']):>8}"
        )
    print(
        f"{'ALL':52}{int(overall['n']):8d}{fmt_ms(overall['p50']):>7}{fmt_ms(overall['p95']):>7}{fmt_ms(overall['p99']):>7}{fmt_ms(overall['max']):>8}"
    )
    print(
        f"server-side (histogram bucket upper bound): p50 <= {fmt_ms(server_p50)} ms, p95 <= {fmt_ms(server_p95)} ms, "
        f"{int(server_total)} requests, {int(server_5xx)} x 5xx"
    )

    print("\n=== GPS pipeline ===")
    print(
        f"pings published {published}, persisted {persisted} ({persisted / max(published, 1):.1%})"
    )
    print(
        f"ingestor lag  (ping time -> accepted):   p50 {lag['p50'] * 1000:.0f} ms  p95 {lag['p95'] * 1000:.0f} ms  p99 {lag['p99'] * 1000:.0f} ms  max {lag['max'] * 1000:.0f} ms"
    )
    print(
        f"fan-out delay (ping time -> supervisor WS): n {int(sup['n'])}  p50 {fmt_ms(sup['p50'])} ms  p95 {fmt_ms(sup['p95'])} ms  p99 {fmt_ms(sup['p99'])} ms  max {fmt_ms(sup['max'])} ms"
    )
    print(
        f"fan-out delay (ping time -> rider WS):      n {int(rid['n'])}  p50 {fmt_ms(rid['p50'])} ms  p95 {fmt_ms(rid['p95'])} ms  p99 {fmt_ms(rid['p99'])} ms  max {fmt_ms(rid['max'])} ms"
    )

    print("\n=== Dispatch ===")
    print(
        f"requests {shared.outcomes['requested']}  outcomes { {k: v for k, v in shared.outcomes.items() if k != 'requested'} }"
    )
    print(
        f"assigned {stats.counters['assigned']}  refused {stats.counters['assign_refused']}  trips completed {stats.counters['trips_completed']}"
    )
    print(
        f"request -> assign (rider wait for a cab): n {int(wait['n'])}  p50 {wait['p50']:.1f} s  p95 {wait['p95']:.1f} s  max {wait['max']:.1f} s"
    )
    print(
        f"assign -> rider told (WS):               n {int(notify['n'])}  p50 {fmt_ms(notify['p50'])} ms  p95 {fmt_ms(notify['p95'])} ms  max {fmt_ms(notify['max'])} ms"
    )
    print(
        f"events that arrived before their data: {stats.counters['event_before_data']}"
    )

    print("\n=== Errors ===")
    if stats.errors:
        for kind, count in stats.errors.most_common():
            print(f"{kind:20}{count:6}   e.g. {stats.error_samples.get(kind, '')}")
    else:
        print("none")
    print(
        f"WebSocket connects {stats.counters['ws_connects']}, drops {stats.counters['ws_drops']}"
    )

    api_p95 = overall["p95"]
    results.append(
        ("API p95 <= 300 ms", api_p95 <= API_P95_TARGET_S, f"{fmt_ms(api_p95)} ms")
    )
    results.append(
        (
            "server-side p95 <= 300 ms",
            server_p95 <= API_P95_TARGET_S,
            f"<= {fmt_ms(server_p95)} ms",
        )
    )
    results.append(
        (
            "supervisor map: ping visible <= 10 s (p95)",
            sup["p95"] <= LOCATION_VISIBLE_TARGET_S,
            f"{fmt_ms(sup['p95'])} ms",
        )
    )
    results.append(
        (
            "rider map: ping visible <= 10 s (p95)",
            math.isnan(rid["p95"]) or rid["p95"] <= LOCATION_VISIBLE_TARGET_S,
            f"{fmt_ms(rid['p95'])} ms",
        )
    )
    results.append(
        (
            "ingestor lag p95 <= 10 s",
            lag["p95"] <= LOCATION_VISIBLE_TARGET_S,
            f"{lag['p95'] * 1000:.0f} ms",
        )
    )
    results.append(
        (
            "assignment told <= 10 s (p95)",
            math.isnan(notify["p95"]) or notify["p95"] <= ASSIGNMENT_NOTIFY_TARGET_S,
            f"{fmt_ms(notify['p95'])} ms",
        )
    )
    results.append(
        (
            "no GPS pings lost",
            published > 0 and persisted >= published * 0.999,
            f"{persisted}/{published}",
        )
    )
    results.append(("no 5xx from the server", server_5xx == 0, f"{int(server_5xx)}"))
    results.append(
        ("no client-side errors", not stats.errors, f"{sum(stats.errors.values())}")
    )
    results.append(
        (
            "every rider finished",
            not timed_out
            and shared.outcomes["dropped"] == shared.outcomes["requested"],
            f"{shared.outcomes['dropped']}/{shared.outcomes['requested']} dropped",
        )
    )
    results.append(
        (
            "no event ahead of its data",
            stats.counters["event_before_data"] == 0,
            f"{stats.counters['event_before_data']}",
        )
    )

    print("\n=== Targets ===")
    for name, ok, value in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:46} {value}")

    if args.json:
        out = {
            "args": vars(args),
            "started": wall_start.isoformat(),
            "finished": wall_end.isoformat(),
            "api_latency_ms": {
                k: {a: (b * 1000 if a != "n" else b) for a, b in summary(v).items()}
                for k, v in stats.latency.items()
            },
            "overall_ms": {
                a: (b * 1000 if a != "n" else b) for a, b in overall.items()
            },
            "server_side_ms": {
                "p50_le": server_p50 * 1000,
                "p95_le": server_p95 * 1000,
                "requests": server_total,
                "5xx": server_5xx,
            },
            "gps": {
                "published": published,
                "persisted": persisted,
                "ingestor_lag_s": lag,
                "fanout_supervisor_s": sup,
                "fanout_rider_s": rid,
            },
            "dispatch": {
                "outcomes": dict(shared.outcomes),
                "assign_wait_s": wait,
                "notify_s": notify,
                "counters": dict(stats.counters),
            },
            "errors": dict(stats.errors),
            "error_samples": stats.error_samples,
            "targets": [{"name": n, "ok": ok, "value": v} for n, ok, v in results],
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(
            json.dumps(out, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nfull numbers: {args.json}")
    return 0 if all(ok for _, ok, _ in results) else 1


def keep_awake() -> None:
    """Windows: ask not to sleep while this process runs (a sleeping laptop wrecked the first long run).

    Nothing is changed in the system's settings; the request ends with the process.
    """
    if sys.platform != "win32":
        return
    import ctypes

    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)  # type: ignore[attr-defined]


def main(argv: list[str]) -> int:
    keep_awake()
    for noisy in ("httpx", "httpcore", "websockets", "aiomqtt"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--api", default="http://localhost:8000/api/v1")
    parser.add_argument("--cabs", type=int, default=world.CABS)
    parser.add_argument("--riders", type=int, default=world.RIDERS)
    parser.add_argument("--supervisors", type=int, default=2, choices=(1, 2))
    parser.add_argument(
        "--minutes", type=float, default=120.0, help="length of the arrival window"
    )
    parser.add_argument(
        "--grace-minutes", type=float, default=30.0, help="extra time to finish trips"
    )
    parser.add_argument("--speed-kph", type=float, default=40.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--json", default=".loadtest/last-run.json", help="where to write the numbers"
    )
    args = parser.parse_args(argv)
    args.cabs = min(args.cabs, world.CABS)
    args.riders = min(args.riders, world.RIDERS)
    try:
        # The default loop: on Windows the selector loop caps at 512 sockets, which 300 riders'
        # WebSockets plus the HTTP pool exceed (the first full run died of it). MQTT therefore
        # runs on paho's own threads, one select() each, outside this loop.
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
