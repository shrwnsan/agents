# Scheduled Baseline (Opt-In)

The skill never installs anything itself. If you want automatic persistence-drift
monitoring between full audits, install the zero-token watcher yourself:

## What it does

`scripts/drift-watch.sh` snapshots user-visible persistence (launchd agents/daemons,
XDG autostart, user systemd units, crontab, ld.so.preload presence), diffs against
the previous snapshot, and sends a macOS notification on any **new** item. It:

- runs as your user — no root, no network, never deletes anything except its own old snapshots
- uses absolute binary paths (launchd provides a minimal environment)
- chains each snapshot to the previous one's SHA-256, so silent edits to stored
  snapshots break the chain detectably
- prunes snapshots and JSONL logs to `FORENSICS_LOG_KEEP` newest files (default 30)

**Known limitation (accepted):** an attacker with your UID can edit both the
current snapshot *and* the stored chain tail. This raises the bar, it does not
make tampering impossible — full integrity requires copying snapshots off-host.

## Installing (macOS)

```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.user.forensics-drift.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.user.forensics-drift</string>
  <key>ProgramArguments</key><array>
    <string>/bin/sh</string>
    <string>PATH-TO-SKILL/scripts/drift-watch.sh</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>12</integer></dict>
  <key>EnvironmentVariables</key><dict><key>FORENSICS_LOG_KEEP</key><string>30</string></dict>
</dict></plist>
EOF
# edit PATH-TO-SKILL to the real path (script is POSIX sh; tested on macOS + Debian), then verify before loading:
test -f /your/real/path/scripts/drift-watch.sh || echo "PATH-TO-SKILL still wrong"
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.forensics-drift.plist
```

## Linux

`cron` or a systemd user timer calling the script; same `FORENSICS_LOG_KEEP`
environment variable. Output goes to stdout/stderr when `osascript` is absent.

## Uninstalling

```bash
launchctl bootout gui/$(id -u)/com.user.forensics-drift
rm ~/Library/LaunchAgents/com.user.forensics-drift.plist
```

## First run

The first execution creates a baseline snapshot and notifies accordingly — that
baseline should be taken right after a full skill audit came back clean.
