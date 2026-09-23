# ADR-0007: PostgreSQL + PostGIS as the single database

- Status: accepted
- Date: 2026-09-24

## Decision
PostgreSQL 16 with PostGIS for all relational and geospatial data; Redis only for ephemeral live state, pub/sub and the Celery broker.

## Consequences
- Zones, nearest-vehicle and polygon queries use PostGIS indexes.
- `location_ping` is partitioned monthly with 90-day retention.
