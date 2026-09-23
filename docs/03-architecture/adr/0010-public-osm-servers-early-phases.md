# ADR-0010: Use public OSM servers in early phases

- Status: accepted
- Date: 2026-09-24
- Amends: ADR-0004

## Context
ADR-0004 chose a fully self-hosted OpenStreetMap stack (OSRM, Nominatim, tiles). Self-hosting is correct at
pilot scale, but it costs a 16 GB VM, a multi-hour Nominatim import, a Planetiler tile build and a monthly
data refresh — before a single line of dispatch logic exists. During development and the early phases the
request volume is a handful of routes per minute from one developer machine and the simulator, which does
not justify that setup effort.

The public OpenStreetMap services cover this volume, but they are donated infrastructure with strict usage
policies: low request rates, an identifying `User-Agent`, no bulk or automated scraping, no client-side
autocomplete against Nominatim, and required attribution.

## Decision
Use the **public OSM servers** for development and the early phases, and keep self-hosting as an
upgrade path that is switchable **by configuration only** — no code change:

| Service | Early phases | Upgrade path |
|---|---|---|
| Routing / ETA / matrices | Public OSRM demo server (`router.project-osrm.org`) | Self-hosted OSRM (MLD, car profile) |
| Geocoding | Public Nominatim (`nominatim.openstreetmap.org`) | Self-hosted Nominatim |
| Map tiles | Public OpenStreetMap tile server | Planetiler tiles + tileserver-gl |

Rules that make this safe and policy-compliant:

1. **All map service URLs come from env config** — `OSRM_URL`, `NOMINATIM_URL`, `TILES_URL`. Never hard-coded
   anywhere in backend, app or simulator code.
2. **Routing provider interface** in `backend/app/modules/routing/` with three implementations, selected by
   `ROUTING_PROVIDER`:
   - `osrm` — talks to any OSRM URL, public or self-hosted.
   - `approx` — no network: haversine distance × road factor **1.4**, speed from a time-of-day table
     (config). Results are flagged `approximate: true`.
   - `cached` — wrapper that caches route and table results in Redis with a configurable TTL
     (`ROUTING_CACHE_TTL_SECONDS`); wraps either of the above.
3. **Global rate limiter for public servers**: max **1 request/second per service**, shared across all
   processes (Redis token bucket, so API workers + Celery workers + beat share one budget). Requests that
   would exceed the limit fall back to the `approx` provider and are flagged as approximate rather than
   queued or dropped.
4. **Identifying `User-Agent`** on every request to a public server: app name + contact email from
   `OSM_USER_AGENT` and `OSM_CONTACT_EMAIL`.
5. **No client-side autocomplete against public Nominatim.** Geocoding goes through the backend only, is
   cached, and only runs on an explicit user search action. Employees mainly set pickup/drop with map pins.
6. **Simulator and optimizer use `approx`** (or a self-hosted OSRM if `OSRM_URL` points at one). They must
   never call the public servers in bulk — a single simulator run issues thousands of route requests.
7. **OpenStreetMap attribution on every map screen** ("© OpenStreetMap contributors"), as already required by
   ODbL and screen C-06.
8. **Re-evaluate before the paid pilot goes live**: switch to self-hosted OSRM if request volume or
   reliability requires it (OQ-21).

## Alternatives considered
- **Self-host from day one (ADR-0004 as written).** Correct end state, but blocks early development on map
  data preparation and a large dev machine. Deferred, not abandoned.
- **`approx` provider only until self-hosting.** No infrastructure at all, but ETAs would never be validated
  against real road routing during Phase 1, which is exactly what the pilot must demonstrate.
- **Paid routing API for development.** Excluded by hard rule 7 and ADR-0004.

## Consequences
- Development and the simulator run with no map servers: `make up` is postgres + redis + mosquitto only.
- **ETA accuracy is lower in `approx` mode** (straight line × 1.4, no road network). Responses and UI mark
  such ETAs as approximate; the accuracy targets in `non-functional.md` apply to `osrm` mode.
- Throughput is capped at 1 req/s per service while on public servers — acceptable for development and demos,
  not for a live pilot with 200 vehicles. This is the trigger for the switch to self-hosted OSRM.
- Public servers may be slow or briefly unavailable; the `approx` fallback keeps the platform working, which
  matches the existing degradation rule in `control-model.md` ("OSRM down → approximate ETAs").
- Attribution, `User-Agent` and rate limiting are contractual, not optional. A change that removes them
  breaks the OSM usage policy.
- The self-hosting runbook stays in `dev-environment.md` under "Optional: self-hosting" and is exercised by
  task I02b.
