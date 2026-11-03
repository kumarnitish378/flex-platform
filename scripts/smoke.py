"""End-to-end smoke test against the RUNNING stack, made only of the calls the apps make.

    python scripts/smoke.py                      # against http://localhost:8000/api/v1
    python scripts/smoke.py --api http://192.168.1.57:8000/api/v1
    python scripts/smoke.py --api https://<ip>.sslip.io/api/v1 --otp-command "ssh ... make -s staging-otp PHONE={phone}"
    make smoke

The stack must be up (`make phone-dev`, which turns the test login on) and the demo data loaded
(`make seed-demo`). The script plays the four people the apps are for, in order:

 1. a driver goes on duty, entering the opening odometer, and starts publishing GPS over MQTT
 2. an employee asks for a cab (a day trip)
 3. a supervisor assigns it; the driver starts, picks up, drops, completes; the employee sees the
    ride completed
 4. the night trip: the demo client's night window is opened around "now" for the test, a woman
    asks for a cab, the platform flags the trip, the driver is **refused** until the supervisor
    confirms the escort, then the trip runs; the window is put back afterwards
 5. the driver goes off duty with the closing odometer, and the operator's billing report for the
    month shows the cab's day: GPS km, the odometer, Rs 8/km, and nothing a rider can see

It runs in real time - GPS has to be published as the cab "drives" for the distance to count - and
takes about four minutes. Every step prints PASS or FAIL; the first failure stops the run and the
steps after it are listed as SKIP. Exit code 0 only when every step passed.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app import demo_seed

TIMEZONE = ZoneInfo("Asia/Kolkata")
#: The cab starts near here; riders are pinned within a couple of km of the office so a trip is
#: seconds of driving, not the 10 km the demo homes are (a pin on the map is what the app sends).
OFFICE = (28.5703, 77.3218)
DEPOT = (28.5640, 77.3218)
EARTH = 6_371_000.0


def offset(
    point: tuple[float, float], north_m: float, east_m: float = 0.0
) -> tuple[float, float]:
    lat = point[0] + math.degrees(north_m / EARTH)
    lng = point[1] + math.degrees(east_m / (EARTH * math.cos(math.radians(point[0]))))
    return lat, lng


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


class Failed(Exception):
    pass


@dataclass
class Smoke:
    api: str
    speed_kph: float
    #: Shell command that prints the one-time code just sent to `{phone}` (staging, where the test
    #: login does not exist). Empty: use the dev/test/sim test login.
    otp_command: str = ""
    http: httpx.Client = field(init=False)
    tokens: dict[str, str] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    results: list[tuple[str, str, str]] = field(default_factory=list)
    mqtt: Any = None
    position: tuple[float, float] = DEPOT
    driven_m: float = 0.0
    topic: str = ""

    def __post_init__(self) -> None:
        self.http = httpx.Client(base_url=self.api, timeout=30)

    # --- plumbing -----------------------------------------------------------------------

    def call(
        self,
        who: str,
        method: str,
        path: str,
        expect: int | tuple[int, ...] = 200,
        **kw: Any,
    ) -> Any:
        headers = (
            {"Authorization": f"Bearer {self.tokens[who]}"}
            if who in self.tokens
            else {}
        )
        response = self.http.request(method, path, headers=headers, **kw)
        wanted = (expect,) if isinstance(expect, int) else expect
        if response.status_code not in wanted:
            raise Failed(
                f"{method} {path} -> {response.status_code} (wanted {wanted}): {response.text[:300]}"
            )
        return (
            response.json()
            if response.content and "json" in response.headers.get("content-type", "")
            else response.text
        )

    def login(self, who: str, phone: str) -> None:
        if not self.otp_command:
            body = self.call("-", "POST", "/auth/test-login", json={"phone": phone})
            self.tokens[who] = body["access_token"]
            return
        # The real login: ask for a code, fetch it the way the operator would (the console OTP
        # provider logs it), and verify - what a phone does once SMS exists.
        self.call("-", "POST", "/auth/otp/request", (200, 202, 204), json={"phone": phone})
        time.sleep(1.5)
        done = subprocess.run(
            self.otp_command.replace("{phone}", phone),
            shell=True,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        words = done.stdout.split()
        if done.returncode != 0 or not words:
            raise Failed(f"could not fetch the code for {phone}: {done.stderr.strip()[:200]}")
        body = self.call(
            "-", "POST", "/auth/otp/verify", json={"phone": phone, "code": words[-1]}
        )
        self.tokens[who] = body["access_token"]

    def event(self) -> dict[str, Any]:
        return {
            "client_event_id": str(uuid.uuid4()),
            "occurred_at": datetime.now(TIMEZONE).astimezone().isoformat(),
            "lat": self.position[0],
            "lng": self.position[1],
        }

    def publish(self) -> None:
        import json

        payload = {
            "v": 1,
            "ts": datetime.now().astimezone().isoformat(),
            "lat": self.position[0],
            "lng": self.position[1],
            "spd": self.speed_kph / 3.6,
            "acc": 5.0,
            "src": "app",
        }
        info = self.mqtt.publish(self.topic, json.dumps(payload), qos=0)
        info.wait_for_publish(5)

    def drive_to(self, target: tuple[float, float]) -> None:
        """Publish pings along a straight line to `target` at the chosen speed, in real time."""
        step_s = 3.0
        hop = self.speed_kph / 3.6 * step_s
        distance = metres(self.position, target)
        steps = max(int(distance // hop), 1)
        start = self.position
        for i in range(1, steps + 1):
            fraction = i / steps
            here = (
                start[0] + (target[0] - start[0]) * fraction,
                start[1] + (target[1] - start[1]) * fraction,
            )
            self.driven_m += metres(self.position, here)
            self.position = here
            self.publish()
            time.sleep(step_s)

    def step(self, name: str, action: Callable[[], str | None]) -> None:
        if any(status == "FAIL" for _, status, _ in self.results):
            self.results.append((name, "SKIP", ""))
            print(f"SKIP  {name}")
            return
        started = time.monotonic()
        try:
            detail = action() or ""
        except Failed as exc:
            self.results.append((name, "FAIL", str(exc)))
            print(f"FAIL  {name}\n      {exc}")
            return
        except Exception as exc:  # noqa: BLE001 - any surprise is a failed step, not a crash
            self.results.append((name, "FAIL", f"{type(exc).__name__}: {exc}"))
            print(f"FAIL  {name}\n      {type(exc).__name__}: {exc}")
            return
        took = time.monotonic() - started
        self.results.append((name, "PASS", detail))
        print(f"PASS  {name}  ({took:.1f}s){'  ' + detail if detail else ''}")

    # --- the scenario -------------------------------------------------------------------------

    def run(self) -> bool:
        self.step("stack is up", self.s_health)
        self.step(
            "log in as operator admin, supervisor, driver and two riders", self.s_logins
        )
        self.step(
            "clean slate: nobody left on duty or waiting from an earlier run",
            self.s_clean,
        )
        self.step("driver goes on duty with the opening odometer", self.s_on_duty)
        self.step(
            "driver publishes GPS over MQTT and the supervisor sees the cab", self.s_gps
        )
        self.step(
            "day trip: employee asks for a cab", lambda: self.s_request("man", "day")
        )
        self.step("day trip: supervisor assigns the cab", lambda: self.s_assign("day"))
        self.step(
            "day trip: driver starts (no escort needed)", lambda: self.s_start("day")
        )
        self.step(
            "day trip: driver collects the rider and drops them at the office",
            lambda: self.s_ride("day"),
        )
        self.step("day trip: driver completes", lambda: self.s_complete("day"))
        self.step(
            "day trip: the employee sees the ride completed",
            lambda: self.s_employee_sees("man", "day"),
        )
        self.step(
            "night: the demo client's night window is opened around now",
            self.s_open_night,
        )
        self.step(
            "night trip: a woman asks for a cab and the supervisor assigns it",
            self.s_night_assign,
        )
        self.step(
            "night trip: the supervisor sees it flagged and an alert is raised",
            self.s_night_flagged,
        )
        self.step(
            "night trip: the driver is refused until the escort is confirmed",
            self.s_night_refused,
        )
        self.step(
            "night trip: the supervisor confirms the escort and the driver starts",
            self.s_night_start,
        )
        self.step("night trip: collect, drop and complete", self.s_night_ride)
        self.step(
            "night trip: the employee sees the ride completed",
            lambda: self.s_employee_sees("woman", "night"),
        )
        self.step("night: the demo client's window is put back", self.s_close_night)
        self.step("driver goes off duty with the closing odometer", self.s_off_duty)
        self.step(
            "billing: the cab's day appears with GPS km, odometer and Rs 8/km",
            self.s_billing,
        )
        self.step("riders see no charge anywhere", self.s_no_charge)
        return all(status == "PASS" for _, status, _ in self.results)

    # steps ---------------------------------------------------------------------------------

    def s_health(self) -> str:
        root = self.api.rsplit("/api/", 1)[0]
        response = httpx.get(f"{root}/health/live", timeout=10)
        if response.status_code != 200:
            raise Failed(f"{root}/health/live -> {response.status_code}")
        return root

    def s_logins(self) -> str:
        self.login("admin", demo_seed.OPERATOR_ADMIN)
        self.login("supervisor", demo_seed.SUPERVISOR)
        self.login("driver", demo_seed.driver_phone(1))
        self.login("man", demo_seed.employee_phone(2))
        self.login("woman", demo_seed.employee_phone(1))
        me = self.call("admin", "GET", "/auth/me")
        self.state["operator_roles"] = me["roles"]
        return "5 logins, no OTP"

    def s_clean(self) -> str:
        """A run that failed half way leaves a driver on duty and riders waiting; tidy up first."""
        cancelled = 0
        for who in ("man", "woman"):
            for request in self.call(who, "GET", "/ride-requests/mine?active=true")[
                "items"
            ]:
                self.call(
                    who,
                    "POST",
                    f"/ride-requests/{request['id']}/cancel",
                    (200, 204, 409),
                    json={"reason": "smoke cleanup"},
                )
                cancelled += 1
        duty = self.call("driver", "GET", "/driver/duty")
        if duty["on_duty"]:
            for trip in self.call("driver", "GET", "/driver/trips?scope=active")[
                "items"
            ]:
                self.http.post(
                    f"/driver/trips/{trip['id']}/complete",
                    json=self.event(),
                    headers={"Authorization": f"Bearer {self.tokens['driver']}"},
                )
            self.call("driver", "POST", "/driver/duty", json={"on_duty": False})
        return f"{cancelled} stale request(s) cancelled" + (
            ", driver taken off duty" if duty["on_duty"] else ""
        )

    def s_on_duty(self) -> str:
        self.state["odometer_open"] = 15000.0
        body = self.call(
            "driver",
            "POST",
            "/driver/duty",
            json={"on_duty": True, "odometer_km": self.state["odometer_open"]},
        )
        if not body["on_duty"] or not body.get("mqtt") or not body.get("gps"):
            raise Failed(f"duty response incomplete: {body}")
        self.state["duty"] = body
        self.state["vehicle_id"] = body["vehicle_id"]
        return (
            f"broker {body['mqtt']['host']}:{body['mqtt']['port']}, gps {body['gps']}"
        )

    def s_gps(self) -> str:
        import paho.mqtt.client as mqtt

        duty = self.state["duty"]["mqtt"]
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=f"smoke-{uuid.uuid4().hex[:8]}"
        )
        client.username_pw_set(duty["username"], duty["password"])
        if duty.get("tls"):
            client.tls_set()  # staging: MQTTS on 8883 with the certificate Caddy obtained
        client.connect(duty["host"], duty["port"], keepalive=30)
        client.loop_start()
        self.mqtt = client
        self.topic = f"{duty['topic_prefix']}/gps"
        self.position = DEPOT
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            self.publish()
            time.sleep(2)
            for vehicle in self.call("supervisor", "GET", "/dispatch/vehicles")[
                "items"
            ]:
                if (
                    vehicle["id"] == self.state["vehicle_id"]
                    and vehicle.get("position")
                    and not vehicle["stale"]
                ):
                    return f"{vehicle['registration_no']} at {vehicle['position']}"
        raise Failed(
            "the supervisor never saw a fresh position (ingestor running? broker reachable?)"
        )

    def trip(self, tag: str) -> dict[str, Any]:
        return self.state[f"trip_{tag}"]

    def s_request(self, who: str, tag: str) -> str:
        pin = offset(OFFICE, -1500, 300 if tag == "day" else -300)
        when = (datetime.now().astimezone() + timedelta(minutes=20)).isoformat()
        body = self.call(
            who,
            "POST",
            "/ride-requests",
            201,
            json={
                "direction": "to_office",
                "requested_time": when,
                "location": {"lat": pin[0], "lng": pin[1]},
                "landmark": "smoke test pin",
            },
        )
        self.state[f"request_{tag}"] = body["id"]
        self.state[f"pin_{tag}"] = pin
        return f"request {body['id'][:8]} status {body['status']}"

    def s_assign(self, tag: str) -> str:
        request_id = self.state[f"request_{tag}"]
        queue = self.call("supervisor", "GET", "/dispatch/requests")["items"]
        if request_id not in {item["id"] for item in queue}:
            raise Failed("the supervisor's queue does not show the request")
        trip = self.call(
            "supervisor",
            "POST",
            "/dispatch/assign",
            json={"request_id": request_id, "vehicle_id": self.state["vehicle_id"]},
        )
        self.state[f"trip_{tag}"] = trip
        # The driver's phone must be able to find the trip it was just given. A new trip is
        # `planned`, which only scope=upcoming lists (the default, scope=active, is dispatched +
        # in_progress): the load test found the driver app asking for the default.
        upcoming = self.call("driver", "GET", "/driver/trips?scope=upcoming")["items"]
        if trip["id"] not in {item["id"] for item in upcoming}:
            raise Failed("the driver's upcoming list does not show the trip just assigned")
        return f"trip {trip['id'][:8]} with {len(trip['stops'])} stops"

    def s_start(self, tag: str) -> str:
        trip = self.trip(tag)
        self.call(
            "driver", "POST", f"/driver/trips/{trip['id']}/start", json=self.event()
        )
        return "started"

    def stops(self, tag: str) -> list[dict[str, Any]]:
        mine = self.call("driver", "GET", "/driver/trips?scope=active")["items"]
        found = [t for t in mine if t["id"] == self.trip(tag)["id"]]
        if not found:
            raise Failed("the trip is not in the driver's active list")
        return sorted(found[0]["stops"], key=lambda s: s["sequence"])

    def s_ride(self, tag: str) -> str:
        for stop in self.stops(tag):
            target = (stop["location"]["lat"], stop["location"]["lng"])
            self.drive_to(target)
            self.call(
                "driver",
                "POST",
                f"/driver/stops/{stop['id']}/arrived",
                json=self.event(),
            )
            self.call(
                "driver", "POST", f"/driver/stops/{stop['id']}/done", json=self.event()
            )
        return f"{self.driven_m / 1000:.2f} km driven so far"

    def s_complete(self, tag: str) -> str:
        self.call(
            "driver",
            "POST",
            f"/driver/trips/{self.trip(tag)['id']}/complete",
            json=self.event(),
        )
        return "completed"

    def s_employee_sees(self, who: str, tag: str) -> str:
        request = self.call(
            who, "GET", f"/ride-requests/{self.state[f'request_{tag}']}"
        )
        if request["status"] != "dropped":
            raise Failed(
                f"the rider sees status {request['status']!r}, expected the ride finished (dropped)"
            )
        return "status dropped"

    # night -----------------------------------------------------------------------------------

    def client_id(self) -> str:
        if "client_id" not in self.state:
            clients = self.call("admin", "GET", "/admin/clients")["items"]
            self.state["client_id"] = next(
                c["id"] for c in clients if c["name"] == demo_seed.CLIENT_NAME
            )
        return str(self.state["client_id"])

    def s_open_night(self) -> str:
        path = f"/admin/clients/{self.client_id()}/policy"
        current = self.call("admin", "GET", path)
        self.state["policy_before"] = {
            "night_safety_enabled": current.get("night_safety_enabled"),
            "night_start": current.get("night_start"),
            "night_end": current.get("night_end"),
        }
        now = datetime.now(TIMEZONE)
        window = {
            "night_safety_enabled": True,
            "night_start": (now - timedelta(hours=1)).strftime("%H:%M"),
            "night_end": (now + timedelta(hours=2)).strftime("%H:%M"),
        }
        self.call("admin", "PUT", path, json=window)
        return f"{window['night_start']}-{window['night_end']} IST (was {self.state['policy_before']['night_start']}-{self.state['policy_before']['night_end']})"

    def s_night_assign(self) -> str:
        self.s_request("woman", "night")
        return self.s_assign("night")

    def s_night_flagged(self) -> str:
        trips = self.call("supervisor", "GET", "/dispatch/trips")["items"]
        ours = next((t for t in trips if t["id"] == self.trip("night")["id"]), None)
        if ours is None or not ours.get("escort") or not ours["escort"]["required"]:
            raise Failed(f"the trip is not flagged: {ours and ours.get('escort')}")
        alerts = self.call("supervisor", "GET", "/alerts?status=open")["items"]
        mine = [
            a
            for a in alerts
            if a["type"] == "escort_required" and a.get("trip_id") == ours["id"]
        ]
        if not mine:
            raise Failed("no escort_required alert was raised for the trip")
        return f"reason {ours['escort']['reason']}, alert {mine[0]['id'][:8]}"

    def s_night_refused(self) -> str:
        response = self.http.post(
            f"/driver/trips/{self.trip('night')['id']}/start",
            json=self.event(),
            headers={"Authorization": f"Bearer {self.tokens['driver']}"},
        )
        body = response.json()
        if (
            response.status_code != 409
            or body.get("details", {}).get("reason") != "escort_confirmation_required"
        ):
            raise Failed(
                f"expected a 409 escort_confirmation_required, got {response.status_code}: {response.text[:200]}"
            )
        return "409 escort_confirmation_required"

    def s_night_start(self) -> str:
        confirmed = self.call(
            "supervisor",
            "POST",
            f"/dispatch/trips/{self.trip('night')['id']}/escort-confirmation",
            json={"basis": "escort_arranged", "note": "smoke test escort"},
        )
        if not confirmed["escort"]["confirmed"]:
            raise Failed(f"not confirmed: {confirmed['escort']}")
        self.call(
            "driver",
            "POST",
            f"/driver/trips/{self.trip('night')['id']}/start",
            json=self.event(),
        )
        who = confirmed["escort"]["confirmed_by"]
        return f"confirmed by {who[:8]}, trip started"

    def s_night_ride(self) -> str:
        self.s_ride("night")
        return self.s_complete("night")

    def s_close_night(self) -> str:
        # Always the demo client's own window: restoring "what it was" would keep a window left
        # open by an earlier run that died half way.
        restore = {
            "night_safety_enabled": True,
            "night_start": demo_seed.NIGHT_START.strftime("%H:%M"),
            "night_end": demo_seed.NIGHT_END.strftime("%H:%M"),
        }
        self.call(
            "admin", "PUT", f"/admin/clients/{self.client_id()}/policy", json=restore
        )
        return f"back to {restore['night_start']}-{restore['night_end']}"

    # off duty and money ---------------------------------------------------------------------------

    def s_off_duty(self) -> str:
        time.sleep(8)  # the ingestor flushes pings in batches of five seconds
        km = self.driven_m / 1000.0
        self.state["odometer_close"] = round(self.state["odometer_open"] + km * 1.02, 1)
        self.state["driven_km"] = km
        self.call(
            "driver",
            "POST",
            "/driver/duty",
            json={"on_duty": False, "odometer_km": self.state["odometer_close"]},
        )
        if self.mqtt is not None:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
        return (
            f"closing odometer {self.state['odometer_close']} for {km:.2f} km published"
        )

    def s_billing(self) -> str:
        month = datetime.now(TIMEZONE).strftime("%Y-%m")
        today = datetime.now(TIMEZONE).date().isoformat()
        report = self.call(
            "admin",
            "GET",
            f"/reports/billing?month={month}&client_id={self.client_id()}",
        )
        if report["treatment"]["rate_per_km"] != 8.0:
            raise Failed(
                f"rate is {report['treatment']['rate_per_km']}, expected Rs 8/km (run make seed-demo)"
            )
        rows = [
            r for r in report["rows"] if r["date"] == today and r["cab"] == "DL01DEMO01"
        ]
        if not rows:
            raise Failed("no row for DL01DEMO01 today")
        row = rows[-1]
        published = self.state["driven_km"]
        # A cab's day sums every duty session it had; this run's is the latest of them.
        mine = row["sessions"][-1]
        if mine["gps_km"] is None or not (
            0.7 * published <= mine["gps_km"] <= 1.1 * published
        ):
            raise Failed(
                f"this session's GPS km {mine['gps_km']} is not close to the {published:.2f} km published"
            )
        if (
            mine["odometer_km"] is None
            or abs(
                mine["odometer_km"]
                - (self.state["odometer_close"] - self.state["odometer_open"])
            )
            > 0.01
        ):
            raise Failed(f"the session's odometer figure is {mine['odometer_km']}")
        if row["gps_km"] < mine["gps_km"] - 0.001 or row["odometer_km"] is None:
            raise Failed("the day's totals do not include this session")
        expected = round(row["billed_km"] * 8.0, 2)
        if abs((row["amount"] or 0) - expected) > 0.011:
            raise Failed(f"amount {row['amount']} != billed_km x 8 = {expected}")
        flags = [f for f in row["flags"] if f != "no_client_trips"]
        return (
            f"this session {mine['gps_km']} GPS km / {mine['odometer_km']} odometer km; "
            f"the cab's day {row['gps_km']} GPS km, billed {row['billed_km']} km = Rs {row['amount']}, flags {flags}"
        )

    def s_no_charge(self) -> str:
        for who in ("man", "woman"):
            response = self.http.get(
                f"/reports/billing?month={datetime.now(TIMEZONE).strftime('%Y-%m')}",
                headers={"Authorization": f"Bearer {self.tokens[who]}"},
            )
            if response.status_code != 403:
                raise Failed(
                    f"a rider got {response.status_code} from /reports/billing"
                )
        request = self.call("man", "GET", f"/ride-requests/{self.state['request_day']}")
        money = [
            k
            for k in request
            if any(
                w in k
                for w in ("amount", "price", "charge", "fare", "cost", "km_billed")
            )
        ]
        if money:
            raise Failed(f"the rider's request carries money fields: {money}")
        return "riders get 403 on billing and no money field on their rides"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--api", default="http://localhost:8000/api/v1")
    parser.add_argument(
        "--speed-kph", type=float, default=100.0, help="simulated cab speed (below 160)"
    )
    args = parser.parse_args()

    print(f"smoke test against {args.api}\n")
    smoke = Smoke(args.api, args.speed_kph)
    ok = smoke.run()
    passed = sum(1 for _, status, _ in smoke.results if status == "PASS")
    print(f"\n{passed}/{len(smoke.results)} steps passed" + ("" if ok else " - FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
