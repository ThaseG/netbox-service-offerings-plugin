#!/usr/bin/env bash
# Issues (or reuses) a Let's Encrypt certificate for $NETBOX_DOMAIN via a
# DNS-01 challenge against Websupport DNS, using acme.sh's built-in
# `dns_websupport` provider (https://github.com/acmesh-official/acme.sh).
#
# acme.sh is idempotent: if a valid certificate already exists and is not
# yet within its ~60-day renewal window, `--issue` is a no-op ("Skip, Next
# renewal time is ..." / exit code 2). Otherwise it performs the DNS-01
# challenge and issues or renews the certificate. This is what gives us
# "reuse if it exists, else challenge" without any extra bookkeeping.
set -euo pipefail

: "${NETBOX_DOMAIN:?NETBOX_DOMAIN must be set}"
: "${ACME_EMAIL:?ACME_EMAIL must be set}"
: "${WS_ApiKey:?WS_ApiKey must be set (Websupport REST API key)}"
: "${WS_ApiSecret:?WS_ApiSecret must be set (Websupport REST API secret)}"

# .. here is ci/ (this script lives in ci/scripts/), not the repo root
CI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACME_HOME="${ACME_HOME:-$HOME/.acme.sh}"
ACME="$ACME_HOME/acme.sh"
CERT_DIR="${CERT_DIR:-$CI_ROOT/docker/nginx/certs}"
COMPOSE_FILE="${COMPOSE_FILE:-$CI_ROOT/docker/docker-compose.yml}"
# docker-compose.yml requires every service's env vars to resolve (via
# ${VAR:?err} guards) just to *parse* the file, regardless of which
# subcommand or service is targeted — so the reload callback below needs
# --env-file too, or it fails the same way `docker compose down` did.
ENV_FILE="${ENV_FILE:-$CI_ROOT/docker/.env}"

mkdir -p "$CERT_DIR"
chmod 700 "$CERT_DIR"

if [ ! -x "$ACME" ]; then
  echo "acme.sh not found at $ACME_HOME — installing..."
  curl -fsSL https://get.acme.sh | sh -s email="$ACME_EMAIL"
fi

export WS_ApiKey WS_ApiSecret

set +e
"$ACME" --issue --dns dns_websupport -d "$NETBOX_DOMAIN" --home "$ACME_HOME"
rc=$?
set -e

if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
  echo "acme.sh --issue failed with exit code $rc" >&2
  exit "$rc"
fi

"$ACME" --install-cert -d "$NETBOX_DOMAIN" --home "$ACME_HOME" \
  --key-file       "$CERT_DIR/privkey.pem" \
  --fullchain-file "$CERT_DIR/fullchain.pem" \
  --reloadcmd      "docker compose --env-file '$ENV_FILE' -f '$COMPOSE_FILE' exec -T nginx nginx -s reload || true"

chmod 600 "$CERT_DIR/privkey.pem"
chmod 644 "$CERT_DIR/fullchain.pem"
echo "Certificate ready at $CERT_DIR/fullchain.pem"
