"""Verify the core infra containers are up and actually usable (task I01 acceptance).

Checks, in order:
  1. docker and the daemon are available
  2. `docker compose config` parses infra/docker-compose.yml
  3. all three services report healthy
  4. postgres accepts `CREATE EXTENSION postgis` and reports a PostGIS version
  5. redis answers PING
  6. mosquitto accepts a subscription on $SYS/broker/uptime

Everything runs through the docker CLI, so this script needs no Python packages.

    python scripts/check_infra.py          # or:  .\\scripts\\dev.ps1 check-infra
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ["docker", "compose", "-f", str(ROOT / "infra" / "docker-compose.yml")]

PG_USER = "smartcab"
PG_DB = "smartcab"


def run(args: list[str], capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=capture, text=True)


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    return ok


def main() -> int:
    print("Checking core infra (task I01)\n")

    if shutil.which("docker") is None:
        check("docker on PATH", False, "install Docker Desktop, then re-run")
        return 1
    check("docker on PATH", True)

    if run(["docker", "info"]).returncode != 0:
        check("docker daemon running", False, "start Docker Desktop, then re-run")
        return 1
    check("docker daemon running", True)

    results: list[bool] = []

    config = run([*COMPOSE, "config", "--quiet"])
    results.append(
        check("compose file parses", config.returncode == 0, config.stderr.strip()[:160])
    )

    ps = run([*COMPOSE, "ps", "--format", "{{.Service}} {{.State}} {{.Health}}"])
    print(f"\n  docker compose ps:\n{ps.stdout.rstrip() or '    (nothing running)'}\n")
    for service in ("postgres", "redis", "mosquitto"):
        line = next((ln for ln in ps.stdout.splitlines() if ln.startswith(service)), "")
        results.append(check(f"{service} running", "running" in line, line.strip()))

    postgis = run(
        [
            *COMPOSE, "exec", "-T", "postgres",
            "psql", "-U", PG_USER, "-d", PG_DB, "-tAc",
            "CREATE EXTENSION IF NOT EXISTS postgis; SELECT postgis_version();",
        ]
    )
    results.append(
        check(
            "postgres: CREATE EXTENSION postgis",
            postgis.returncode == 0 and postgis.stdout.strip() != "",
            postgis.stdout.strip().splitlines()[-1] if postgis.stdout.strip() else
            postgis.stderr.strip()[:160],
        )
    )

    redis = run([*COMPOSE, "exec", "-T", "redis", "redis-cli", "ping"])
    results.append(
        check("redis: PING", "PONG" in redis.stdout.upper(), redis.stdout.strip())
    )

    # -E exits on SUBACK. The topic must be inside the tree the dev ACL grants
    # (sc/v1/#): a $SYS subscription is denied and would just time out.
    mqtt = run(
        [
            *COMPOSE, "exec", "-T", "mosquitto",
            "mosquitto_sub", "-h", "127.0.0.1", "-p", "1883",
            "-t", "sc/v1/#", "-E", "-i", "check-infra",
        ]
    )
    results.append(
        check(
            "mosquitto: subscribe works",
            mqtt.returncode == 0,
            (mqtt.stdout or mqtt.stderr).strip()[:160],
        )
    )

    passed = all(results)
    print("\n" + ("All infra checks passed." if passed else "Some infra checks FAILED (see above)."))
    if not passed:
        print("Hint: `make up` first, then wait for health checks (~20 s) and re-run.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
