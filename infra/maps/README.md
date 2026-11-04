# Prepared map data

**Do not commit the data.** `infra/maps/data/` and `infra/maps/tiles/` are
git-ignored; this file records what was built and when, which is the thing worth keeping.

| | |
|---|---|
| Source extract | `india-latest.osm.pbf` |
| Source URL | https://download.geofabrik.de/asia/india-latest.osm.pbf |
| Region | `ncr`, bbox `76.80,28.20,77.75,28.95` |
| Prepared | 2026-10-15T04:21:25Z |
| OSRM image | `osrm/osrm-backend:v5.25.0`, MLD pipeline, car profile |
| Tiles | Planetiler, OpenMapTiles schema, z0-z14 |

Rebuild monthly: `infra/scripts/prepare_maps.sh all`, then `make up-maps`.

Routing data ages faster than it looks - a new flyover or a changed one-way is the
difference between an ETA that holds and one that does not.
