# CLAUDE.md — Agent instructions for Smart Cab

Read this file fully before every task. It is short on purpose; details live in `docs/`.

## What this project is
A cab operations platform sold to **small and mid-sized cab operators** who serve corporate clients.
It replaces phone/WhatsApp dispatch with: live tracking + ETA, assisted and automatic cab assignment,
pooling, supervisor control modes, and (later) demand prediction.

- One **universal Flutter app** (Android first) renders screens by role: employee, driver, supervisor, operator admin, client admin.
- **Backend:** Python + FastAPI modular monolith, PostgreSQL + PostGIS, Redis, MQTT (Mosquitto) for GPS, Celery workers.
- **Maps:** OpenStreetMap only, self-hosted (OSRM routing, Nominatim geocoding, self-hosted vector tiles, MapLibre). **No paid map APIs. No WhatsApp API.**
- **Simulator:** Python + SimPy closed-loop simulator that drives the real API and MQTT (like ArduPilot SITL).

## Repository layout
```
app/         Flutter universal app (Android, later iOS + web dashboards)
backend/     FastAPI service + Celery workers + Alembic migrations
simulator/   SimPy closed-loop simulator + scenario files
infra/       Docker Compose, OSRM, Nominatim, tiles, Mosquitto, Caddy configs
docs/        All specifications (source of truth)
```

## Where to look before you change something
| You are touching | Read first |
|---|---|
| Anything | `docs/00-product/glossary.md` |
| Auth, permissions, which role sees what | `docs/00-product/roles-and-permissions.md` |
| Request / trip states | `docs/02-domain/trip-lifecycle.md` |
| Assignment, pooling, cost function | `docs/02-domain/allocation-rules.md` |
| Modes, overrides, failsafe | `docs/02-domain/control-model.md` |
| Database | `docs/03-architecture/data-model.md` |
| API endpoints | `docs/03-architecture/api-spec.yaml` (contract — change it first, then code) |
| GPS / MQTT | `docs/03-architecture/mqtt-topics.md` |
| App screens | `docs/01-requirements/screens-by-role.md` |
| Simulator | `docs/04-simulation/simulator-spec.md` |
| Code style, structure | `docs/05-engineering/coding-standards.md` |
| Tests | `docs/05-engineering/testing-strategy.md` |
| Current work | `docs/06-phases/phase-1-tasks.md` |

## Hard rules
1. **The API contract is `api-spec.yaml`.** Change the spec first, regenerate the Dart client, then implement. Never let app and backend drift.
2. **Never read the system clock directly in backend domain code.** Use the injected `Clock` (see coding standards). The simulator depends on this.
3. **Authorization is enforced on the server** for every endpoint. Hiding a screen in the app is not security.
4. **Business numbers come from config, not code.** Detour limits, weights, timeouts, windows: see `allocation-rules.md` config keys.
5. **Every state change goes through the state machine** in `trip-lifecycle.md`. No direct status writes.
6. **Overridden or locked trips must never be changed by the optimizer.**
7. **No paid APIs, no WhatsApp API, no Google Maps.** OSM stack only.
8. **Do not invent requirements.** If a spec is missing or ambiguous, stop and add an item to `docs/07-decisions/open-questions.md`, then ask.
9. Record significant design choices as an ADR in `docs/03-architecture/adr/` and a line in `docs/07-decisions/decision-log.md`.
10. Keep secrets out of the repo. Use `.env` (see `docs/05-engineering/dev-environment.md`).

## Commands (once code exists)
```
make up            # start infra (postgres, redis, mosquitto, osrm, nominatim, tiles)
make backend-dev   # run FastAPI with reload
make worker        # run Celery worker
make test          # backend unit + integration tests
make sim-quick     # simulator smoke scenarios (CI)
make sim-full      # full scenario suite
make api-client    # regenerate Dart client from api-spec.yaml
cd app && flutter test
```
If a command in this list does not exist yet, creating it is part of the task that needs it.

## How to work on a task
1. Pick one task from `docs/06-phases/phase-1-tasks.md`. Do only that task.
2. Read the docs listed in the task.
3. Write or update tests first where practical.
4. Implement. Keep changes small and within the task scope.
5. Run lint, type checks and tests. All must pass.
6. Mark the task done in the task file and summarise what changed.

## Definition of done (every task)
- Acceptance criteria in the task are met and demonstrated by tests.
- `ruff`, `mypy`, `pytest` pass (backend); `flutter analyze`, `flutter test` pass (app).
- API spec, docs and migrations updated if behaviour changed.
- No TODOs left without an issue or open-question entry.
