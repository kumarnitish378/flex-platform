# Smart Cab (working name)

Cab operations platform for small and mid-sized cab operators serving corporate employee transport.

**Status:** early implementation (Phase 0). Specs in `docs/` are the source of truth; current work is
tracked in `docs/06-phases/phase-1-tasks.md`.

## What it does (full vision)
- Employees request cabs in an app and see the cab, driver, live location and ETA.
- Drivers get their trips in order and share GPS while on duty.
- Supervisors see every cab and request on a live map, with waiting timers.
- The system suggests or automatically assigns cabs, pools compatible riders, and reuses nearby cabs.
- Supervisors choose Manual, Semi-auto or Full-auto mode per client, zone or time window, and can override any trip.
- Later: demand prediction and proactive ride offers ("cab leaving 7:10 with 2 colleagues — join?").

## Tech stack (approved)
Flutter (universal app) · Python FastAPI · PostgreSQL + PostGIS · Redis · Mosquitto (MQTT) · Celery ·
Google OR-Tools · OpenStreetMap + OSRM + MapLibre raster tiles · SimPy simulator · Docker Compose · Caddy · Prometheus/Grafana.

## Start here
1. `docs/00-product/vision-and-scope.md` — what and why
2. `docs/06-phases/roadmap.md` — phases
3. `docs/05-engineering/dev-environment.md` — local setup
4. `CLAUDE.md` — rules for AI coding agents (and humans)

## Repository layout
```
app/         Flutter universal app
backend/     FastAPI + workers + migrations
simulator/   Closed-loop simulator
infra/       Docker Compose and service configs
scripts/     Developer commands (make targets and their PowerShell equivalents)
docs/        Specifications
```

## Developer commands
`make help` lists every target, what it does, and whether it is usable yet (targets belonging to
unfinished tasks say which task creates them).

| | |
|---|---|
| `make help` | list targets |
| `make install` | create `.venv` and install backend + simulator dependencies |
| `make up` / `make down` | start / stop core infra containers (postgres, redis, mosquitto) |
| `make test` | backend tests |
| `make lint` | ruff check, ruff format --check, mypy |
| `make backend-dev` | run the API with reload |
| `make stack-up` / `make stack-down` | start / stop the backend a scenario drives (broker, migrations, API, GPS ingestor) |
| `make sim-quick` / `make sim-full` | simulator suites, against that backend |
| `make sim-offline` | the quick suite with no backend: proves the agents run, **does not check assertions** |

### Running scenarios

A scenario is only a test when there is a platform to test. Run the stack first:

```bash
make up          # postgres, redis
make stack-up    # broker, migrations, API, GPS ingestor
make sim-quick   # S01 against it; assertions are evaluated
make stack-down
```

Without `--platform` a run still exercises the agents and prints its metrics, but ends
with `assert not checked` rather than a pass — an offline run cannot tell you whether
every request reached a terminal state, because there were no requests.

**One run at a time per backend.** Seeding truncates every table, so a second run
started against the same backend would destroy the first one's world. The backend
refuses this with a 409 naming the run that holds it; pass `force` only to clear a claim
left behind by a run that crashed.

`make sim-quick` is what PR CI runs (S01, one simulated hour). The full suite — six
scenarios, two of them sixteen simulated hours — runs nightly in
`.github/workflows/sim-nightly.yml` and uploads each run's metrics and logs as artifacts.


**Windows:** GNU make on Windows runs recipes through `cmd.exe` and is easy to break, so every target
has an identical PowerShell entry point in `scripts/dev.ps1`:

```powershell
.\scripts\dev.ps1 help
.\scripts\dev.ps1 install
.\scripts\dev.ps1 test
```

Both routes run the same underlying commands — use whichever works on your machine.

## Configuration
Copy `.env.example` to `.env` and edit it; `.env` is git-ignored and must never be committed.
Map service URLs (`OSRM_URL`, `TILES_URL`) always come from configuration, never from code, and
`OSM_CONTACT_EMAIL` must be a real address before anything calls a public OSM server (ADR-0010).

## Licence
Proprietary — all rights reserved. See [LICENSE](LICENSE). The source is public for visibility only;
it is not open source and no usage rights are granted.

Map data © OpenStreetMap contributors, available under the Open Database Licence (ODbL). ODbL covers
that data, not this code. Attribution must be shown on every map screen (ADR-0010).
