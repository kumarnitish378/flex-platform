# ADR-0024: Raster Tile Rendering and Parent-Tile Prefetching

## Context

Task A05 mandates rendering raster map tiles using the shared `AppMap` widget. ADR-0010 §A2 required complying with OpenStreetMap Foundation (OSMF) tile usage policies, which prohibit aggressive tile prefetching when querying public tile servers.

However, `maplibre_gl` 0.27.1 implements default parent-tile prefetching in native code behind its platform view. As implemented in I02b, self-hosted map tiles are served directly from our own infrastructure (`make up-maps` serving raster PNG tiles at `TILES_URL` configured via `--dart-define`).

## Decision

1. **Self-Hosted Map Tile Server**: All map instances in the Smart Cab app consume raster tiles from the configured `TILES_URL` (self-hosted tile server in production and staging, or local tile server during development).
2. **Tile Prefetching Permitted on Self-Hosted Tile Server**: Parent-tile prefetching performed by `maplibre_gl` is permitted when requesting tiles from our self-hosted tile infrastructure, as it improves zooming performance without impacting public OSM tile servers.
3. **Public Tile Policy Compliance**: If a public tile server URL is ever used in dev/testing, identifying `User-Agent` headers (`flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`) and OpenStreetMap attribution ("© OpenStreetMap contributors") are maintained as enforced by widget tests.

## Consequences

- Resolves OQ-35. `maplibre_gl` remains the primary map rendering engine for raster tiles in Phase 1 and vector tiles in future phases.
- Tile network requests are served from the self-hosted tile infrastructure (`http://10.0.2.2:8081/styles/basic/{z}/{x}/{y}.png`).
- Widget tests use `isTestMode: true` or fallback canvas for offline testing without native platform view dependencies.
