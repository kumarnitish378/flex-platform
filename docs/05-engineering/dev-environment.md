# Development environment

## 1. Prerequisites
- Linux or macOS (Windows via WSL2), 8 GB RAM is enough for the default setup (no map servers).
- Docker + Docker Compose v2
- Python 3.12 + `uv` (or pip/venv)
- Flutter stable SDK + Android Studio / Android SDK; a physical Android phone for GPS tests
- `make`, `git`
- Internet access for the public OSM services (see §3) — or, for offline work, `ROUTING_PROVIDER=approx`.
- Only for self-hosting (§8, optional): 16 GB RAM, `osmium-tool`, Java 21 (Planetiler).

## 2. Services (infra/docker-compose.yml)
| Service | Image (suggested) | Port | Notes |
|---|---|---|---|
| postgres | `postgis/postgis:16-3.4` | 5432 | DB `smartcab` |
| redis | `redis:7` | 6379 | |
| mosquitto | `eclipse-mosquitto:2` | 1883 (dev), 8883 (TLS) | config in `infra/mosquitto/` |
| caddy | `caddy:2` | 80/443 | staging/prod only |
| prometheus, grafana | official images | 9090, 3000 | optional in dev |
Verify image tags at setup time and pin them.

Map services are **not** part of the default compose (ADR-0010) — `make up` starts postgres, redis and
mosquitto only. Routing and tiles come from the public OSM servers via `OSRM_URL` and `TILES_URL`; there is
**no geocoding service** (`GEOCODING_PROVIDER=none`). To self-host them instead, see §8.

## 3. Map services (default: public OSM servers)
No setup and no map data download. Defaults in `.env.example`:
```
ROUTING_PROVIDER=cached_osrm
GEOCODING_PROVIDER=none
OSRM_URL=https://router.project-osrm.org
TILES_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png
OSM_USER_AGENT=flex-platform/0.1
OSM_CONTACT_EMAIL=you@example.com
# NOMINATIM_URL is intentionally unset — public Nominatim must never be used (ADR-0010 §A1)
```
Smoke test:
```
curl "$OSRM_URL/route/v1/driving/77.3218,28.5703;77.3910,28.5123?overview=false"
```

**Usage policy — not optional** (ADR-0010, OSMF policies for Nominatim and tiles):
- Set `OSM_CONTACT_EMAIL` to a real address before making any request; requests without an identifying
  `User-Agent` may be blocked.
- The backend enforces a shared 1 request/second per service; do not disable it or run load tests against
  the public servers.
- **Never point `NOMINATIM_URL` at `nominatim.openstreetmap.org`.** Its policy forbids vehicle-tracking
  applications and personal data. Phase 1 has no geocoding at all; a self-hosted instance is the only option
  later (§8, task I02c).
- Tiles: raster only, app-side `User-Agent` `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`, ≥ 7-day
  cache, **no prefetching and no offline download**.
- Bulk work (simulator, optimizer, `make sim-full`) must run with `ROUTING_PROVIDER=approx`.
- Maps must show "© OpenStreetMap contributors" bottom-right, never covered.
- These services are best-effort with **no SLA** and may be withdrawn for commercial use — self-hosted OSRM
  and tiles are required before the paid pilot (OQ-21).

Offline or rate-limited? Set `ROUTING_PROVIDER=approx` — no network calls, ETAs from haversine × 1.4 and the
time-of-day speed table, flagged approximate.

## 4. Environment variables (`.env`, never committed; `.env.example` committed)
| Variable | Example | Used by |
|---|---|---|
| `APP_ENV` | `dev` / `sim` / `staging` / `prod` | backend |
| `DATABASE_URL` | `postgresql+asyncpg://smartcab:smartcab@localhost:5432/smartcab` | backend |
| `REDIS_URL` | `redis://localhost:6379/0` | backend, workers |
| `MQTT_HOST` / `MQTT_PORT` | `localhost` / `1883` | ingestor, app config |
| `MQTT_INGESTOR_USER` / `_PASSWORD` | | ingestor |
| `ROUTING_PROVIDER` | `cached_osrm` (dev/staging/prod) / `approx` (simulator, offline) | backend, simulator |
| `GEOCODING_PROVIDER` | `none` (default, Phase 1) / `nominatim` (self-hosted only) | backend |
| `OSRM_URL` | `https://router.project-osrm.org` (public) or `http://localhost:5000` (self-hosted) | backend, simulator |
| `NOMINATIM_URL` | unset in Phase 1; `http://localhost:8080` only if self-hosted (never the public server) | backend |
| `TILES_URL` | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` or `http://localhost:8081` | app |
| `OSM_USER_AGENT` | `flex-platform/0.1` (app tiles send `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`) | backend, simulator, app |
| `OSM_CONTACT_EMAIL` | real contact address (required by OSM usage policy) | backend, simulator |
| `ROUTING_CACHE_TTL_SECONDS` | `900` | backend |
| `OSM_RATE_LIMIT_PER_SECOND` | `1` (do not raise for public servers) | backend |
| `JWT_SECRET` | random 64 bytes | backend |
| `ACCESS_TOKEN_TTL_SECONDS` | `900` | backend |
| `REFRESH_TOKEN_TTL_DAYS` | `30` | backend |
| `OTP_PROVIDER` | `console` (dev) / `<sms-provider>` | backend |
| `PUSH_PROVIDER` | `fcm` / `ntfy` / `log` | backend |
| `FCM_CREDENTIALS_FILE` | path | backend |
| `SIMCTL_ENABLED` | `true` only when `APP_ENV=sim` | backend |

