#!/usr/bin/env bash
# --check stays offline. --candidate creates an explicitly non-submission ZIP.
# No argument (or --release) gates a production ZIP on live deployment evidence.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 package_validator.py "$@"
