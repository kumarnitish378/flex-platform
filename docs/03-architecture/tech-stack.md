# Tech stack (approved 24 Sep 2026)

Pin exact versions at project start in `backend/pyproject.toml`, `app/pubspec.yaml` and `infra/docker-compose.yml`, and record them in the table below. Use the latest stable release at that time.

## Backend
| Purpose | Choice | Pinned version |
|---|---|---|
| Language | Python 3.12 | |
| Web framework | FastAPI + Uvicorn | |
| Validation | Pydantic v2 | |
| ORM / DB access | SQLAlchemy 2.x (async) + asyncpg | |
| Migrations | Alembic | |
| Geo | PostGIS, GeoAlchemy2, Shapely | |
| Background jobs | Celery + Redis broker (+ beat) | |
| MQTT client | aiomqtt (ingestor) | |
| Optimizer | Google OR-Tools | |
| ML (Phase 4) | scikit-learn, LightGBM, pandas | |
| Auth | PyJWT; OTP via SMS gateway adapter (pluggable; console adapter in dev) | |
| HTTP client | httpx | |
| Lint / format | ruff (lint + format) | |
| Types | mypy (strict on `domain/`) | |
| Tests | pytest, pytest-asyncio, testcontainers (Postgres, Redis) | |

## App
| Purpose | Choice | Pinned version |
|---|---|---|
| Framework | Flutter (stable), Dart 3 | |
| State management | Riverpod | |
| Routing | go_router | |
| API client | Generated from `api-spec.yaml` (openapi-generator, dart-dio) | |
| Maps | maplibre_gl (MapLibre Native) with self-hosted vector tiles | |
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
| Cache / pubsub / broker | Redis 7 |
| MQTT broker | Eclipse Mosquitto 2 (EMQX if scale requires) |
| Routing | OSRM (MLD algorithm, car profile), Delhi NCR extract |
| Geocoding | Nominatim (self-hosted) |
| Map tiles | Planetiler-generated OpenMapTiles-schema MBTiles + tileserver-gl |
| Reverse proxy / TLS | Caddy |
| Containers | Docker + Docker Compose |
| Monitoring | Prometheus + Grafana; structured JSON logs |
| CI/CD | GitHub Actions |
| Push notifications | Firebase Cloud Messaging (free) or ntfy (self-hosted) |

## Simulator
Python 3.12, SimPy, httpx, aiomqtt, PyYAML, pandas (results), matplotlib (reports).

## Explicitly excluded
Google Maps / Mapbox / MapmyIndia paid APIs, WhatsApp Business API, proprietary routing or traffic APIs, paid background-geolocation SDKs.
