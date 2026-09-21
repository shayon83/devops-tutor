#!/usr/bin/env bash
# Writes a .env that CI can boot the stack with.
#
# The values in .env.example are placeholders, and the backend deliberately
# refuses to start on a placeholder -- that fail-fast behaviour is the point of
# backend/src/config.py. So CI starts from .env.example (which keeps this
# script honest about the full variable list) and substitutes obviously fake
# but structurally valid credentials.
#
# These credentials cannot register with LiveKit Cloud. Everything that does
# not need a real voice connection still works.
set -euo pipefail

cd "$(dirname "$0")/.."
cp .env.example .env

replace() {
  # Replaces a KEY=... line in place, failing if the key is not present, so a
  # variable renamed in .env.example cannot silently stop being set here.
  local key=$1 value=$2
  grep -q "^${key}=" .env || { echo "::error::${key} missing from .env.example"; exit 1; }
  sed -i "s|^${key}=.*|${key}=${value}|" .env
}

replace LIVEKIT_URL "wss://ci-dummy.livekit.cloud"
replace LIVEKIT_API_KEY "ci-dummy-api-key"
replace LIVEKIT_API_SECRET "ci-dummy-api-secret-at-least-32-bytes-long"
replace GRAFANA_ADMIN_PASSWORD "ci-dummy-grafana-password"

echo "Wrote .env with dummy credentials:"
sed 's/=.*/=<redacted>/' .env | grep -E '^(LIVEKIT|GRAFANA)' || true
