#!/usr/bin/env bash
# Container healthcheck for the self-hosted OSRM (task I02b).
#
# **Why a script and not a one-line `test:` in the compose file.** Two reasons, both
# found the hard way:
#
# 1. The `osrm/osrm-backend` image has **no HTTP client at all** - no curl, no wget, no
#    nc, no python. A curl-based healthcheck looks right and leaves the container
#    permanently `unhealthy` with "curl: not found" buried in the healthcheck log. What
#    it does have is bash, so the request goes over `/dev/tcp`.
# 2. An HTTP request needs CRLF line endings, and a `\r\n` written inline in YAML
#    becomes a real newline before docker ever sees it, which breaks the request. In a
#    file the bytes are the bytes.
#
# It asks for a **real route across the NCR**, not a TCP connect: osrm-routed accepts
# the socket long before the graph is loaded, so a connect-only check reports healthy
# while every route fails - and dispatch would then be pointed at a server that cannot
# answer.

set -uo pipefail

HOST="${OSRM_HEALTH_HOST:-127.0.0.1}"
PORT="${OSRM_HEALTH_PORT:-5000}"
# Connaught Place (Delhi) to Sector 18 (Noida, UP): deliberately across the state line,
# because the extract that only covered Delhi routed within Delhi perfectly well.
PATH_AND_QUERY="/route/v1/driving/77.2167,28.6315;77.3260,28.5700?overview=false"

exec 3<>"/dev/tcp/${HOST}/${PORT}" || {
  echo "osrm: nothing listening on ${HOST}:${PORT}" >&2
  exit 1
}

printf 'GET %s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n\r\n' "$PATH_AND_QUERY" "$HOST" >&3

if cat <&3 | grep -q '"code":"Ok"'; then
  exit 0
fi

echo "osrm: answered, but not with a route (graph still loading, or no data here)" >&2
exit 1
