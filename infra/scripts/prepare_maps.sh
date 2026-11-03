#!/usr/bin/env bash
# Prepare self-hosted OSM map data for Delhi NCR (task I02b).
#
# **Why this exists.** Phase 1 runs on the public OSM servers, under their usage policies
# and inside a shared 1 request/second budget (ADR-0010). Those services are best-effort,
# have no SLA, and may be withdrawn for commercial use - so self-hosting routing and
# tiles is **required before the paid pilot** (ADR-0010 §A3, OQ-21). Nothing in the
# application changes when it happens: `OSRM_URL` and `TILES_URL` move, and that is all.
#
# **Everything runs in containers.** `osmium`, `osrm-backend` and Planetiler are each a
# `docker run`, so the only thing this needs on the host is Docker and disk. The
# "16 GB RAM, osmium-tool, Java 21" in dev-environment.md §1 is what the tools need, not
# what you must install.
#
# Usage:
#   infra/scripts/prepare_maps.sh all        download, crop, OSRM, tiles  (~1 hour)
#   infra/scripts/prepare_maps.sh download
#   infra/scripts/prepare_maps.sh crop
#   infra/scripts/prepare_maps.sh osrm
#   infra/scripts/prepare_maps.sh fonts
#   infra/scripts/prepare_maps.sh tiles
#   infra/scripts/prepare_maps.sh status     what is prepared and how old it is
#   infra/scripts/prepare_maps.sh clean      remove the intermediates, keep the download
#
# Then:
#   make up-maps
#   curl "http://localhost:5000/route/v1/driving/77.3218,28.5703;77.3910,28.5123"
#
# Re-run monthly to pick up new OSM data. `infra/maps/README.md` records the data date.

set -euo pipefail

# Two Git-Bash-on-Windows accommodations, both inert on Linux, which is where this
# actually runs.
#
# `dk` turns off MSYS path rewriting **for docker only**. Git Bash rewrites anything
# that looks like a POSIX path in an argument into a Windows path, so the container-side
# `/data` reaches docker as `C:/Program Files/Git/data`. Scoping it to docker matters:
# a blanket `export` breaks `curl -o` and `python3`, which are native Windows binaries
# here and need the rewriting.
#
# `host_path` then translates the one path that genuinely must be a Windows path - the
# host side of a bind mount, which docker sees after the rewriting is off.
# Both switches, because they cover different cases: MSYS2_ARG_CONV_EXCL handles plain
# path arguments, MSYS_NO_PATHCONV the `--flag=/path` form that Planetiler uses - which
# the first one does not, as a rewritten `--output=C:/Program Files/Git/tiles/...`
# demonstrated.
dk() { MSYS2_ARG_CONV_EXCL='*' MSYS_NO_PATHCONV=1 docker "$@"; }

host_path() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi
}

