# ADR-0004: OpenStreetMap stack, self-hosted; no paid map APIs

- Status: accepted, **amended by ADR-0010**
- Date: 2026-09-24

> **Amended 2026-09-24 by [ADR-0010](0010-public-osm-servers-early-phases.md).** The OSM-only, no-paid-API
> decision below stands. What changed: *self-hosted* is no longer required in development and the early
> phases — the public OSM servers are used first, and self-hosting is an upgrade path switched by config
> (`OSRM_URL`, `NOMINATIM_URL`, `TILES_URL`) only.

## Context
Cost control and independence from per-request pricing.

## Decision
- Map data: OpenStreetMap (Delhi NCR extract first).
- Routing, ETA, distance matrices: OSRM (MLD, car profile), self-hosted.
- Geocoding: Nominatim, self-hosted.
- Tiles: vector tiles generated with Planetiler (OpenMapTiles schema), served by tileserver-gl; rendered with MapLibre.

## Alternatives considered
Google Maps Platform, Mapbox, MapmyIndia: better traffic and address data, but paid and vendor-locked.

## Consequences
- **No live traffic.** ETAs start from OSM speeds + time-of-day factors; accuracy improves by learning speeds from our own GPS (road_speed_profile → OSRM segment speed updates).
- Indian address geocoding is weak; employees use map pins + landmarks (already their habit).
- ODbL attribution must be shown on all maps.
- Map servers need RAM and monthly data refresh.
