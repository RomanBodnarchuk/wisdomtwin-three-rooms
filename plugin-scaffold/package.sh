#!/usr/bin/env bash
# Build the directory ZIP. The archive root is the plugin, not this repository.
# Pass --check to validate the manifest without writing a ZIP.
# Set MCP_SERVER_URL to the public https endpoint ending in /mcp when building the ZIP.

set -euo pipefail
cd "$(dirname "$0")"

check_only=0
if [[ "${1:-}" == "--check" ]]; then
  check_only=1
fi

python3 - << 'PY'
import json
import sys
from pathlib import Path

root = Path(".")
plugin = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
mcp = json.loads((root / "mcp.json").read_text(encoding="utf-8"))
allowed = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
extra = sorted(set(plugin) - allowed)
if extra:
    sys.exit(f"plugin.json has fields the Agent Plugins schema rejects: {', '.join(extra)}")
if plugin.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
    sys.exit("plugin.json schema is missing")
if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json":
    sys.exit("mcp.json schema is missing")
interface = plugin["extensions"]["com.openai"]["interface"]
short = interface["shortDescription"]
display = interface["displayName"]
if len(display) > 30 or "\n" in display:
    sys.exit(f"displayName must be one line of at most 30 characters ({len(display)})")
if len(short) > 30 or "\n" in short:
    sys.exit(f"shortDescription must be one line of at most 30 characters ({len(short)})")
for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
    value = interface.get(key, "")
    if not value.startswith("https://") or len(value) > 1024:
        sys.exit(f"{key} must be an https URL")
prompts = interface["defaultPrompt"]
if len(prompts) > 3 or len(set(prompts)) != len(prompts):
    sys.exit("defaultPrompt allows at most three unique prompts")
if any(len(item) > 128 or "\n" in item or "@" in item for item in prompts):
    sys.exit("a starter prompt is too long or contains an @mention")
review = plugin["extensions"]["com.openai"]["review"]["test_cases"]
if len(review["positive"]) != 5 or len(review["negative"]) != 3:
    sys.exit("review needs five positive cases and three negative cases")
logo = root / interface["logo"].removeprefix("./")
if not logo.is_file():
    sys.exit(f"missing logo {logo}")
servers = mcp.get("mcpServers", {})
if list(servers) != ["wisdomtwin"]:
    sys.exit("mcp.json must declare one server named wisdomtwin")
entry = servers["wisdomtwin"]
if entry.get("type") != "streamable-http" or not str(entry.get("url", "")).startswith("https://"):
    sys.exit("wisdomtwin must be a streamable-http https server")
print(f"manifest checks passed (subtitle {len(short)} characters)")
PY

if [[ "$check_only" -eq 1 ]]; then
  exit 0
fi

if [[ -z "${MCP_SERVER_URL:-}" ]]; then
  echo "Set MCP_SERVER_URL to the public https origin plus /mcp, then run ./package.sh again." >&2
  exit 1
fi

case "${MCP_SERVER_URL}" in
  https://*/mcp) ;;
  *)
    echo "MCP_SERVER_URL must be an https URL ending in /mcp." >&2
    exit 1
    ;;
esac

case "${MCP_SERVER_URL}" in
  *REPLACE_WITH*|*example.com*|*localhost*|*127.0.0.1*)
    echo "MCP_SERVER_URL is not a production host." >&2
    exit 1
    ;;
esac

outdir="dist"
rm -rf "$outdir"
mkdir -p "$outdir/assets"
MCP_SERVER_URL="$MCP_SERVER_URL" python3 - << 'PY'
import json
import os
from pathlib import Path

mcp = json.loads(Path("mcp.json").read_text(encoding="utf-8"))
mcp["mcpServers"]["wisdomtwin"]["url"] = os.environ["MCP_SERVER_URL"]
Path("dist/mcp.json").write_text(json.dumps(mcp, indent=2) + "\n", encoding="utf-8")
PY
cp plugin.json "$outdir/plugin.json"
cp assets/logo.svg "$outdir/assets/logo.svg"
(
  cd "$outdir"
  rm -f wisdomtwin-plugin.zip
  zip -r wisdomtwin-plugin.zip plugin.json mcp.json assets/logo.svg >/dev/null
)
echo "Wrote ${outdir}/wisdomtwin-plugin.zip"
