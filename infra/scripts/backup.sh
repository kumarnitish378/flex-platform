#!/usr/bin/env bash
# PostgreSQL backup and restore (task R01).
#
# `non-functional.md` (Availability): daily backups, 14-day retention, restore tested
# monthly. The restore half lives in this same file on purpose - a backup script
# without a restore path is a script nobody has ever run in the direction that matters.
#
# Usage:
#   backup.sh once                 take one dump now
#   backup.sh loop                 take one every BACKUP_INTERVAL_SECONDS (the container)
#   backup.sh list                 what is in the backup directory
#   backup.sh verify <file>        prove a dump is readable and non-trivial
#   backup.sh restore <file> [db]  restore into `db` (default: a scratch copy, NOT live)
#
# Connection comes from the standard PG* environment variables, so the same script runs
# in the compose and on a laptop against a tunnel.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"
PGDATABASE="${PGDATABASE:-smartcab}"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

take_backup() {
  mkdir -p "$BACKUP_DIR"
  local stamp file
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  file="$BACKUP_DIR/${PGDATABASE}-${stamp}.dump"

  # Custom format (-Fc), not plain SQL: it is compressed, and `pg_restore` can read it
  # selectively, which is what makes "restore one table someone truncated" possible
  # without replaying the whole database.
  #
  # Written to a .part first and renamed at the end. A dump interrupted halfway is a
  # file that looks like a backup and is not, and the day you find out is the day you
  # need it.
  log "dumping ${PGDATABASE} -> $(basename "$file")"
  pg_dump --format=custom --compress=6 --file="${file}.part" "$PGDATABASE"
  mv "${file}.part" "$file"

  verify_backup "$file"
  log "backup complete: $(basename "$file") ($(du -h "$file" | cut -f1))"
  prune
}

verify_backup() {
  local file="${1:?usage: backup.sh verify <file>}"
  [ -f "$file" ] || die "no such backup: $file"

  # `pg_restore --list` parses the archive's table of contents. A truncated or corrupt
  # dump fails here rather than at 3 a.m. during a restore.
  local entries
  entries="$(pg_restore --list "$file" | grep -c '^[0-9]' || true)"
  [ "$entries" -gt 0 ] || die "$file has no restorable entries"

  # A dump of an empty database is also "valid". The schema has well over twenty
  # tables, so a table of contents this short means the dump ran against the wrong
  # database - which is a silent failure worth catching here.
  [ "$entries" -ge 20 ] || die "$file has only $entries entries; wrong database?"
  log "verified $(basename "$file"): $entries restorable entries"
}

prune() {
  # -mtime +N is "older than N days".
  local removed
  removed="$(find "$BACKUP_DIR" -name "${PGDATABASE}-*.dump" -type f -mtime "+${RETENTION_DAYS}" -print -delete | wc -l)"
  [ "$removed" -eq 0 ] || log "pruned $removed backup(s) older than ${RETENTION_DAYS} days"
}

list_backups() {
  mkdir -p "$BACKUP_DIR"
  ls -lh "$BACKUP_DIR"/${PGDATABASE}-*.dump 2>/dev/null || log "no backups yet"
}

restore_backup() {
  local file="${1:?usage: backup.sh restore <file> [target-database]}"
  # Default target is a scratch database, never the live one. Restoring over production
  # must be something somebody typed on purpose.
  local target="${2:-${PGDATABASE}_restore_check}"

  [ -f "$file" ] || die "no such backup: $file"
  verify_backup "$file"

  if [ "$target" = "$PGDATABASE" ]; then
    log "WARNING: restoring over the LIVE database '${target}'."
    log "Stop the api, ingestor, worker and beat containers first, or they will write"
    log "into a half-restored schema."
    [ "${CONFIRM_LIVE_RESTORE:-}" = "yes" ] \
      || die "refusing: re-run with CONFIRM_LIVE_RESTORE=yes"
  fi

  log "recreating ${target}"
  psql --dbname=postgres --quiet --command="DROP DATABASE IF EXISTS \"${target}\";"
  psql --dbname=postgres --quiet --command="CREATE DATABASE \"${target}\";"

  # --no-owner / --no-privileges: the dump records the roles of the box it came from,
  # and a restore onto a fresh VM has none of them. The application connects as one
  # role anyway.
  log "restoring $(basename "$file") into ${target}"
  pg_restore --dbname="$target" --no-owner --no-privileges --exit-on-error "$file"

  local tables
  tables="$(psql --dbname="$target" --tuples-only --no-align \
    --command="SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")"
  log "restore complete: ${target} has ${tables} tables"
  [ "$tables" -ge 20 ] || die "restored database has only ${tables} tables"
}

loop() {
  log "backup loop started: every ${INTERVAL}s, keeping ${RETENTION_DAYS} days"
  while true; do
    take_backup || log "backup failed; will retry at the next interval"
    sleep "$INTERVAL"
  done
}

case "${1:-once}" in
  once)    take_backup ;;
  loop)    loop ;;
  list)    list_backups ;;
  verify)  verify_backup "${2:-}" ;;
  restore) restore_backup "${2:-}" "${3:-}" ;;
  *)       die "unknown command: $1 (once | loop | list | verify | restore)" ;;
esac
