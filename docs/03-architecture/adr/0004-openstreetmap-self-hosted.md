# ADR-0004: OpenStreetMap stack, self-hosted; no paid map APIs

- Status: accepted
- Date: 2026-09-24

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
