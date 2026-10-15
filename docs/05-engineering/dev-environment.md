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
| caddy | `caddy:2-alpine` | 80/443 | staging/prod only (`docker-compose.staging.yml`) |
| prometheus, grafana | `prom/prometheus`, `grafana/grafana` | 9090, 3000 | staging/prod; not published, reached through Grafana |
| loki, promtail | `grafana/loki`, `grafana/promtail` | 3100 | staging/prod; log shipping |
Verify image tags at setup time and pin them.

The staging and production stack is a **separate, standalone** compose file -
`infra/docker-compose.staging.yml`, started with `make staging-up`. It is not an overlay
on the development one, because that one publishes Postgres, Redis and the broker on the
host so a developer can reach them, and inheriting those would put the database on the
public internet. The full runbook is `deployment.md`.

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
| `OSM_REQUEST_TIMEOUT_SECONDS` | `5` | backend |
| `JWT_SECRET` | random 64 bytes | backend |
| `ACCESS_TOKEN_TTL_SECONDS` | `900` | backend |
| `REFRESH_TOKEN_TTL_DAYS` | `30` | backend |
| `OTP_PROVIDER` | `console` (dev) / `<sms-provider>` | backend |
| `PUSH_PROVIDER` | `fcm` / `ntfy` / `log` | backend |
| `FCM_CREDENTIALS_FILE` | path | backend |
| `SIMCTL_ENABLED` | `true` only when `APP_ENV=sim` | backend |
| `METRICS_PORT` | `0` (off) in dev; `9101` ingestor, `9102` worker in staging | ingestor, Celery worker |
| `SITE_ADDRESS` / `MONITORING_ADDRESS` | staging/prod only: the API and Grafana hostnames | Caddy |
| `ACME_EMAIL` | staging/prod only: where Let's Encrypt sends expiry warnings | Caddy |
| `GRAFANA_ADMIN_PASSWORD` | staging/prod only | Grafana |

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
| `make up-maps` | Start the self-hosted osrm + tileserver containers (needs `make maps` first) |
| `make staging-up` / `staging-down` | Start/stop the staging stack on the VM — see `deployment.md` |
| `make staging-ps` / `staging-logs` | What is running; follow the application logs |
| `make staging-mqtt-cert` | Re-publish Caddy's certificate to the broker after a renewal |
| `make backup` / `backup-list` | Take a database dump now; list what exists |
| `make backup-verify` | Restore a dump into a scratch database and compare row counts (monthly) |

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

Map data preparation is **one command**, and every tool it needs runs in a container —
the "osmium-tool and Java 21" above is what the tools need, not what you must install:

```
infra/scripts/prepare_maps.sh all      # ~1 hour: download, crop, OSRM, fonts, tiles
infra/scripts/prepare_maps.sh status   # what is prepared and how old it is
make up-maps
```

What it does, and why:

1. **Download** the Geofabrik *northern-zone* India extract (~214 MB) rather than all of
   India — a tenth of the size and it contains the whole NCR. Resumable.
2. **Crop** to the NCR box `76.80,28.20,77.75,28.95` with `osmium` (~35 MB). This is what
   keeps the OSRM and Planetiler runs inside 16 GB.
3. **OSRM**, MLD pipeline, car profile. MLD rather than CH because re-running
   `osrm-customize` with `--segment-speed-file` from `road_speed_profile` then takes
   minutes rather than hours — which is how learned speeds reach routing.
4. **Fonts**: the OpenMapTiles Noto Sans glyph PBFs. tileserver-gl rasterises text
   server-side, so without them every tile comes back correct and silent — roads and
   water, no street names.
5. **Tiles**: Planetiler produces `ncr.mbtiles` in the OpenMapTiles schema, and
   `tileserver-gl` (not `-light`) rasterises it to PNG, because Phase 1 serves **raster**
   tiles (ADR-0010 §A2). The vector tiles stay available for when MapLibre takes over.
6. The data date is recorded in `infra/maps/README.md`. The prepared data itself is
   git-ignored. **Rebuild monthly**: routing data ages faster than it looks — a new
   flyover or a changed one-way is the difference between an ETA that holds and one that
   does not.

Nominatim is **not** part of this. Phase 1 ships no geocoding; self-hosting it is the
separate, optional task I02c.

Then repoint the URLs (and nothing else):
```
OSRM_URL=http://localhost:5000        # http://osrm:5000 from another container
TILES_URL=http://localhost:8081/styles/basic/{z}/{x}/{y}.png
OSM_RATE_LIMIT_PER_SECOND=50          # your own server; the 1/s budget was theirs
# only with task I02c:
GEOCODING_PROVIDER=nominatim
NOMINATIM_URL=http://localhost:8080
```
No application code changes — that is the whole point of the provider interface from I02.
The rate limiter drops away on its own (`build_rate_limiter` only limits public hosts),
the cache still applies, and `/health/ready` starts **actually probing** the routing
server, which it refuses to do against a public one.
