#!/usr/bin/env bash
# Deploy the latest main to this host. Preserves .env and docker volumes.
# Run on the VM: manually (./scripts/deploy.sh), via cron, or a self-hosted runner.
set -euo pipefail

cd "${HACKLET_DIR:-$HOME/hacklet-league}"

git fetch origin
git reset --hard origin/main

docker compose up -d --build

# Caddy is bind-mounted, so `up -d` won't restart it on a Caddyfile change; reload it
# explicitly (zero-downtime) so routing changes always take effect. Falls back to a
# restart if the running config can't be reloaded.
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null \
  || docker compose restart caddy

docker image prune -f   # drop dangling images from the rebuild (keeps disk in check)
