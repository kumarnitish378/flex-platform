# Smart Cab (working name)

Cab operations platform for small and mid-sized cab operators serving corporate employee transport.

**Status:** specification stage. No code yet. All specs are in `docs/`.

## What it does (full vision)
- Employees request cabs in an app and see the cab, driver, live location and ETA.
- Drivers get their trips in order and share GPS while on duty.
- Supervisors see every cab and request on a live map, with waiting timers.
- The system suggests or automatically assigns cabs, pools compatible riders, and reuses nearby cabs.
- Supervisors choose Manual, Semi-auto or Full-auto mode per client, zone or time window, and can override any trip.
- Later: demand prediction and proactive ride offers ("cab leaving 7:10 with 2 colleagues — join?").

## Tech stack (approved)
Flutter (universal app) · Python FastAPI · PostgreSQL + PostGIS · Redis · Mosquitto (MQTT) · Celery ·
Google OR-Tools · OpenStreetMap + OSRM + Nominatim + MapLibre · SimPy simulator · Docker Compose · Caddy · Prometheus/Grafana.

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
docs/        Specifications
```

## Licence notes
Map data © OpenStreetMap contributors, available under the Open Database Licence (ODbL). Attribution must be shown on every map screen.
