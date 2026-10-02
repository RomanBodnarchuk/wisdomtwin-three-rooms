#!/usr/bin/env bash
# Gated release: deploys the agent and proves 7/7 tests passed on the exact deployed version.
# Does NOT enable dialing. WT_DIAL_MODE stays whatever it was (default: disabled).
# Run from project root:  op run --env-file=scripts/env.op -- bash scripts/release.sh
set -euo pipefail
REF="${WT_SUPABASE_PROJECT_REF:?}"
# 0. Close the release gate before anything changes.
supabase secrets set --project-ref "$REF" WT_RELEASED_AGENT_VERSION=blocked
node scripts/canon-lint.mjs --pre-release            # 1. content + placeholder checks (tests not attached yet)
elevenlabs tests push                                 # 2. upload tests; ids land in tests.json
node scripts/attach-tests.mjs                         # 3. attach all 7 to the agent config
node scripts/canon-lint.mjs --release                 # 3b. full gate: now also requires exactly 7 attached tests
elevenlabs agents push --dry-run                      # 4. local request preview
elevenlabs agents push --version-description "release $(date -u +%Y-%m-%dT%H:%MZ)"   # 5. deploy
VERSION="$(node scripts/verify-release.mjs)"          # 6. 7/7 passed on this version, or exit
# 7. Re-open the gate for exactly this version. Any later change to the agent produces a new version_id
#    and the backend refuses to dial until this script passes again.
supabase secrets set --project-ref "$REF" WT_RELEASED_AGENT_VERSION="$VERSION"
echo "Released $VERSION. Evidence: release/evidence-$VERSION.json. Dialing mode unchanged."