In `dev`, `OTP_PROVIDER=console` prints OTPs to the log, and `PUSH_PROVIDER=log` logs notifications.
Map URLs are read from config everywhere — never hard-code them in backend, app or simulator code.

## 5. Make targets
| Target | Does |
|---|---|
| `make up` / `make down` | Start/stop infra containers |
| `make migrate` | `alembic upgrade head` |
| `make seed` | Load dev fixture (1 operator, 1 client, offices, employees, vehicles, users for each role) |
| `make backend-dev` | Uvicorn with reload |
| `make ingestor` | Run MQTT ingestor |
| `make worker` / `make beat` | Celery worker / scheduler |
| `make test` | Backend unit + integration + contract |
| `make lint` | ruff + mypy |
| `make api-client` | Regenerate Dart client into `app/lib/data/api/` |
| `make sim-quick` / `make sim-full` | Simulator suites (starts backend with `APP_ENV=sim`, `ROUTING_PROVIDER=approx`) |
| `make maps` | Optional (self-hosting only): run `prepare_maps.sh` — see §8 |

## 6. Dev seed users (after `make seed`)
One phone number per role (e.g. `+910000000001` operator_admin … `+910000000006` employee); OTP appears in the backend console.

## 7. Running the app against local backend
- Android emulator reaches host at `10.0.2.2`; a physical phone needs the machine's LAN IP.
- Flavors / `--dart-define`: `API_BASE_URL`, `MQTT_HOST`, `TILES_URL`, `APP_ENV`.

## 8. Optional: self-hosting the map services
Not needed for development. OSRM + tiles (task I02b) are **required before the paid pilot** — the public
services have no SLA and may be withdrawn for commercial use (OQ-21). Nominatim (task I02c) is optional and
only worth doing if address search turns out to be needed; Phase 1 ships without geocoding.
Requires ~16 GB RAM, `osmium-tool` and Java 21. Nothing in the code changes — only the URLs.

Extra compose services (`infra/docker-compose.maps.yml`, started with `make up-maps`):

| Service | Image (suggested) | Port | Task | Notes |
|---|---|---|---|---|
| osrm | `osrm/osrm-backend` | 5000 | I02b | serves prepared NCR data |
| tileserver | `maptiler/tileserver-gl` | 8081 | I02b | serves MBTiles + style |
| nominatim | `mediagis/nominatim` | 8080 | I02c (optional) | imports NCR extract on first start (slow) |

Map data preparation (one-time, then monthly):
1. Download India extract from Geofabrik: `india-latest.osm.pbf` (northern-zone extract if available is smaller).
2. Crop to Delhi NCR bounding box to save RAM:
   ```
   osmium extract -b 76.80,28.20,77.75,28.95 india-latest.osm.pbf -o ncr.osm.pbf
   ```
3. OSRM (MLD pipeline, car profile):
   ```
   docker run -t -v $PWD/data:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/ncr.osm.pbf
   docker run -t -v $PWD/data:/data osrm/osrm-backend osrm-partition /data/ncr.osrm
   docker run -t -v $PWD/data:/data osrm/osrm-backend osrm-customize /data/ncr.osrm
   ```
   Served by compose with `osrm-routed --algorithm mld /data/ncr.osrm`.
   Later (speed learning): re-run `osrm-customize` with `--segment-speed-file` generated from `road_speed_profile`.
4. Nominatim: mount `ncr.osm.pbf` and let the container import it (first start can take a while).
5. Tiles: run Planetiler for the NCR area to produce `ncr.mbtiles` (OpenMapTiles schema), place in `infra/tiles/`, with an OpenMapTiles-compatible style JSON.
6. Script all steps in `infra/scripts/prepare_maps.sh` and document the data date in `infra/tiles/README.md`.

Then repoint the URLs (and nothing else):
```
OSRM_URL=http://localhost:5000
TILES_URL=http://localhost:8081
# only with task I02c:
GEOCODING_PROVIDER=nominatim
NOMINATIM_URL=http://localhost:8080
```
The rate limiter and cache still apply but can be relaxed for your own servers
(`OSM_RATE_LIMIT_PER_SECOND`).