# `unzip` is not on a minimal Debian VM and `python3` is not on Git Bash, so try each
# rather than making one of them a prerequisite for a single archive.
unzip_into() {
  local archive="$1" target="$2"
  if command -v unzip >/dev/null 2>&1; then
    unzip -q -o "$archive" -d "$target"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m zipfile -e "$archive" "$target"
  elif command -v python >/dev/null 2>&1; then
    python -m zipfile -e "$archive" "$target"
  else
    die "need one of: unzip, python3, python - to unpack $(basename "$archive")"
  fi
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPS_DIR="${MAPS_DIR:-$ROOT/maps}"
DATA_DIR="$MAPS_DIR/data"
TILES_DIR="$MAPS_DIR/tiles"
FONTS_DIR="$MAPS_DIR/fonts"

# All of India, not a Geofabrik zone extract.
#
# The zone extracts look tempting - northern-zone is 214 MB against 1.7 GB - and the
# first version of this script used one. It is wrong for this product: **Delhi NCR
# straddles two zones.** Delhi, Gurgaon and Faridabad are in the northern zone;
# Noida and Ghaziabad are in Uttar Pradesh, which Geofabrik puts in the *central* zone.
# Cropping the northern zone to the NCR box produced a routing engine that answered
# every query, served Delhi correctly, and returned `NoRoute` for anything touching
# Noida - where half the pilot's offices are. `verify_coverage` below now fails on
# exactly that.
#
# The download is large and the crop is not, so the size costs one slow step a month
# and nothing downstream. Change it only together with NCR_BBOX and the anchors.
EXTRACT_URL="${EXTRACT_URL:-https://download.geofabrik.de/asia/india-latest.osm.pbf}"
EXTRACT_FILE="$DATA_DIR/$(basename "$EXTRACT_URL")"

# Delhi NCR, from dev-environment.md §8. west,south,east,north.
NCR_BBOX="${NCR_BBOX:-76.80,28.20,77.75,28.95}"
REGION="${REGION:-ncr}"

OSRM_IMAGE="${OSRM_IMAGE:-osrm/osrm-backend:v5.25.0}"
OSMIUM_IMAGE="${OSMIUM_IMAGE:-debian:bookworm-slim}"
PLANETILER_IMAGE="${PLANETILER_IMAGE:-ghcr.io/onthegomap/planetiler:latest}"
#: Docker volumes for Planetiler's downloads and its scratch space. Neither belongs
#: in the repository tree: the downloads are a cache worth keeping between runs, the
#: scratch is thrown away, and on a bind mount both are very slow to read back.
PLANETILER_CACHE="${PLANETILER_CACHE:-smartcab-planetiler-sources}"
PLANETILER_TMP="${PLANETILER_TMP:-smartcab-planetiler-tmp}"

# Glyph PBFs for the map labels. tileserver-gl rasterises text server-side, so without
# these every tile comes back correct and silent - roads and water, no street names.
FONTS_URL="${FONTS_URL:-https://github.com/openmaptiles/fonts/releases/download/v2.0/noto-sans.zip}"

log()  { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

require_docker() {
  command -v docker >/dev/null 2>&1 || die "docker is required; see dev-environment.md §1"
  dk info >/dev/null 2>&1 || die "the docker daemon is not running"
}

# `docker run` with the data directory mounted at /data, which every tool below uses.
in_data() {
  dk run --rm -v "$(host_path "$DATA_DIR"):/data" "$@"
}

# --- steps ------------------------------------------------------------------

download() {
  mkdir -p "$DATA_DIR"
  if [ -f "$EXTRACT_FILE" ]; then
    note "already downloaded: $(basename "$EXTRACT_FILE") ($(du -h "$EXTRACT_FILE" | cut -f1))"
    note "delete it to force a refresh"
    return
  fi
  log "downloading $(basename "$EXTRACT_FILE")"
  # -C - resumes: this is a few hundred MB over a connection that may not survive it.
  curl -fL --retry 3 -C - -o "$EXTRACT_FILE" "$EXTRACT_URL"
  note "$(du -h "$EXTRACT_FILE" | cut -f1)"
}

crop() {
  require_docker
  [ -f "$EXTRACT_FILE" ] || die "no extract; run '$0 download' first"
  local out="$DATA_DIR/${REGION}.osm.pbf"

  if [ -f "$out" ] && [ "$out" -nt "$EXTRACT_FILE" ]; then
    note "already cropped: $(basename "$out") ($(du -h "$out" | cut -f1))"
    return
  fi

  log "cropping to the NCR box ($NCR_BBOX)"
  note "this is what keeps the OSRM and Planetiler runs inside 16 GB"
  # osmium-tool has no official image worth trusting, and this runs once a month, so
  # installing it into a plain Debian container is cheaper than vetting a third party.
  in_data "$OSMIUM_IMAGE" bash -c "
    set -eu
    apt-get update -qq && apt-get install -y -qq --no-install-recommends osmium-tool >/dev/null
    osmium extract --bbox '$NCR_BBOX' --overwrite \
      -o /data/${REGION}.osm.pbf /data/$(basename "$EXTRACT_FILE")
  "
  note "$(du -h "$out" | cut -f1)"
  verify_coverage
}

#: Places the pilot actually serves, spread across the NCR so a source extract missing
#: a whole state cannot pass. `lon,lat|label`, one per line - lon,lat is OSRM's order
#: and the order used everywhere a coordinate is written in this repository's map
#: tooling, and the pipe keeps the spaces in the labels.
COVERAGE_ANCHORS="${COVERAGE_ANCHORS:-$(cat <<'ANCHORS'
77.2167,28.6315|Connaught Place (Delhi)
77.3260,28.5700|Sector 18 (Noida, UP)
77.0266,28.4595|Cyber City (Gurgaon, Haryana)
77.4538,28.6692|Indirapuram (Ghaziabad, UP)
ANCHORS
)}"

#: A 0.02-degree box is about 2 km. Anywhere in urban NCR has far more than this many
#: roads; a box with fewer is a hole in the data, not a quiet neighbourhood.
MIN_WAYS_PER_ANCHOR="${MIN_WAYS_PER_ANCHOR:-50}"

