#!/usr/bin/env bash
# Print deck/WisdomTwin-Investor-Deck.html to PDF with headless Chrome and
# refresh every path the public site serves the deck from (see public/404.html).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/deck/WisdomTwin-Investor-Deck.html"
OUT="$ROOT/public/WisdomTwin-Investor-Deck.pdf"

CHROME="${CHROME:-$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || command -v chromium-browser || true)}"
if [[ -z "$CHROME" ]]; then
  echo "No Chrome/Chromium binary found. Set CHROME=/path/to/chrome." >&2
  exit 1
fi

# A throwaway profile keeps the print run independent of any running Chrome instance.
PROFILE="$(mktemp -d)"
trap 'rm -rf "$PROFILE"' EXIT

"$CHROME" \
  --headless=new \
  --no-sandbox \
  --disable-gpu \
  --user-data-dir="$PROFILE" \
  --hide-scrollbars \
  --force-device-scale-factor=1 \
  --virtual-time-budget=5000 \
  --run-all-compositor-stages-before-draw \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "file://$SRC" >/dev/null 2>&1

ALIASES=(
  "$ROOT/public/deck.pdf"
  "$ROOT/public/wisdomtwin-deck.pdf"
  "$ROOT/public/WisdomTwin-E4-Investor-Deck-2026-08-10.pdf"
  "$ROOT/public/WisdomTwin-E4-Investor-Deck-2026-08-11.pdf"
  "$ROOT/public/downloads/wisdomtwin-deck.pdf"
  "$ROOT/wisdomtwin-deck.pdf"
)
for alias in "${ALIASES[@]}"; do
  cp "$OUT" "$alias"
done

echo "Wrote $OUT and ${#ALIASES[@]} aliases"
md5sum "$OUT"
