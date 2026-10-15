#!/usr/bin/env bash
# Container healthcheck for the self-hosted tile server (task I02b).
#
# **It fetches a real tile, not `/health`.** tileserver-gl answers `/health` as soon as
# the process is up, including when the MBTiles failed to open or the style points at a
# source that is not there - and then every tile comes back as a valid PNG of the
# background colour. That exact failure happened while I02b was being built: four tiles
# over four different cities all returned 200 image/png and all were byte-identical at
# 1831 bytes, because the coordinates missed the data. A healthy tile over urban NCR is
# tens of kilobytes; a blank one is under two.
#
# Spoken through node, which is the server's own runtime and therefore always present -
# this image has no curl and no wget, the same trap as `osrm/osrm-backend`.

set -uo pipefail

HOST="${TILES_HEALTH_HOST:-127.0.0.1}"
PORT="${TILES_HEALTH_PORT:-8080}"
STYLE="${TILES_HEALTH_STYLE:-basic}"
# z13 over Sector 18, Noida: dense enough that a real tile is never small, and on the
# Uttar Pradesh side of the NCR, where a source extract covering only Delhi would be
# empty.
TILE="${TILES_HEALTH_TILE:-13/5855/3417}"
MIN_BYTES="${TILES_HEALTH_MIN_BYTES:-5000}"

node -e '
const [host, port, style, tile, minBytes] = process.argv.slice(1);
const url = `http://${host}:${port}/styles/${style}/${tile}.png`;
require("http").get(url, (res) => {
  if (res.statusCode !== 200) {
    console.error(`tiles: ${url} -> HTTP ${res.statusCode}`);
    process.exit(1);
  }
  let size = 0;
  res.on("data", (chunk) => { size += chunk.length; });
  res.on("end", () => {
    if (size < Number(minBytes)) {
      console.error(
        `tiles: ${url} returned ${size} bytes; under ${minBytes} means a blank tile - ` +
        "the MBTiles or the style source is not loading"
      );
      process.exit(1);
    }
    process.exit(0);
  });
}).on("error", (err) => {
  console.error(`tiles: ${url} unreachable: ${err.message}`);
  process.exit(1);
});
' "$HOST" "$PORT" "$STYLE" "$TILE" "$MIN_BYTES"
