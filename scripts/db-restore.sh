#!/usr/bin/env bash
# Restore a gzipped pg_dump into the running database. Restore into an EMPTY DB
# (i.e. `docker compose up -d db` on a fresh host, BEFORE the backend has run
# migrations). Usage:
#   ./scripts/db-restore.sh backups/hacklet-<timestamp>.sql.gz
set -euo pipefail

cd "${HACKLET_DIR:-$HOME/hacklet-league}"
file="${1:?usage: db-restore.sh <dump.sql.gz>}"

gunzip -c "$file" | docker compose exec -T db \
  psql -U "${POSTGRES_USER:-hacklet}" -d "${POSTGRES_DB:-hacklet}" -v ON_ERROR_STOP=1 --single-transaction
echo "restored $file"
