#!/bin/sh
# drift-watch.sh — zero-token persistence drift watcher (opt-in companion to the
# live-system-forensics skill). Snapshots user-visible persistence, diffs against
# the previous snapshot, and notifies on NEW items. Never removes anything,
# never requires root, never contacts the network.
#
# Retention: JSONL logs and snapshots are pruned to FORENSICS_LOG_KEEP newest
# files (default 30). Set in the launchd plist or your env.

STATE_DIR="${HOME}/.cache/live-system-forensics"
KEEP="${FORENSICS_LOG_KEEP:-30}"
TS=$(/bin/date +%Y%m%d-%H%M%S)-$$
SNAP="${STATE_DIR}/watch-snapshot-${TS}.txt"
PREV=$(/bin/ls -t "${STATE_DIR}"/watch-snapshot-*.txt 2>/dev/null | /usr/bin/sed -n 2p)

/bin/mkdir -p "${STATE_DIR}"

snapshot() {
  # macOS persistence surfaces; missing commands/dirs are skipped silently
  command -v launchctl >/dev/null 2>&1 && launchctl list 2>/dev/null | /usr/bin/awk 'NR>1 && $3 !~ /^com\.apple/ {print "launchd\t" $3}' | /usr/bin/sort -u
  [ -d "${HOME}/Library/LaunchAgents" ] && /bin/ls "${HOME}/Library/LaunchAgents" 2>/dev/null | /usr/bin/sed 's/^/useragent\t/'
  [ -d "/Library/LaunchAgents" ] && /bin/ls "/Library/LaunchAgents" 2>/dev/null | /usr/bin/sed 's/^/sysagent\t/'
  [ -d "/Library/LaunchDaemons" ] && /bin/ls "/Library/LaunchDaemons" 2>/dev/null | /usr/bin/sed 's/^/daemon\t/'
  # Linux persistence surfaces
  [ -d "${HOME}/.config/autostart" ] && /bin/ls "${HOME}/.config/autostart" 2>/dev/null | /usr/bin/sed 's/^/autostart\t/'
  [ -d "${HOME}/.config/systemd/user" ] && /bin/ls "${HOME}/.config/systemd/user" 2>/dev/null | /usr/bin/sed 's/^/usersystemd\t/'
  crontab -l 2>/dev/null | /usr/bin/sed 's/^/cron\t/'
  [ -f "/etc/ld.so.preload" ] && { echo "ldso-preload\tPRESENT"; /bin/cat /etc/ld.so.preload 2>/dev/null | /usr/bin/sed 's/^/ldso-preload-line\t/'; }
}

snapshot | sort > "${SNAP}"

# integrity chain: each snapshot records the previous snapshot's SHA,
# so silent edits to older snapshots become detectable
if [ -n "$PREV" ]; then
  if command -v shasum >/dev/null 2>&1; then
    echo "prevsha\t$(shasum -a 256 "$PREV" | awk '{print $1}')" >> "${SNAP}"
  elif command -v sha256sum >/dev/null 2>&1; then
    echo "prevsha\t$(sha256sum "$PREV" | awk '{print $1}')" >> "${SNAP}"
  fi
fi

notify() {  # $1 = message
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"$1\" with title \"forensics drift-watch\"" 2>/dev/null
  else
    printf '[drift-watch] %s\n' "$1"
  fi
}

if [ -n "$PREV" ]; then
  NEW=$(/usr/bin/diff "$PREV" "$SNAP" 2>/dev/null | /usr/bin/grep '^>' | /usr/bin/grep -v '^> prevsha' | /usr/bin/sed 's/^> //')
  if [ -n "$NEW" ]; then
    echo "$NEW" > "${STATE_DIR}/drift-last.txt"
    N=$(printf '%s\n' "$NEW" | /usr/bin/grep -c '^')
    notify "${N} new persistence item(s) — see ${STATE_DIR}/drift-last.txt"
  fi
  REMOVED=$(/usr/bin/diff "$PREV" "$SNAP" 2>/dev/null | /usr/bin/grep '^<' | /usr/bin/grep -v '^< prevsha')
  [ -n "$REMOVED" ] && printf '%s\n' "$REMOVED" > "${STATE_DIR}/drift-last-removed.txt"
else
  notify "baseline snapshot created (${SNAP})"
fi

# retention: keep newest $KEEP snapshots and JSONL logs.
# Note: ls-then-delete has a small TOCTOU window; harmless for a scheduler-cadence
# watcher (worst case: a snapshot created mid-prune survives to the next prune).
if [ "$KEEP" -gt 0 ]; then
  /bin/ls -t "${STATE_DIR}"/watch-snapshot-*.txt 2>/dev/null | /usr/bin/tail -n +"$((KEEP+1))" | while read -r f; do /bin/rm -f "$f"; done
  /bin/ls -t "${STATE_DIR}"/*-[0-9]*.jsonl 2>/dev/null | /usr/bin/tail -n +"$((KEEP+1))" | while read -r f; do /bin/rm -f "$f"; done
fi
