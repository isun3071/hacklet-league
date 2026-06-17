#!/usr/bin/env bash
# Deploy the latest main to this host. Preserves .env and docker volumes.
# Run on the VM: manually (./scripts/deploy.sh), via cron, or a self-hosted runner.
set -euo pipefail

cd "${HACKLET_DIR:-$HOME/hacklet-league}"

git fetch origin
git reset --hard origin/main

docker compose up -d --build
docker image prune -f   # drop dangling images from the rebuild (keeps disk in check)
