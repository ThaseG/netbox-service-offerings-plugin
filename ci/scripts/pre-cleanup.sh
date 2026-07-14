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
# docker-compose.yml requires every service's env vars to resolve (via
# ${VAR:?err} guards) just to *parse* the file — `down` needs this file
# present just as much as `up` does, even though it isn't writing/reading
# any of the actual values.
ENV_FILE="${ENV_FILE:-$CI_ROOT/docker/.env}"

if [ -f "$COMPOSE_FILE" ]; then
  echo "Stopping current stack (containers only, named volumes preserved)..."
  compose_args=(-f "$COMPOSE_FILE")
  if [ -f "$ENV_FILE" ]; then
    compose_args=(--env-file "$ENV_FILE" "${compose_args[@]}")
  else
    echo "WARNING: $ENV_FILE not found — 'docker compose down' will likely fail to parse" \
         "docker-compose.yml's required environment variables." >&2
  fi
  # Deliberately don't hard-fail the deploy if this errors (e.g. nothing
  # was running yet) — but DO surface it loudly, since a silently-swallowed
  # failure here leaves stale containers/networks behind that the next
  # `up` won't necessarily reconcile with, which is exactly the kind of
  # thing that produces confusing "container is up but can't reach its
  # peers" failures downstream.
  if ! docker compose "${compose_args[@]}" down --remove-orphans; then
    echo "WARNING: 'docker compose down' failed (see above) — stale containers/networks may remain." >&2
  fi
fi

echo "Pruning dangling images..."
docker image prune -f

echo "Pruning build cache older than 24h..."
docker builder prune -f --filter "until=24h"
