#!/usr/bin/env bash
# Check configuration by default. --deploy is an explicit, separately authorized
# public deployment. Secret values go through stdin, never CLI arguments.

set -euo pipefail
cd "$(dirname "$0")"

mode="${1:---check}"
case "$mode" in
  --check|--deploy) ;;
  --help) echo "Usage: ./deploy.sh [--check|--deploy]. --deploy needs hosting and public-release authorization."; exit 0 ;;
  *) echo "Use --check or --deploy." >&2; exit 2 ;;
esac
if [[ "$-" == *x* ]]; then
  set +x
  echo "Disable shell tracing before handling deployment credentials." >&2
  exit 1
fi
export PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-${RAILWAY_PUBLIC_URL:-}}"
export WISDOMTWIN_ENV=production HOST=0.0.0.0

required=(
  DATABASE_URL
  REDIS_URL
  CONNECTOR_TOKEN_KEY
  PUBLIC_BASE_URL
  OAUTH_CLIENT_ID
  OAUTH_REDIRECT_URIS
  OIDC_ISSUER
  OIDC_CLIENT_ID
)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Required environment variable is unset: ${name}" >&2
    exit 1
  fi
done
python3 -c 'from runtime import validate_runtime; validate_runtime()'
if [[ "$mode" == --check ]]; then
  echo "Production configuration names and runtime restrictions checked. No deployment performed."
  exit 0
fi
if ! command -v railway >/dev/null 2>&1; then
  echo "Install and authorize the Railway CLI, then link the intended service." >&2
  exit 1
fi

optional=(
  OPENAI_GENERATION_MODEL
  OPENAI_EMBEDDING_MODEL
  OPENAI_REASONING_EFFORT
  OPENAI_API_KEY
  WISDOMTWIN_ALLOW_PAID_MODEL_APIS
  WISDOMTWIN_GENERATION_MODE
  OIDC_CLIENT_SECRET
  SLACK_CLIENT_ID
  SLACK_CLIENT_SECRET
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  PRIVACY_POLICY_URL
  TERMS_OF_SERVICE_URL
  SUPPORT_URL
  OPENAI_APPS_CHALLENGE
)
names=(
  "${required[@]}"
  WISDOMTWIN_ENV
  HOST
  SLACK_CONNECTOR_ENABLED
  SLACK_POLICY_APPROVED
  GMAIL_CONNECTOR_ENABLED
  DRIVE_CONNECTOR_ENABLED
  GOOGLE_REVIEW_APPROVED
  WISDOMTWIN_AUTH_DISABLED
  WISDOMTWIN_USE_FIXTURES
  "${optional[@]}"
)

# Reset any existing unsafe flags even when omitted from the calling shell.
export WISDOMTWIN_AUTH_DISABLED=false WISDOMTWIN_USE_FIXTURES=false
export SLACK_CONNECTOR_ENABLED="${SLACK_CONNECTOR_ENABLED:-false}"
export SLACK_POLICY_APPROVED="${SLACK_POLICY_APPROVED:-false}"
export GMAIL_CONNECTOR_ENABLED="${GMAIL_CONNECTOR_ENABLED:-false}"
export DRIVE_CONNECTOR_ENABLED="${DRIVE_CONNECTOR_ENABLED:-false}"
export GOOGLE_REVIEW_APPROVED="${GOOGLE_REVIEW_APPROVED:-false}"
export WISDOMTWIN_ALLOW_PAID_MODEL_APIS="${WISDOMTWIN_ALLOW_PAID_MODEL_APIS:-false}"
export WISDOMTWIN_GENERATION_MODE="${WISDOMTWIN_GENERATION_MODE:-extractive}"

for name in "${names[@]}"; do
  if [[ -n "${!name:-}" ]]; then
    if ! printf '%s' "${!name}" | railway variable set "$name" --stdin --skip-deploys >/dev/null 2>&1; then
      echo "Railway variable update failed for ${name}; inspect the service privately." >&2
      exit 1
    fi
  fi
done

railway up

health="${PUBLIC_BASE_URL%/}/health"
echo "Checking ${health}"
curl --fail --silent --show-error "${health}"
echo
