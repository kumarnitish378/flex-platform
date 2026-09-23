# Architecture

## 1. Overview
A **modular monolith** backend (FastAPI) with background workers, a single universal Flutter app, and self-hosted OpenStreetMap services. A closed-loop simulator talks to the same API and MQTT broker as real apps.

```mermaid
flowchart TD
    APP[Flutter app<br/>role-based screens] -->|HTTPS REST + WebSocket| API[FastAPI<br/>modular monolith]
    APP -->|GPS via MQTT| MQ[Mosquitto]
    TRK[ESP32 GPS tracker<br/>optional] --> MQ
    SIM[Simulator] --> API
    SIM --> MQ
    MQ --> ING[GPS ingestor]
    ING --> RT[(Redis)]
    ING --> DB[(PostgreSQL + PostGIS)]
    API --> DB
    API --> RT
    API --> WK[Celery workers<br/>optimizer, ETA, notifications]
    WK --> DB
    WK --> RT
    API --> OSRM[OSRM]
    WK --> OSRM
    API --> NOM[Nominatim]
    WK --> PUSH[FCM / ntfy push]
    APP --> TILES[Tile server]
```

## 2. Backend modules
`backend/app/modules/<name>/` each with `router.py`, `schemas.py`, `service.py`, `repository.py`, `models.py`.

| Module | Responsibility |
|---|---|
| `auth` | OTP login, tokens, roles, active role, permissions |
| `tenancy` | Operators, clients, offices, users |
| `fleet` | Vehicles, drivers, duty state |
| `people` | Employees, CSV import, saved places |
| `requests` | Ride requests, validation, cancellation |
| `trips` | Trips, stops, state machines, driver actions |
| `dispatch` | Candidates, manual assignment, suggestions, modes, overrides, failsafe, pause |
| `optimizer` | Cost function, single insertion, OR-Tools batch solver (Phase 3) |
| `routing` | OSRM client (route, table), ETA service, speed profiles, Nominatim client |
| `tracking` | GPS ingestion, live positions, stale detection, WebSocket fan-out |
| `notifications` | Push (FCM/ntfy), in-app notification records |
| `alerts` | SOS, driver issues, expiry, failsafe, mode prompts |
| `reports` | Metrics, CSV export, billing export |
| `config` | Operator config keys with validation and audit |
| `audit` | Audit log |
| `simctl` | Sim-only: clock control, seeding (enabled only when `APP_ENV=sim`) |
| `prediction` | Phase 4: demand and ready-time models, offers |

Rules:
- Modules talk through **service interfaces**, never another module's repository or tables directly.
- Domain logic (state machines, cost function, hard rules) lives in pure functions in `backend/app/domain/` with no I/O, so it is unit-testable and reused by the simulator's analysis tools.

## 3. Key flows

### 3.1 Employee requests a cab (Phase 1, manual)
```mermaid
sequenceDiagram
    participant E as Employee app
    participant A as API
    participant S as Supervisor app
    participant D as Driver app
    E->>A: POST /ride-requests
    A-->>E: 201 request (queued)
    A-->>S: WS event request.created
    S->>A: GET /dispatch/requests/{id}/candidates
    A-->>S: vehicles with ETA, load
    S->>A: POST /dispatch/assign
    A-->>D: push + WS trip.assigned
    A-->>E: push + WS request.assigned (vehicle, driver, ETA)
    D->>A: trip/stop status updates
    A-->>E: WS vehicle.location, stop.eta, stop.arrived
```

### 3.2 GPS pipeline
1. Driver app publishes to MQTT every 5 s (moving) / 30 s (stationary).
2. `tracking` ingestor (a separate process subscribed to Mosquitto) validates the device, writes the latest position to Redis (`veh:{id}:pos`), appends to `location_ping` in batches (every 5 s), and publishes an internal event.
3. WebSocket hub pushes position to subscribed supervisors and to the employee of the active trip.
4. ETA worker recomputes active stop ETAs every 30 s via OSRM.
5. Nightly job aggregates pings into `road_speed_profile`; weekly job regenerates OSRM speed files (Phase 1 late / Phase 2).

### 3.3 Clock
- Backend code gets time from `Clock` (dependency-injected). `SystemClock` in dev/prod; `SimClock` in `APP_ENV=sim` controlled by `/simctl/clock`.
- Celery schedules and timeouts (failsafe, expiry) use the clock via a scheduler loop that checks due items, not wall-clock `sleep`, so the simulator can accelerate time.

## 4. Realtime
- One WebSocket endpoint `/ws` authenticated with the access token; clients subscribe to channels permitted for their role:
  - `operator.{id}.vehicles`, `operator.{id}.requests`, `operator.{id}.alerts` (supervisor/admin)
  - `trip.{id}` (employee of that trip, assigned driver)
  - `user.{id}` (personal notifications)
- Redis pub/sub connects API workers to the WebSocket hub so it scales to several API processes.

## 5. Deployment (pilot)
Single VM (India region), Docker Compose:
`caddy`, `api` (uvicorn, 2–4 workers), `ingestor`, `worker` (Celery), `beat` (scheduler), `postgres` (PostGIS), `redis`, `mosquitto`, `osrm`, `nominatim`, `tileserver`, `prometheus`, `grafana`.
Environments: `dev` (local), `sim` (simulator + accelerated clock), `staging`, `prod`.

## 6. Scaling path
- More API workers behind Caddy; Redis pub/sub for WebSockets.
- Move `ingestor` to Go if GPS load exceeds ~1,000 msg/s.
- Split `optimizer` into its own service if solver runs block workers.
- Kubernetes only at multi-operator scale (Phase 5).
