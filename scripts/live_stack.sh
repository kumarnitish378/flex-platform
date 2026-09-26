#!/usr/bin/env bash
# Bring up everything a closed-loop scenario needs, and wait until it is actually ready.
#
# One script for CI and for a developer reproducing a CI failure, because two versions of
# "start the stack" drift and the one that drifts is always the one you are not looking
# at. Postgres and Redis come from the workflow's `services:` block (or `make up`
# locally); this starts the pieces those cannot: the broker, the migrations, the API and
# the GPS ingestor.
#
# Usage:  scripts/live_stack.sh up | down
# Env:    DATABASE_URL, REDIS_URL, MQTT_HOST, MQTT_PORT, API_PORT, LOG_DIR

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8000}"
MQTT_HOST="${MQTT_HOST:-localhost}"
MQTT_PORT="${MQTT_PORT:-1883}"
LOG_DIR="${LOG_DIR:-/tmp/live-stack}"
PID_DIR="$LOG_DIR/pids"
BROKER_NAME="smartcab-ci-mosquitto"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://smartcab:smartcab@localhost:5432/smartcab}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export MQTT_HOST MQTT_PORT

# APP_ENV=sim is what enables /simctl/*, and ADR-0008 makes that impossible anywhere
# else. A scenario cannot seed a world without it.
export APP_ENV=sim
export SIMCTL_ENABLED=true
# ADR-0010 rule 6: CI must never call the public OSM servers.
export ROUTING_PROVIDER=approx
export GEOCODING_PROVIDER=none
# Not a secret: this process is thrown away with the job, and the value never leaves it.
export JWT_SECRET="${JWT_SECRET:-ci-only-ephemeral-secret-0123456789ab}"

start_broker() {
  # Anonymous access, because the broker is reachable only from this job and handing CI
  # a password file buys nothing. The dev broker in infra/ requires auth; production
  # requires auth and TLS.
  if docker ps --format '{{.Names}}' | grep -qx "$BROKER_NAME"; then
    echo "broker already running"
    return
  fi
  mkdir -p "$LOG_DIR/mosquitto"
  cat > "$LOG_DIR/mosquitto/mosquitto.conf" <<'CONF'
listener 1883
allow_anonymous true
CONF
  docker run -d --rm --name "$BROKER_NAME" \
    -p "${MQTT_PORT}:1883" \
    -v "$LOG_DIR/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro" \
    eclipse-mosquitto:2 >/dev/null
  echo "broker started"
}

wait_for_broker() {
  for _ in $(seq 1 30); do
    if (exec 3<>"/dev/tcp/${MQTT_HOST}/${MQTT_PORT}") 2>/dev/null; then
      exec 3>&- 2>/dev/null || true
      echo "broker ready"
      return
    fi
    sleep 1
  done
  echo "::error::the MQTT broker never accepted a connection" >&2
  exit 1
}

migrate() {
  (cd "$ROOT/backend" && alembic upgrade head)
  echo "migrations applied"
}

start_api() {
  mkdir -p "$PID_DIR"
  (cd "$ROOT/backend" && nohup python -m uvicorn app.main:create_app --factory \
    --port "$API_PORT" --log-level warning > "$LOG_DIR/api.log" 2>&1 & echo $! > "$PID_DIR/api")
  (cd "$ROOT/backend" && nohup python -m app.ingestor > "$LOG_DIR/ingestor.log" 2>&1 \
    & echo $! > "$PID_DIR/ingestor")
  echo "api and ingestor starting"
}

wait_for_api() {
  for _ in $(seq 1 60); do
    if curl -fsS "http://localhost:${API_PORT}/health/live" >/dev/null 2>&1; then
      echo "api ready"
      return
    fi
    sleep 1
  done
  echo "::error::the API never became healthy" >&2
  tail -50 "$LOG_DIR/api.log" >&2 || true
  exit 1
}

# The ingestor is not optional: without it no GPS reaches the database, so no vehicle has
# a known position, so dispatch offers no candidates and every scenario reports a fleet
# that never moved. Failing here is far clearer than that.
check_ingestor() {
  local pid
  pid="$(cat "$PID_DIR/ingestor" 2>/dev/null || echo)"
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    echo "::error::the GPS ingestor is not running; scenarios would report a motionless fleet" >&2
    tail -50 "$LOG_DIR/ingestor.log" >&2 || true
    exit 1
  fi
  echo "ingestor running"
}

case "${1:-up}" in
  up)
    mkdir -p "$LOG_DIR"
    start_broker
    wait_for_broker
    migrate
    start_api
    wait_for_api
    sleep 3
    check_ingestor
    echo "stack up on http://localhost:${API_PORT}"
    ;;
  down)
    for name in api ingestor; do
      pid="$(cat "$PID_DIR/$name" 2>/dev/null || echo)"
      [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    done
    docker rm -f "$BROKER_NAME" >/dev/null 2>&1 || true
    echo "stack down"
    ;;
  *)
    echo "usage: $0 up|down" >&2
    exit 2
    ;;
esac