verify_coverage() {
  log "checking the crop covers the whole service area"
  note "a zone extract passes every other check and silently has no Noida in it"

  local failures=0
  while IFS='|' read -r coords label; do
    [ -n "$coords" ] || continue
    local lon="${coords%%,*}" lat="${coords##*,}"
    local box
    box="$(awk -v lon="$lon" -v lat="$lat" \
      'BEGIN{printf "%.4f,%.4f,%.4f,%.4f", lon-0.01, lat-0.01, lon+0.01, lat+0.01}')"

    local ways
    ways="$(in_data "$OSMIUM_IMAGE" bash -c '
      set -eu
      apt-get update -qq
      apt-get install -y -qq --no-install-recommends osmium-tool >/dev/null 2>&1
      osmium extract --bbox "$1" --overwrite -o /tmp/probe.osm.pbf "/data/$2.osm.pbf"
      osmium tags-filter --overwrite -o /tmp/roads.osm.pbf /tmp/probe.osm.pbf w/highway
      osmium fileinfo -e /tmp/roads.osm.pbf | awk "/Number of ways/ {print \$NF}"
    ' _ "$box" "$REGION" | tr -dc '0-9')"

    if [ "${ways:-0}" -lt "$MIN_WAYS_PER_ANCHOR" ]; then
      printf '   MISSING  %-34s %s roads in a 2 km box\n' "$label" "${ways:-0}"
      failures=$((failures + 1))
    else
      printf '   ok       %-34s %s roads\n' "$label" "$ways"
    fi
  done <<< "$COVERAGE_ANCHORS"

  if [ "$failures" -ne 0 ]; then
    printf '\n' >&2
    printf 'ERROR: %s of the service area has no road data.\n' "$failures" >&2
    printf '       The source extract does not cover the whole NCR. A Geofabrik zone\n' >&2
    printf '       extract will not: the NCR spans two of them. Use the default\n' >&2
    printf '       asia/india-latest.osm.pbf, delete %s.osm.pbf and re-run crop.\n' "$REGION" >&2
    exit 1
  fi
}

osrm() {
  require_docker
  local pbf="$DATA_DIR/${REGION}.osm.pbf"
  [ -f "$pbf" ] || die "no cropped extract; run '$0 crop' first"

  log "OSRM: extract (car profile)"
  in_data "$OSRM_IMAGE" osrm-extract -p /opt/car.lua "/data/${REGION}.osm.pbf"

  # MLD, not CH. CH gives faster queries but a customise step that is just as slow as
  # the first build, and the whole point of MLD here is that re-running `osrm-customize`
  # with learned speeds from `road_speed_profile` takes minutes rather than hours
  # (dev-environment.md §8, step 3).
  log "OSRM: partition"
  in_data "$OSRM_IMAGE" osrm-partition "/data/${REGION}.osrm"

  log "OSRM: customize"
  in_data "$OSRM_IMAGE" osrm-customize "/data/${REGION}.osrm"

  note "ready: /data/${REGION}.osrm (served by docker-compose.maps.yml)"
}

fonts() {
  if [ -d "$FONTS_DIR/Noto Sans Regular" ]; then
    note "fonts already present"
    return
  fi
  log "downloading map label fonts"
  mkdir -p "$FONTS_DIR"
  curl -fL --retry 3 --progress-bar -o "$FONTS_DIR/fonts.zip" "$FONTS_URL"
  unzip_into "$FONTS_DIR/fonts.zip" "$FONTS_DIR"
  rm -f "$FONTS_DIR/fonts.zip"
  note "$(find "$FONTS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l) font stacks"
}

