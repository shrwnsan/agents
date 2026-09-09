#!/usr/bin/env bash
# Thin wrapper: all implementation logic lives in publish.py
# (Python 3 stdlib only — no curl, no jq). Kept as a human-friendly
# entrypoint; see ../README.md for the environment matrix that
# motivated consolidating to a single implementation.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: publish.sh requires python3 (the implementation is publish.py)" >&2
  exit 1
fi

exec python3 "${SCRIPT_DIR}/publish.py" "$@"
