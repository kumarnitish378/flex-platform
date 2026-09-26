"""Talking to the real backend (M04, `simulator-spec.md` sections 2 and 5).

The simulator is a **closed loop**: it drives the same API a phone drives, so a bug in
assignment or tracking shows up here rather than in production. Nothing in this module
reaches into the database or imports backend code - if the simulator can do it, a client
can do it.

Three things it needs from the platform:

1. **A world to act in** - `/simctl/reset` seeds the fixture and hands back ids and one
   access token per role.
2. **Shared time** - `/simctl/clock` so the backend's `Clock` and the SimPy clock agree.
   Without this the backend would expire requests on wall-clock time while the simulator
   runs an hour a second.
3. **Credentials to publish GPS** - a driver going on duty is issued the MQTT username
   and password for their vehicle (B11), exactly as the driver app is.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

DEFAULT_TIMEOUT_SECONDS = 10.0


class PlatformError(RuntimeError):
    """The backend refused something the simulator needs. Always fatal to a run."""


@dataclass(frozen=True, slots=True)
class SeededUser:
    role: str
    phone: str
    user_id: uuid.UUID
    access_token: str


@dataclass(frozen=True, slots=True)
class DutyCredentials:
    """What the driver app gets when it goes on duty, and so does a simulated driver.

    Includes the broker address and topic prefix, so the simulator publishes where the
    backend told it to rather than reconstructing the topic from `mqtt-topics.md` and
    drifting the day that document changes.
    """

    vehicle_id: uuid.UUID
    host: str
    port: int
    username: str
    password: str
    topic_prefix: str

    @property
    def gps_topic(self) -> str:
        return f"{self.topic_prefix}/gps"


@dataclass(frozen=True, slots=True)
class CreatedRequest:
    id: uuid.UUID
    status: str


@dataclass(slots=True)
class SeededWorld:
    operator_id: uuid.UUID
    client_id: uuid.UUID
    office_ids: list[uuid.UUID] = field(default_factory=list)
    employee_ids: list[uuid.UUID] = field(default_factory=list)
    vehicle_ids: list[uuid.UUID] = field(default_factory=list)
    driver_ids: list[uuid.UUID] = field(default_factory=list)
    users: list[SeededUser] = field(default_factory=list)
    now: datetime | None = None

    def token_for(self, role: str) -> str:
        for user in self.users:
            if user.role == role:
                return user.access_token
        raise PlatformError(f"The reset fixture seeded no {role}")

    def tokens_for(self, role: str) -> list[str]:
        """Every login of a role.

        There is one driver account per seeded cab, because a driver may hold only one
        open duty session (B11): a fleet cannot share an account.
        """
        return [user.access_token for user in self.users if user.role == role]


class PlatformClient:
    """A thin, synchronous client. SimPy is single-threaded, so async buys nothing here."""

    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    # --- the world ------------------------------------------------------------

    def reset(self) -> SeededWorld:
        """Truncate and seed. The only destructive call, and sim-only on the server."""
        body = self._post("/simctl/reset", json={})
        return SeededWorld(
            operator_id=uuid.UUID(body["operator_id"]),
            client_id=uuid.UUID(body["client_id"]),
            office_ids=[uuid.UUID(value) for value in body.get("office_ids", [])],
            employee_ids=[uuid.UUID(value) for value in body.get("employee_ids", [])],
            vehicle_ids=[uuid.UUID(value) for value in body.get("vehicle_ids", [])],
            driver_ids=[uuid.UUID(value) for value in body.get("driver_ids", [])],
            users=[
                SeededUser(
                    role=user["role"],
                    phone=user["phone"],
                    user_id=uuid.UUID(user["user_id"]),
                    access_token=user["access_token"],
                )
                for user in body.get("users", [])
            ],
            now=_parse_time(body.get("now")),
        )

    def apply_config(self, token: str, overrides: dict[str, Any]) -> dict[str, Any]:
        """Push the scenario's `operator.config_overrides` (B05, `PATCH /admin/config`).

        Through the API, not the database: the ranges and the audit trail are part of what
        the scenario is exercising, and a scenario that sets an out-of-range value should
        fail loudly here rather than quietly run with something the product would refuse.
        """
        if not overrides:
            return {}
        return self._patch("/admin/config", json=dict(overrides), token=token)

    # --- time -------------------------------------------------------------------

    def set_clock(self, now: datetime) -> datetime:
        """Move the backend's clock to a simulated instant and run what became due."""
        body = self._put("/simctl/clock", json={"now": now.isoformat()})
        return _parse_time(body["now"]) or now

    def advance_clock(self, seconds: int) -> dict[str, Any]:
        """Advance and report what the jump triggered, so a scenario can assert on it."""
        return self._put("/simctl/clock", json={"advance_seconds": seconds})

    def clock(self) -> datetime | None:
        return _parse_time(self._get("/simctl/clock")["now"])

    # --- driving -------------------------------------------------------------------

    def go_on_duty(self, driver_token: str, vehicle_id: uuid.UUID) -> DutyCredentials:
        """Sign a driver into a cab and collect its MQTT credentials (B11, DRV-02)."""
        body = self._post(
            "/driver/duty",
            json={"on_duty": True, "vehicle_id": str(vehicle_id)},
            token=driver_token,
        )
        mqtt = body.get("mqtt")
        if not mqtt:
            raise PlatformError(
                "Going on duty returned no MQTT credentials; the simulator cannot publish GPS"
            )
        return DutyCredentials(
            vehicle_id=uuid.UUID(str(body.get("vehicle_id") or vehicle_id)),
            host=str(mqtt["host"]),
            port=int(mqtt["port"]),
            username=str(mqtt["username"]),
            password=str(mqtt["password"]),
            topic_prefix=str(mqtt["topic_prefix"]),
        )

    def go_off_duty(self, driver_token: str) -> None:
        self._post("/driver/duty", json={"on_duty": False}, token=driver_token)

    # --- riding (M05) ---------------------------------------------------------------

    def create_request(
        self,
        token: str,
        direction: str,
        requested_time: datetime,
        lat: float | None = None,
        lng: float | None = None,
        landmark: str | None = None,
    ) -> CreatedRequest:
        """`POST /ride-requests` as the employee. The same call the app makes (EMP-02).

        With no coordinates the backend uses the employee's saved home, exactly as the
        app does when a rider taps "home" rather than dropping a pin.
        """
        payload: dict[str, Any] = {
            "direction": direction,
            "requested_time": requested_time.isoformat(),
            "landmark": landmark,
        }
        if lat is not None and lng is not None:
            payload["location"] = {"lat": lat, "lng": lng}
        body = self._post("/ride-requests", json=payload, token=token)
        return CreatedRequest(id=uuid.UUID(body["id"]), status=str(body["status"]))

    def request_status(self, token: str, request_id: uuid.UUID) -> str:
        """What the backend says this request is now. Never inferred locally."""
        body = self._get(f"/ride-requests/{request_id}", token=token)
        return str(body["status"])

    def cancel_request(self, token: str, request_id: uuid.UUID, reason: str) -> str:
        body = self._post(
            f"/ride-requests/{request_id}/cancel", json={"reason": reason}, token=token
        )
        return str(body.get("status", "cancelled"))

    # --- driving a trip (M05) -----------------------------------------------------------

    def driver_trips(self, token: str, scope: str = "active") -> list[dict[str, Any]]:
        """The driver's own trips, with their stops in order (DRV-03)."""
        body = self._get(f"/driver/trips?scope={scope}", token=token)
        items: list[dict[str, Any]] = body.get("items", [])
        return items

    def start_trip(self, token: str, trip_id: uuid.UUID, at: datetime) -> dict[str, Any]:
        return self._driver_event(f"/driver/trips/{trip_id}/start", token, at)

    def complete_trip(self, token: str, trip_id: uuid.UUID, at: datetime) -> dict[str, Any]:
        return self._driver_event(f"/driver/trips/{trip_id}/complete", token, at)

    def stop_action(
        self,
        token: str,
        stop_id: uuid.UUID,
        action: str,
        at: datetime,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        """`arrived`, `done` or `no_show`, with the position the tap happened at."""
        return self._driver_event(f"/driver/stops/{stop_id}/{action}", token, at, lat=lat, lng=lng)

    def report_issue(
        self, token: str, issue_type: str, note: str | None = None, trip_id: uuid.UUID | None = None
    ) -> dict[str, Any]:
        """DRV-06, used by the fault injector."""
        return self._post(
            "/driver/issues",
            json={"type": issue_type, "note": note, "trip_id": str(trip_id) if trip_id else None},
            token=token,
        )

    def _driver_event(
        self,
        path: str,
        token: str,
        at: datetime,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        """Every driver action carries a fresh idempotency key and the tap time (B15)."""
        body: dict[str, Any] = {
            "client_event_id": str(uuid.uuid4()),
            "occurred_at": at.isoformat(),
        }
        if lat is not None and lng is not None:
            body["lat"] = lat
            body["lng"] = lng
        return self._post(path, json=body, token=token)

    # --- reading back ------------------------------------------------------------------

    def live_vehicles(self, supervisor_token: str) -> list[dict[str, Any]]:
        """What the supervisor's live map shows (SUP-01).

        This is how a run proves its cabs are moving: the same endpoint the map reads,
        rather than a database query only the simulator knows how to make.
        """
        body = self._get("/dispatch/vehicles", token=supervisor_token)
        items: list[dict[str, Any]] = body.get("items", [])
        return items

    def health(self) -> bool:
        """Is anything answering?

        The health endpoints sit at the server root, outside the `/api/v1` prefix, so
        this asks the origin rather than the API base.
        """
        try:
            response = self._client.get(f"{self._origin()}/health/live")
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def _origin(self) -> str:
        parsed = httpx.URL(self.base_url)
        return f"{parsed.scheme}://{parsed.netloc.decode()}"

    # --- plumbing --------------------------------------------------------------------------

    def _get(self, path: str, token: str | None = None) -> dict[str, Any]:
        return self._send("GET", path, token=token)

    def _post(self, path: str, json: dict[str, Any], token: str | None = None) -> dict[str, Any]:
        return self._send("POST", path, json=json, token=token)

    def _put(self, path: str, json: dict[str, Any], token: str | None = None) -> dict[str, Any]:
        return self._send("PUT", path, json=json, token=token)

    def _patch(self, path: str, json: dict[str, Any], token: str | None = None) -> dict[str, Any]:
        return self._send("PATCH", path, json=json, token=token)

    def _send(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            response = self._client.request(
                method, f"{self.base_url}{path}", json=json, headers=headers
            )
        except httpx.HTTPError as exc:
            raise PlatformError(f"{method} {path} failed: {exc}") from exc

        if response.status_code >= 400:
            raise PlatformError(
                f"{method} {path} returned {response.status_code}: {response.text[:200]}"
            )
        if not response.content:
            return {}
        parsed: dict[str, Any] = response.json()
        return parsed

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> PlatformClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
