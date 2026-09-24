# Tech stack (approved 24 Sep 2026)

Pin exact versions at project start in `backend/pyproject.toml`, `app/pubspec.yaml` and `infra/docker-compose.yml`, and record them in the table below. Use the latest stable release at that time.

Backend versions were pinned on 2026-09-24 (task B01). Blank cells are packages not installed yet; they get pinned by the task that introduces them.

## Backend
| Purpose | Choice | Pinned version |
|---|---|---|
| Language | Python 3.12 | `requires-python = ">=3.12"`; CI runs 3.12 |
| Web framework | FastAPI + Uvicorn | fastapi 0.141.1, uvicorn 0.53.0 |
| Validation | Pydantic v2 | pydantic 2.13.5, pydantic-settings 2.15.0 |
| ORM / DB access | SQLAlchemy 2.x (async) + asyncpg | sqlalchemy 2.0.54, asyncpg 0.31.0, greenlet 3.5.6 |
| Migrations | Alembic | alembic 1.20.0 |
| Geo | PostGIS, GeoAlchemy2, Shapely | |
| Background jobs | Celery + Redis broker (+ beat) | |
| MQTT client | aiomqtt (ingestor) | |
| Optimizer | Google OR-Tools | |
| ML (Phase 4) | scikit-learn, LightGBM, pandas | |
| Auth | PyJWT; OTP via SMS gateway adapter (pluggable; console adapter in dev) | |
| HTTP client | httpx | 0.28.1 (runtime: OSRM client) |
| Routing providers | `osrm` / `approx` / `cached` behind one interface, selected by `ROUTING_PROVIDER` (ADR-0010) | |
| Geocoding provider | `GeocodingProvider` interface; **`none` in Phase 1** (`GEOCODING_PROVIDER`), self-hosted Nominatim optional later | |
| Lint / format | ruff (lint + format) | 0.16.8 |
| Types | mypy (strict on `domain/`) | 2.3.1 (strict on `app.domain.*` and `app.core.*`) |
| Tests | pytest, pytest-asyncio, testcontainers (Postgres, Redis) | pytest 9.1.1, pytest-asyncio 1.4.0; testcontainers lands with B02 |

## App
| Purpose | Choice | Pinned version |
|---|---|---|
| Framework | Flutter (stable), Dart 3 | |
| State management | Riverpod | |
| Routing | go_router | |
| API client | Generated from `api-spec.yaml` (openapi-generator, dart-dio) | |
| Maps | maplibre_gl (MapLibre Native), **raster** style; tile URL from `TILES_URL` — public OSM raster tiles early, self-hosted later. ≥ 7-day tile cache, no prefetch, no offline download | |
| Location | geolocator + foreground service (flutter_foreground_task) | |
| MQTT | mqtt_client | |
| Push | firebase_messaging (FCM) behind a `PushService` interface | |
| Local storage | drift (SQLite) for offline queue; flutter_secure_storage for tokens | |
| i18n | Flutter intl (ARB files), English first | |
| Lint | very_good_analysis or flutter_lints (strict) | |
| Tests | flutter_test, mocktail, integration_test | |

## Infrastructure
| Purpose | Choice |
|---|---|
| Database | PostgreSQL 16 + PostGIS 3 |
| Cache / pubsub / broker | Redis 7 (client: redis-py 8.1.0) |
| MQTT broker | Eclipse Mosquitto 2 (EMQX if scale requires) |
| Routing | OSRM — public demo server (`router.project-osrm.org`) in early phases; self-hosted OSRM (MLD, car profile, Delhi NCR extract) later. URL from `OSRM_URL` |
| Routing fallback | `approx` provider: haversine × 1.4 road factor, time-of-day speed table, no network |
| Routing cache / rate limit | Redis: route + table cache (TTL from config) and a shared 1 req/s-per-service token bucket for public servers |
| Geocoding | **None in Phase 1** — map pins + landmark text. Public Nominatim is **not permitted** (OSMF policy: no vehicle-tracking applications, no personal data). Self-hosted Nominatim optional later (task I02c) |
| Map tiles | Public OpenStreetMap **raster** tiles (`tile.openstreetmap.org/{z}/{x}/{y}.png`) in early phases; Planetiler-generated OpenMapTiles-schema MBTiles + tileserver-gl later. URL from `TILES_URL` |
| Reverse proxy / TLS | Caddy |
| Containers | Docker + Docker Compose |
| Monitoring | Prometheus + Grafana; structured JSON logs |
| CI/CD | GitHub Actions |
| Push notifications | Firebase Cloud Messaging (free) or ntfy (self-hosted) |

Map services are chosen by configuration only (ADR-0010), never in code. While on the public servers:
- the backend sends an identifying `User-Agent` (`OSM_USER_AGENT` + `OSM_CONTACT_EMAIL`) and stays within 1
  request/second per service; over-limit requests fall back to `approx` and are flagged approximate;
- the app sends `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)` on tile requests — never the
  MapLibre or HTTP library default — honours cache headers with a ≥ 7-day tile cache, and never prefetches
  or downloads tiles for offline use;
- every map screen shows "© OpenStreetMap contributors" bottom-right, never hidden behind UI.

The public services are best-effort with **no SLA** and may be withdrawn for commercial use: self-hosted OSRM
and tiles are required before the paid pilot (ADR-0010 §A3, OQ-21).

## Simulator
Python 3.12, SimPy, httpx, aiomqtt, PyYAML, pandas (results), matplotlib (reports).
Uses the `approx` routing provider by default; it must never call the public OSM servers in bulk.

## Explicitly excluded
Google Maps / Mapbox / MapmyIndia paid APIs, WhatsApp Business API, proprietary routing or traffic APIs, paid background-geolocation SDKs.