tiles() {
  require_docker
  local pbf="$DATA_DIR/${REGION}.osm.pbf"
  [ -f "$pbf" ] || die "no cropped extract; run '$0 crop' first"
  mkdir -p "$TILES_DIR"

  log "Planetiler: building ${REGION}.mbtiles (OpenMapTiles schema)"
  note "the long one - half an hour or so for the NCR box"
  # One mount with a working directory, and **relative** paths in the arguments.
  # Planetiler takes its paths as `--flag=/path`, and that is the one form Git Bash
  # rewrites in spite of both MSYS_NO_PATHCONV and MSYS2_ARG_CONV_EXCL: it arrives as
  # `--output=C:/Program Files/Git/tiles/ncr.mbtiles` and Planetiler rejects it as an
  # illegal URI. A relative path has no leading slash, so nothing recognises it as a
  # path to rewrite - on any platform, which is why this is the version worth keeping.
  # Planetiler's downloads and its scratch space both go in named volumes rather than
  # the repository tree. Two reasons, and the second one is what makes this necessary
  # rather than tidy:
  #
  #  * They are not project data. The downloads (natural earth, water polygons, lake
  #    centrelines - about 1.1 GB) are a cache worth keeping between monthly rebuilds;
  #    `data/tmp` is scratch that is thrown away. Neither belongs in a working copy.
  #  * **Reading them back through a bind mount is pathologically slow.** Planetiler
  #    unzips a 680 MB natural-earth sqlite into `data/tmp` and then reads it; on a bind
  #    mount that ran at 0.1 CPU and 8% in eighteen minutes, turning a half-hour build
  #    into an overnight one. Only the final MBTiles has to land on the host.
  dk volume create "$PLANETILER_CACHE" >/dev/null
  dk volume create "$PLANETILER_TMP" >/dev/null
  dk run --rm -w /maps \
    -v "$(host_path "$MAPS_DIR"):/maps" \
    -v "$PLANETILER_CACHE:/maps/data/sources" \
    -v "$PLANETILER_TMP:/maps/data/tmp" \
    "$PLANETILER_IMAGE" \
    --osm-path="data/${REGION}.osm.pbf" \
    --output="tiles/${REGION}.mbtiles" \
    --force \
    --download \
    --minzoom=0 --maxzoom=14

  note "$(du -h "$TILES_DIR/${REGION}.mbtiles" | cut -f1)"
  note "tileserver-gl rasterises these to PNG; Phase 1 serves RASTER tiles (ADR-0010 A2)"
  record_date
}

record_date() {
  cat > "$MAPS_DIR/README.md" <<EOF
# Prepared map data

**Do not commit the data.** \`infra/maps/data/\` and \`infra/maps/tiles/\` are
git-ignored; this file records what was built and when, which is the thing worth keeping.

| | |
|---|---|
| Source extract | \`$(basename "$EXTRACT_URL")\` |
| Source URL | $EXTRACT_URL |
| Region | \`$REGION\`, bbox \`$NCR_BBOX\` |
| Prepared | $(date -u +%Y-%m-%dT%H:%M:%SZ) |
| OSRM image | \`$OSRM_IMAGE\`, MLD pipeline, car profile |
| Tiles | Planetiler, OpenMapTiles schema, z0-z14 |

Rebuild monthly: \`infra/scripts/prepare_maps.sh all\`, then \`make up-maps\`.

Routing data ages faster than it looks - a new flyover or a changed one-way is the
difference between an ETA that holds and one that does not.
EOF
  note "wrote $MAPS_DIR/README.md"
}

status() {
  printf 'extract : %s\n' "$([ -f "$EXTRACT_FILE" ] && du -h "$EXTRACT_FILE" | cut -f1 || echo 'not downloaded')"
  printf 'cropped : %s\n' "$([ -f "$DATA_DIR/${REGION}.osm.pbf" ] && du -h "$DATA_DIR/${REGION}.osm.pbf" | cut -f1 || echo 'not cropped')"
  printf 'osrm    : %s\n' "$([ -f "$DATA_DIR/${REGION}.osrm.mldgr" ] && echo 'prepared (mld)' || echo 'not prepared')"
  printf 'fonts   : %s
' "$([ -d "$FONTS_DIR/Noto Sans Regular" ] && echo 'present' || echo 'not downloaded')"
  printf 'tiles   : %s\n' "$([ -f "$TILES_DIR/${REGION}.mbtiles" ] && du -h "$TILES_DIR/${REGION}.mbtiles" | cut -f1 || echo 'not built')"
  [ -f "$MAPS_DIR/README.md" ] && grep -E '^\| Prepared' "$MAPS_DIR/README.md" || true
}

clean() {
  log "removing intermediates, keeping the download"
  find "$DATA_DIR" -name "${REGION}.osrm*" -delete
  rm -f "$DATA_DIR/${REGION}.osm.pbf"
  note "kept $(basename "$EXTRACT_FILE")"
  note "kept the Planetiler source cache ($PLANETILER_CACHE); 'docker volume rm' it to refetch"
  dk volume rm "$PLANETILER_TMP" >/dev/null 2>&1 || true
}

case "${1:-all}" in
  all)      download; crop; osrm; fonts; tiles ;;
  download) download ;;
  crop)     crop ;;
  osrm)     osrm; record_date ;;
  fonts)    fonts ;;
  tiles)    fonts; tiles ;;
  status)   status ;;
  clean)    clean ;;
  *)        die "unknown step: $1 (all | download | crop | osrm | fonts | tiles | status | clean)" ;;
esac
