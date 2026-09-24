# infra

Docker Compose and service configuration.

- `docker-compose.yml` — core services only: postgres (PostGIS), redis, mosquitto.
- `docker-compose.maps.yml` — OPTIONAL self-hosted map services (osrm, tileserver, nominatim).
  Not needed for development: early phases use the public OSM servers (ADR-0010).
- `mosquitto/` — broker config and ACLs.
- `data/`, `tiles/` — map data, git-ignored, only used when self-hosting.

See `docs/05-engineering/dev-environment.md` (§2 core, §8 optional self-hosting).
