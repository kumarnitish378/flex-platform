# ADR-0010: Use public OSM servers in early phases

- Status: accepted (amended 2026-09-24 — see §Amendment)
- Date: 2026-09-24
- Amends: ADR-0004

## Context
ADR-0004 chose a fully self-hosted OpenStreetMap stack (OSRM, Nominatim, tiles). Self-hosting is correct at
pilot scale, but it costs a 16 GB VM, a multi-hour Nominatim import, a Planetiler tile build and a monthly
data refresh — before a single line of dispatch logic exists. During development and the early phases the
request volume is a handful of routes per minute from one developer machine and the simulator, which does
not justify that setup effort.

The public OpenStreetMap services cover this volume, but they are donated infrastructure with strict usage
policies: low request rates, an identifying `User-Agent`, no bulk or automated scraping, required
attribution, and — for Nominatim — an outright prohibition on vehicle-tracking applications (see §Amendment).

## Decision
Use the **public OSM servers** for development and the early phases, and keep self-hosting as an
upgrade path that is switchable **by configuration only** — no code change:

| Service | Early phases | Upgrade path |
|---|---|---|
| Routing / ETA / matrices | Public OSRM demo server (`router.project-osrm.org`) | Self-hosted OSRM (MLD, car profile) |
| Geocoding | **None** — map pins + landmark text (see §Amendment) | Self-hosted Nominatim (optional, I02c) |
| Map tiles | Public OpenStreetMap raster tiles (`tile.openstreetmap.org`) | Planetiler tiles + tileserver-gl |

Rules that make this safe and policy-compliant:

1. **All map service URLs come from env config** — `OSRM_URL`, `TILES_URL` (and `NOMINATIM_URL` only when a
   self-hosted instance exists). Never hard-coded anywhere in backend, app or simulator code.
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
   `OSM_USER_AGENT` and `OSM_CONTACT_EMAIL`. The app uses `flex-platform/<version> (contact:
   <OSM_CONTACT_EMAIL>)` for tile requests — never a library default (§A2).
5. **No geocoding against public Nominatim at all** (revised in §Amendment). Phase 1 ships without
   geocoding: employees and admins set locations with map pins + landmark text.
6. **Simulator and optimizer use `approx`** (or a self-hosted OSRM if `OSRM_URL` points at one). They must
   never call the public servers in bulk — a single simulator run issues thousands of route requests.
7. **OpenStreetMap attribution on every map screen** — "© OpenStreetMap contributors", bottom-right and never
   covered by UI, as required by ODbL and screen C-06.
8. **Self-host before the paid pilot goes live**: the public services have no SLA and may be withdrawn for
   commercial use, so switching to self-hosted OSRM and tiles is a go-live requirement, not an option (§A3,
   task I02b, OQ-21).

## Amendment (2026-09-24): alignment with the OSMF usage policies
Checked against the official policies at `operations.osmfoundation.org/policies/nominatim` and
`/policies/tiles`. Two rules above were not compliant as written; this amendment replaces them.

### A1. Geocoding: do not use public Nominatim in the product
The Nominatim usage policy explicitly prohibits use by **vehicle tracking applications** — which is what this
platform is — and asks that no personal data be submitted. Employee home addresses are personal data. A
rate-limited, cached, backend-only integration does not make this permitted; the prohibition is categorical.

Therefore:
- **Phase 1 has no geocoding.** Employees, supervisors and admins set pickup, drop, home and office locations
  with **map pins plus free-text landmark**, which matches how people describe locations in NCR anyway.
- The backend keeps a `GeocodingProvider` interface with a **`none`** implementation (`GEOCODING_PROVIDER=none`,
  the default): forward/reverse geocoding calls return "unavailable", and no endpoint offers address search.
- `NOMINATIM_URL` is unset by default. A **self-hosted** Nominatim is the only permitted implementation and is
  an optional later task (**I02c**), not a Phase 1 deliverable.
- No address search box appears in any Phase 1 screen (`screens-by-role.md`).

### A2. Map tiles: rules for `tile.openstreetmap.org`
Public OSM tiles are raster PNGs served on donated capacity. The app must:
- Use a MapLibre **raster** style pointing at `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, with the URL
  read from `TILES_URL` — never hard-coded, so self-hosted tiles are a config change.
- Send a **distinct, stable `User-Agent`** on every tile request: `flex-platform/<version> (contact:
  <OSM_CONTACT_EMAIL>)`. Never the HTTP library or MapLibre default — a generic agent gets blocked.
- **Honour HTTP cache headers** and keep a local tile cache of **at least 7 days**.
- **No offline map download and no tile prefetching anywhere**, including the driver app. Only tiles for
  what is currently on screen may be fetched.
- Show **"© OpenStreetMap contributors" bottom-right, always visible** and never covered by sheets, cards or
  controls.

### A3. No SLA; self-hosting required before the paid pilot
The public OSM services are **best-effort, donated infrastructure with no SLA**, and access may be
throttled or **withdrawn for commercial use** — which a paid pilot is. Running a revenue-generating product on
them is therefore not an option:
- **Before the paid pilot goes live, switch to self-hosted OSRM and self-hosted tiles** (tasks I02b and the
  tile part of it). This is a requirement, not a review item; OQ-21 tracks the timing decision.
- Until then, availability incidents on the public servers are handled by the `approx` fallback (routing) and
  by a degraded map (tiles), never by raising the rate limit.

## Alternatives considered
- **Self-host from day one (ADR-0004 as written).** Correct end state, but blocks early development on map
  data preparation and a large dev machine. Deferred, not abandoned.
- **`approx` provider only until self-hosting.** No infrastructure at all, but ETAs would never be validated
  against real road routing during Phase 1, which is exactly what the pilot must demonstrate.
- **Public Nominatim with rate limiting and caching.** Rejected: prohibited for vehicle-tracking applications
  regardless of volume (§A1).
- **A free geocoding tier from another provider** (Photon, LocationIQ, Geoapify). Rejected for Phase 1: either
  paid beyond a small free tier (hard rule 7) or the same policy questions. Map pins cover the need.
- **Paid routing API for development.** Excluded by hard rule 7 and ADR-0004.

## Consequences
- Development and the simulator run with no map servers: `make up` is postgres + redis + mosquitto only.
- **No address search anywhere in Phase 1.** Employees pick locations on the map; saved places (home, office)
  are set once by the client admin, so the daily flow needs no typing. Accept that a first-time pin drop is
  slower than typing an address.
- Tiles are raster, not vector: no client-side styling or rotation-aware labels until tiles are self-hosted.
- The public services carry **no SLA** and may be withdrawn for commercial use, so the pilot timeline must
  include the self-hosting work (I02b) as a dependency, not an optional extra.
- **ETA accuracy is lower in `approx` mode** (straight line × 1.4, no road network). Responses and UI mark
  such ETAs as approximate; the accuracy targets in `non-functional.md` apply to `osrm` mode.
- Throughput is capped at 1 req/s per service while on public servers — acceptable for development and demos,
  not for a live pilot with 200 vehicles. This is the trigger for the switch to self-hosted OSRM.
- Public servers may be slow or briefly unavailable; the `approx` fallback keeps the platform working, which
  matches the existing degradation rule in `control-model.md` ("OSRM down → approximate ETAs").
- Attribution, `User-Agent` and rate limiting are contractual, not optional. A change that removes them
  breaks the OSM usage policy.
- The self-hosting runbook stays in `dev-environment.md` under "Optional: self-hosting" and is exercised by
  tasks I02b (OSRM + tiles, required before the paid pilot) and I02c (Nominatim, optional).
