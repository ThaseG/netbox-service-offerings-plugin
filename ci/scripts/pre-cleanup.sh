#!/usr/bin/env bash
# Pre-deploy cleanup. Deliberately non-destructive: it stops the running
# stack and reclaims disk space from stopped containers, dangling images
# and build cache, but never touches named volumes (Postgres/Redis/media
# data) or the acme.sh certificate directory. Data loss here would mean
# losing the whole NetBox database, so nothing volume-related is pruned.
set -euo pipefail

# .. here is ci/ (this script lives in ci/scripts/), not the repo root
CI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$CI_ROOT/docker/docker-compose.yml}"

if [ -f "$COMPOSE_FILE" ]; then
  echo "Stopping current stack (containers only, named volumes preserved)..."
  docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
fi

echo "Pruning dangling images..."
docker image prune -f

echo "Pruning build cache older than 24h..."
docker builder prune -f --filter "until=24h"
