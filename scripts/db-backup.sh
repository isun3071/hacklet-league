#!/usr/bin/env bash
# Dump the Postgres database to a timestamped, gzipped file under backups/.
# Run on whichever host currently holds the data.
set -euo pipefail

cd "${HACKLET_DIR:-$HOME/hacklet-league}"
mkdir -p backups
out="backups/hacklet-$(date +%Y%m%d-%H%M%S).sql.gz"

docker compose exec -T db pg_dump -U "${POSTGRES_USER:-hacklet}" "${POSTGRES_DB:-hacklet}" | gzip > "$out"
echo "wrote $out"
