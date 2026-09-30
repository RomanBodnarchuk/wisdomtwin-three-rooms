#!/usr/bin/env bash
# Deploy the plugin directory to Railway and check /health.
# Values are passed through from the shell. This script does not echo them.
# Do not run it under bash -x.

set -euo pipefail
cd "$(dirname "$0")"

if ! command -v railway >/dev/null 2>&1; then
  echo "The Railway CLI is not installed. Install it, log in, and run this script again." >&2
  exit 1
fi

if [[ -z "${RAILWAY_PUBLIC_URL:-}" ]]; then
  echo "Set RAILWAY_PUBLIC_URL to the deployed HTTPS origin, with no trailing path." >&2
  exit 1
fi

case "${RAILWAY_PUBLIC_URL}" in
  https://*) ;;
  *)
    echo "RAILWAY_PUBLIC_URL must be an https origin." >&2
    exit 1
    ;;
esac

export PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-$RAILWAY_PUBLIC_URL}"

required=(
  OPENAI_API_KEY
  DATABASE_URL
  REDIS_URL
  SLACK_CLIENT_ID
  SLACK_CLIENT_SECRET
  CONNECTOR_TOKEN_KEY
  PUBLIC_BASE_URL
)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Required environment variable is unset: ${name}" >&2
    exit 1
  fi
done

echo "Link this directory to the Railway service before running. Uploading after variables are set."

optional=(
  OPENAI_GENERATION_MODEL
  OPENAI_EMBEDDING_MODEL
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  OAUTH_CLIENT_ID
  OAUTH_REDIRECT_URIS
  PRIVACY_POLICY_URL
  OPENAI_APPS_CHALLENGE
)
names=(
  "${required[@]}"
  SLACK_CONNECTOR_ENABLED
  GMAIL_CONNECTOR_ENABLED
  DRIVE_CONNECTOR_ENABLED
  "${optional[@]}"
)

for name in "${names[@]}"; do
  if [[ -n "${!name:-}" ]]; then
    railway variable set "${name}=${!name}" >/dev/null
  fi
done

railway up

health="${RAILWAY_PUBLIC_URL%/}/health"
echo "Checking ${health}"
curl --fail --silent --show-error "${health}"
echo
