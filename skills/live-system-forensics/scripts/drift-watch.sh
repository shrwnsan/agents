#!/bin/sh
# drift-watch.sh — zero-token persistence drift watcher (opt-in companion to the
# live-system-forensics skill). Snapshots user-visible persistence, diffs against
# the previous snapshot, and notifies on NEW items. Never touches the persistence
# items it watches, never requires root, never contacts the network.
#
# Retention: deletes its own snapshots, and this host's findings logs
# (<hostname>-YYYYMMDD-HHMM.jsonl), beyond the FORENSICS_LOG_KEEP newest of each
# (default 30; 0 disables). Other JSONL in the directory, such as app audit
# receipts, is never pruned. Set in the launchd plist or your env.

STATE_DIR="${HOME}/.cache/live-system-forensics"
KEEP="${FORENSICS_LOG_KEEP:-30}"
HOST=$(hostname 2>/dev/null || uname -n)
TS=$(/bin/date +%Y%m%d-%H%M%S)-$$
SNAP="${STATE_DIR}/watch-snapshot-${TS}.txt"
# computed before SNAP is written below, so the newest existing snapshot (1p)
# is the previous run; 2p would diff against two runs back
PREV=$(/bin/ls -t "${STATE_DIR}"/watch-snapshot-*.txt 2>/dev/null | /usr/bin/sed -n 1p)

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

# retention: keep the newest $KEEP snapshots and this host's findings logs.
# The JSONL glob spells out <hostname>-YYYYMMDD-HHMM.jsonl: app audit receipts
# (<app>-v<ver>-<date>.jsonl) and the logs of a host whose name starts with
# this one (<hostname>-2-...) share this directory and must never be pruned.
# Note: ls-then-delete has a small TOCTOU window; harmless for a scheduler-cadence
# watcher (worst case: a snapshot created mid-prune survives to the next prune).
if [ "$KEEP" -gt 0 ]; then
  /bin/ls -t "${STATE_DIR}"/watch-snapshot-*.txt 2>/dev/null | /usr/bin/tail -n +"$((KEEP+1))" | while read -r f; do /bin/rm -f "$f"; done
  if [ -n "$HOST" ]; then
    /bin/ls -t "${STATE_DIR}/${HOST}"-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9].jsonl 2>/dev/null \
      | /usr/bin/tail -n +"$((KEEP+1))" | while read -r f; do /bin/rm -f "$f"; done
  fi
fi
