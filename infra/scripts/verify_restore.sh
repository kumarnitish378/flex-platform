#!/usr/bin/env bash
# Prove the backups can actually be restored (task R01).
#
# `non-functional.md`: "restore tested monthly". A monthly test that depends on someone
# remembering a sequence of commands is a monthly test that stops happening, so it is
# one command: `make backup-verify`.
#
# What it does, end to end:
#   1. takes a fresh dump of the live database through `backup.sh once`;
#   2. restores it into a scratch database that is never the live one;
#   3. compares row counts for the tables that would hurt most to lose;
#   4. drops the scratch database.
#
# It touches nothing live - `backup.sh restore` refuses the live database without an
# explicit CONFIRM_LIVE_RESTORE, and this script never sets that.
#
# Usage:
#   infra/scripts/verify_restore.sh                      # against the dev compose
#   COMPOSE_FILE=infra/docker-compose.staging.yml \
#   PG_SERVICE=postgres infra/scripts/verify_restore.sh  # against staging, on the VM

set -euo pipefail

# Git Bash on Windows rewrites anything that looks like a POSIX path in an argument
# into a Windows path before the process sees it, so `/opt/backup/backup.sh` reaches
# docker as `C:/Program Files/Git/opt/backup/backup.sh`. Exempt the container-side
# paths only - a blanket exemption would also stop the compose file's own path being
# translated, which is the one that does need it. Means nothing on Linux, which is
# where this actually runs.
export MSYS2_ARG_CONV_EXCL='/opt/;/tmp/'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT/docker-compose.yml}"
PG_SERVICE="${PG_SERVICE:-postgres}"
PGUSER="${POSTGRES_USER:-smartcab}"
PGDATABASE="${POSTGRES_DB:-smartcab}"
SCRATCH="${PGDATABASE}_restore_check"

#: The tables whose loss would end the pilot. Checked by row count on both sides,
#: because a restore that produces the right *schema* and no rows passes every check
#: that only counts tables.
TABLES=(operator client office employee vehicle driver ride_request trip location_ping)

compose() { docker compose -f "$COMPOSE_FILE" "$@"; }

in_pg() {
  # PGUSER too, not only PGPASSWORD: `docker compose exec` runs as root inside the
  # container, and libpq defaults the role to the OS user, so `pg_dump` asks for a
  # role named `root` and is refused.
  compose exec -T     -e PGUSER="$PGUSER"     -e PGPASSWORD="${POSTGRES_PASSWORD:-smartcab}"     "$PG_SERVICE" "$@"
}

counts() {
  local db="$1" table sql=""
  for table in "${TABLES[@]}"; do
    sql+="SELECT '${table}=' || count(*) FROM ${table} UNION ALL "
  done
  in_pg psql -U "$PGUSER" -d "$db" -tA -c "${sql%UNION ALL } ORDER BY 1"
}

cleanup() {
  in_pg psql -U "$PGUSER" -d postgres -q -c "DROP DATABASE IF EXISTS \"$SCRATCH\";" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Both steps in one `bash -c`, so the container-side paths live inside a quoted script
# rather than in arguments - which also sidesteps Git Bash rewriting `BACKUP_DIR=/tmp/...`
# on a developer machine, which it does even with the exclusions above.
echo "== taking a backup of ${PGDATABASE}, then restoring it into ${SCRATCH}"
in_pg bash -c '
  set -euo pipefail
  export BACKUP_DIR=/tmp/verify-restore
  bash /opt/backup/backup.sh once
  echo
  bash /opt/backup/backup.sh restore "$(ls -t "$BACKUP_DIR"/*.dump | head -1)"
  rm -rf "$BACKUP_DIR"
'

echo
echo "== comparing row counts"
before="$(counts "$PGDATABASE")"
after="$(counts "$SCRATCH")"

if [ "$before" = "$after" ]; then
  echo "$after" | sed 's/^/   /'
  echo
  echo "RESTORE VERIFIED: every checked table matches the live database."
else
  echo "live:" && echo "$before" | sed 's/^/   /'
  echo "restored:" && echo "$after" | sed 's/^/   /'
  echo
  echo "RESTORE FAILED: the restored database does not match." >&2
  exit 1
fi
