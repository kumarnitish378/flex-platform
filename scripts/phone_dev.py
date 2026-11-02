"""`make phone-dev`: bring the whole stack up so a phone on the same Wi-Fi can use it.

What a phone needs that `make backend-dev` does not give it:

* the API listening on **0.0.0.0**, not 127.0.0.1;
* the MQTT broker reachable, and `/driver/duty` telling the phone to connect to the laptop's
  **LAN address** (`MQTT_PUBLIC_HOST`), not to `localhost` or a Docker service name;
* the tile server reachable (when its map data has been prepared);
* `AUTH_TEST_LOGIN=true` with `APP_ENV=dev`, so the app can log in by phone number with no OTP.

Everything the backend needs besides the API is started as well - the GPS ingestor, a Celery
worker and the beat scheduler - because the escort alert, request expiry and stale-vehicle sweeps
are all beat jobs. Logs and pids live in `.phone-dev/`. `make phone-dev-stop` stops them.

Usage:  python scripts/phone_dev.py up | down | info
Env:    PHONE_DEV_HOST  override the detected LAN address (e.g. a hotspot or VPN address)
        API_PORT, MQTT_PORT, TILES_PORT
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".phone-dev"

API_PORT = int(os.environ.get("API_PORT", "8000"))
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TILES_PORT = int(os.environ.get("TILES_PORT", "8081"))
TILE_STYLE = "basic"
#: The public OSM tiles, used only when the self-hosted tile server has no data. The app sends
#: its own User-Agent and honours the cache headers (ADR-0010 rule 7).
PUBLIC_TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

PROCESSES = {
    "api": ["-m", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0"],
    "ingestor": ["-m", "app.ingestor"],
    "worker": [
        "-m",
        "celery",
        "-A",
        "app.workers.celery_app",
        "worker",
        "--loglevel=info",
        "-P",
        "solo",
    ],
    "beat": ["-m", "celery", "-A", "app.workers.celery_app", "beat", "--loglevel=info"],
}


# --- pure helpers (unit-tested) ----------------------------------------------------------


def lan_ip(override: str | None = None) -> str:
    """The address a phone on the same network can reach this machine on.

    A UDP "connect" sends nothing: it only asks the OS which interface it would use to reach
    the outside, and that interface's address is the LAN one.
    """
    if override:
        return override
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        address: str = probe.getsockname()[0]
    except OSError:
        address = ""
    finally:
        probe.close()
    if not address or address.startswith("127."):
        address = socket.gethostbyname(socket.gethostname())
    return address


def backend_environment(
    host: str, base: dict[str, str] | None = None
) -> dict[str, str]:
    """The environment the backend processes run with for phone testing."""
    env = dict(os.environ if base is None else base)
    env.update(
        {
            "APP_ENV": "dev",
            "AUTH_TEST_LOGIN": "true",
            # What /driver/duty hands the phone. The backend itself still reaches the broker
            # on localhost (MQTT_HOST), which is a different question.
            "MQTT_PUBLIC_HOST": host,
            "MQTT_PUBLIC_PORT": str(MQTT_PORT),
            "MQTT_PUBLIC_TLS": "false",
        }
    )
    env.setdefault("MQTT_HOST", "localhost")
    return env


def urls(host: str, tiles_ready: bool) -> dict[str, str]:
    return {
        "api": f"http://{host}:{API_PORT}/api/v1",
        "docs": f"http://{host}:{API_PORT}/docs",
        "health": f"http://{host}:{API_PORT}/health/live",
        "mqtt": f"{host}:{MQTT_PORT}",
        "tiles": (
            f"http://{host}:{TILES_PORT}/styles/{TILE_STYLE}/{{z}}/{{x}}/{{y}}.png"
            if tiles_ready
            else PUBLIC_TILES
        ),
    }


def dart_defines(
    host: str, tiles_ready: bool, contact: str = "you@example.com"
) -> list[str]:
    """The exact `--dart-define` values for a phone build (`app/lib/core/env.dart`)."""
    found = urls(host, tiles_ready)
    return [
        f"--dart-define=API_BASE_URL={found['api']}",
        f"--dart-define=MQTT_HOST={host}",
        f"--dart-define=MQTT_PORT={MQTT_PORT}",
        f"--dart-define=TILES_URL={found['tiles']}",
        f"--dart-define=OSM_CONTACT_EMAIL={contact}",
        "--dart-define=APP_TESTING=true",
    ]


def tiles_ready() -> bool:
    return (ROOT / "infra" / "maps" / "tiles" / "ncr.mbtiles").exists()


# --- process control -----------------------------------------------------------------------


def python() -> str:
    candidate = (
        ROOT
        / ".venv"
        / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    )
    return str(candidate if candidate.exists() else sys.executable)


def compose(*args: str) -> None:
    subprocess.run(["docker", "compose", *args], cwd=ROOT, check=True)


def wait_for(check: Callable[[], bool], what: str, seconds: int = 90) -> None:
    for _ in range(seconds):
        if check():
            return
        time.sleep(1)
    raise SystemExit(f"{what} never became ready")


def api_is_up() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{API_PORT}/health/live", timeout=2
        ):
            return True
    except OSError:
        return False


def port_in_use(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def start(name: str, env: dict[str, str]) -> None:
    STATE.mkdir(exist_ok=True)
    arguments = list(PROCESSES[name])
    if name == "api":
        arguments += ["--port", str(API_PORT), "--log-level", "info"]
    log = (STATE / f"{name}.log").open("w", encoding="utf-8")
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    process = subprocess.Popen(
        [python(), *arguments],
        cwd=ROOT / "backend",
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )
    (STATE / f"{name}.pid").write_text(str(process.pid))


def stop_all() -> None:
    for pid_file in sorted(STATE.glob("*.pid")):
        pid = int(pid_file.read_text())
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            try:
                os.kill(pid, 15)
            except OSError:
                pass
        pid_file.unlink()
        print(f"stopped {pid_file.stem} ({pid})")


def print_info(host: str, ready: bool) -> None:
    found = urls(host, ready)
    print()
    print("Phone testing is up. On the phone (same Wi-Fi):")
    print(f"  API        {found['api']}")
    print(f"  API docs   {found['docs']}")
    print(
        f"  MQTT       {found['mqtt']}  (the driver app is told this by /driver/duty)"
    )
    print(f"  Tiles      {found['tiles']}")
    if not ready:
        print(
            "             (self-hosted tiles not prepared - using the public OSM tiles)"
        )
    print(
        "  Open the API docs URL in the phone's browser first: if it loads, the network is fine."
    )
    print()
    print("Build the app with:")
    print("  flutter run " + " ".join(dart_defines(host, ready)))
    print()
    print("Demo logins: run `make seed-demo`, then see docs/runbook-phone-testing.md.")
    print(
        "Windows firewall must allow inbound TCP "
        f"{API_PORT}, {MQTT_PORT}"
        + (f", {TILES_PORT}" if ready else "")
        + " (same runbook)."
    )
    print("Stop everything with: make phone-dev-stop")


def up() -> None:
    host = lan_ip(os.environ.get("PHONE_DEV_HOST"))
    ready = tiles_ready()
    env = backend_environment(host)

    print(f"LAN address: {host}")
    files = ["-f", "infra/docker-compose.yml"]
    if ready:
        files += ["-f", "infra/docker-compose.maps.yml"]
    compose(*files, "up", "-d")
    wait_for(
        lambda: (
            subprocess.run(
                ["docker", "exec", "smartcab-postgres", "pg_isready", "-U", "smartcab"],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        ),
        "postgres",
    )
    subprocess.run(
        [python(), "-m", "alembic", "upgrade", "head"],
        cwd=ROOT / "backend",
        env=env,
        check=True,
    )

    if port_in_use(API_PORT):
        raise SystemExit(
            f"port {API_PORT} is already in use - run `make phone-dev-stop` (or stop the other "
            "backend) first, so the phone does not talk to stale code"
        )
    for name in PROCESSES:
        start(name, env)
        print(f"started {name}")
    wait_for(api_is_up, "the API")
    print_info(host, ready)


def down() -> None:
    if STATE.exists():
        stop_all()
    print("(the Docker infrastructure is left running; `make down` stops it)")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "info"
    if command == "up":
        up()
    elif command == "down":
        down()
    else:
        host_ = lan_ip(os.environ.get("PHONE_DEV_HOST"))
        print_info(host_, tiles_ready())
