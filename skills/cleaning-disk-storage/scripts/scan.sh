#!/usr/bin/env bash
# scan.sh — read-only disk cleanup scanner for cleaning-disk-storage.
#
# Reports candidate sizes per category. Writes nothing, deletes nothing.
# Deletion decisions stay with the agent + user; this script only measures.
#
# Usage:
#   scan.sh [root]        # scan root (default: $HOME; scoping to a project dir is faster)
#
# Notes:
# - Full-home scans can take minutes on large volumes. Scope the root when you can.
# - Sizes come from `du` (actual blocks). See reference/GOTCHAS.md for sparse-file
#   and BSD/GNU drift caveats.

set -u

ROOT="${1:-$HOME}"

section() {
  printf '\n=== %s ===\n' "$1"
}

kb_to_human() {
  awk -v kb="$1" 'BEGIN {
    if (kb >= 1048576) printf "%.1f GB", kb/1048576;
    else if (kb >= 1024) printf "%.0f MB", kb/1024;
    else printf "%.0f KB", kb
  }'
}

# total_size NUL-separated-path-list  -> human total on stdout
total_size() {
  xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {print s+0}'
}

printf 'Disk usage overview (%s):\n' "$(uname -s)"
df -h "$ROOT" 2>/dev/null | tail -1 | awk '{print "  " $3 " used, " $4 " free (" $5 ")"}'

section "1. Build artifacts under $ROOT"
printf '    (node_modules / target / .venv / .next / tool caches — regenerable)\n'
BUILD_LIST="$(mktemp "${TMPDIR:-/tmp}/clean-scan-build.XXXXXX")"
find "$ROOT" -type d \( -name node_modules -o -name __pycache__ -o -name .venv \
  -o -name venv -o -name target -o -name .next -o -name .pytest_cache \
  -o -name .mypy_cache -o -name .ruff_cache \) -prune -print 2>/dev/null > "$BUILD_LIST"
COUNT=$(wc -l < "$BUILD_LIST" | tr -d ' ')
if [ "$COUNT" -gt 0 ]; then
  TOTAL="$(kb_to_human "$(tr '\n' '\0' < "$BUILD_LIST" | total_size)")"
  printf 'Found %s build dirs, total %s. Largest:\n' "$COUNT" "$TOTAL"
  tr '\n' '\0' < "$BUILD_LIST" | xargs -0 du -sk 2>/dev/null | sort -rn | head -15 |
    awk '{printf "  %8.0f MB  %s\n", $1/1024, substr($0, index($0, $2))}'
else
  printf 'None found.\n'
fi
rm -f "$BUILD_LIST"

section "2. Package manager caches"
for d in "$HOME/Library/Caches/Homebrew" "$HOME/.npm" "$HOME/.cache/uv" \
         "$HOME/Library/Caches/go-build" "$HOME/Library/Caches/pip" \
         "$HOME/Library/Caches/pnpm" "$HOME/Library/Caches/ms-playwright" \
         "$HOME/.cargo/registry/cache"; do
  [ -d "$d" ] && printf '  %-45s %s\n' "$d" "$(du -sh "$d" 2>/dev/null | cut -f1)"
done
printf '  Prefer native cleanup: brew cleanup --prune=all; uv cache clean; go clean -cache; pip cache purge\n'

section "3. General caches (top entries)"
for base in "$HOME/Library/Caches" "$HOME/.cache"; do
  [ -d "$base" ] || continue
  printf '  %s:\n' "$base"
  du -sh "$base"/* 2>/dev/null | sort -rh | head -10 | sed 's/^/    /'
done

section "4. AI agent temp dirs"
for d in "$HOME/.claude/debug" "$HOME/.claude/shell-snapshots" "$HOME/.claude/projects" \
         "$HOME/.gemini/tmp" "$HOME/.gemini/history" "$HOME/.factory/logs" \
         "$HOME/.factory/sessions" "$HOME/.continue/index" "$HOME/.codex/sessions"; do
  [ -d "$d" ] && printf '  %-40s %s\n' "$d" "$(du -sh "$d" 2>/dev/null | cut -f1)"
done

section "5. Crash logs"
for d in "$HOME/Library/Logs/DiagnosticReports" "$HOME/.local/state"; do
  [ -e "$d" ] || continue
  [ "$d" = "$HOME/.local/state" ] && find "$d" -maxdepth 3 -type d -name crash -print0 2>/dev/null | while IFS= read -r -d '' c; do
    printf '  %-40s %s\n' "$c" "$(du -sh "$c" 2>/dev/null | cut -f1)"
  done
  [ "$d" != "$HOME/.local/state" ] && printf '  %-40s %s\n' "$d" "$(du -sh "$d" 2>/dev/null | cut -f1)"
done

section "6. .DS_Store sweep"
DS_FILE="$(mktemp "${TMPDIR:-/tmp}/clean-scan-ds.XXXXXX")"
find "$ROOT" -name ".DS_Store" -type f -not -path "*/Library/*" -print0 2>/dev/null > "$DS_FILE"
DS_COUNT=$(tr '\0' '\n' < "$DS_FILE" | grep -c . || true)
if [ "${DS_COUNT:-0}" -gt 0 ]; then
  printf '  %s files, %s total\n' "$DS_COUNT" "$(kb_to_human "$(total_size < "$DS_FILE")")"
else
  printf '  None found.\n'
fi
rm -f "$DS_FILE"

section "7. macOS-only checks"
AERIALS="$HOME/Library/Application Support/com.apple.wallpaper/aerials"
[ -d "$AERIALS" ] && printf '  aerial wallpaper assets: %s\n' "$(du -sh "$AERIALS" 2>/dev/null | cut -f1)"

printf '\nScan complete. Read-only: nothing was modified.\n'
printf 'Next: review findings with the user, then clean per SKILL.md (trash-only, confirm >1 GB items).\n'
