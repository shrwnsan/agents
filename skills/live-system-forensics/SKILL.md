---
name: live-system-forensics
description: Perform live forensic analysis on Unix systems to detect malware and suspicious activity. Analyzes running processes, network connections, startup persistence (systemd, LaunchAgents, cron), recent files, and IDE extensions. Use when user asks to check for malware, investigate suspicious activity, audit system security, or analyze unknown applications like AI IDEs.
---

# Live System Forensics

## Quick Start

1. Check running processes for anomalies
2. Analyze network connections
3. Audit startup persistence (systemd, LaunchAgents, cron, XDG autostart)
4. Review recent file activity
5. Examine IDE/AI tool extensions and configurations
6. Provide findings summary with risk assessment

**Write policy**: recon is read-only except for ONE sanctioned write — the JSONL findings log in `~/.cache/live-system-forensics/` (see Output Format). The scheduled drift watcher is optional and never installed by the skill itself.

**Efficiency note**: Phases 1-3 are independent — run them as parallel tool calls. Note: some Phase 3 checks need `sudo` (system systemd, `sfltool dumpbtm`); if running unprivileged, run those separately and treat "permission denied" on system paths as expected, not suspicious — only permission failures on your own account's files are a finding.

**Deep-dive references** (load only when needed):
- `reference/PROCESSES.md` — process triage, codesign verification, hidden-process detection
- `reference/NETWORK.md` — connection analysis, `ss`/`/proc` fallbacks for systems without `lsof`
- `reference/PERSISTENCE.md` — full persistence matrix per platform (launchd, systemd, cron, XDG, ld.so.preload, shell rc)
- `reference/SYSTEMD.md` — systemd unit forensics detail
- `reference/EXTENSIONS.md` — IDE/browser extension audit detail
- `reference/ALLOWLIST.md` — per-host known-good items; classify every finding as allowlisted / known-apple / unknown

## Purpose

Detect malware, suspicious processes, and persistence mechanisms on Unix systems (macOS, Linux, WSL) through live forensic analysis. Unlike disk forensics, this examines the running system state to identify active threats.

## When to Use

- User suspects malware or unwanted software
- Investigating unknown applications (e.g., Antigravity IDE, AI tools)
- Auditing system security after installing new software
- Checking for suspicious processes, network connections, or startup persistence
- Responding to security incidents

## Supported Platforms

- **macOS**: LaunchAgents, LaunchDaemons, launchctl live state, Background Task Management, cron
- **Linux**: systemd (user + system), cron, XDG autostart, ld.so.preload, init.d
- **WSL**: Same as Linux + Windows interop paths

## Analysis Workflow

### Phase 1: Process Analysis

**Check running processes (use `auxww` — truncated commands hide indicators):**
```bash
ps auxww
```

On non-BSD `ps` (some Linux/SysV): `ps -ef`. For deeper triage — parent/child anomalies, dead-parent orphans, codesign verification on macOS — see `reference/PROCESSES.md`.

**Find processes by name or path:**
```bash
ps auxww | grep -i "suspicious_name"
ps auxww | grep -E "(antigravity|gravity|vscode|ide)"
```

**Baseline (macOS) — run first; it gates confidence in everything after:**
```bash
csrutil status   # "enabled" = normal; "disabled" = userland results are unreliable — note in output and downgrade all verdicts
```

**Process analysis focus:**
- Unknown processes (not standard system processes)
- Processes with high CPU/memory consumption
- Processes running from unexpected paths (e.g., `/tmp`, `~/Library`, hidden dirs)
- On macOS: verify suspicious binaries with `codesign -dv --verify` and `spctl -a -t execute <path>` — unsigned/adhoc-signed binaries are a strong signal
- Classify every unknown-looking item against `reference/ALLOWLIST.md`: allowlisted / known-apple (under /System) / unknown → investigate

### Phase 2: Network Analysis

**Check active connections (macOS/BSD):**
```bash
lsof -i -P -n | grep -E "(LISTEN|ESTABLISHED)"
```

(`-n` skips reverse DNS — much faster and avoids tipping off DNS logs.)

**Linux without `lsof`:**
```bash
ss -tunap
```

See `reference/NETWORK.md` for `/proc/net/tcp` parsing on minimal containers.

**Focus:** map every connection and listener to a known process. Investigate any listener or outbound connection whose owning process you can't explain.

**Listener rule (non-negotiable):** every listening socket must be *named in the report* — port, owning process, and why it's listening. An unexplained listener is never omitted or summarized away; if the owner can't be determined, escalate it as a finding. (A backdoor's listener is easy to lose inside a long connection dump — name each one explicitly.)

### Phase 3: Persistence Analysis

**macOS - User LaunchAgents:**
```bash
ls -la ~/Library/LaunchAgents/
```

**macOS - System LaunchAgents/LaunchDaemons:**
```bash
ls -la /Library/LaunchAgents/
ls -la /Library/LaunchDaemons/
```

**macOS - live launchd state (plist files on disk can be stale or missing; check what's actually loaded):**
```bash
launchctl list | awk '$3 !~ /^com\.apple/'
sudo launchctl dumpstate | grep -v com.apple > /tmp/launchd-nonapple.txt   # catches agents bootstrapped without a plist on disk; review the full dump file
sudo sfltool dumpbtm   # Background Task Management DB (Ventura+) — catches items not visible in /Library
```
Limitation: agents injected into a running launchd session via `launchctl bootstrap` without disk artifacts, or with SIP compromised, may evade all of the above — a clean result here is not proof of absence.

**macOS - system extensions & kexts:**
```bash
systemextensionsctl list
```

**Linux/WSL - systemd (user):**
```bash
systemctl --user list-timers
systemctl --user list-units --type=service --all   # needs XDG_RUNTIME_DIR; over non-graphical SSH this errors — fall back to: ls -la ~/.config/systemd/user/
ls -la ~/.config/systemd/user/
```

**Linux/WSL - systemd (system, requires root):**
```bash
systemctl list-timers
systemctl list-units --type=service --all
ls -la /etc/systemd/system/   # admin-configured units (persistence lands here); /lib or /usr/lib/systemd/system is distro-maintained
```

**Linux/WSL - cron:**
```bash
crontab -l
ls -la /etc/cron.d/
ls -la /etc/cron.daily/ /etc/cron.hourly/ 2>/dev/null
```

**Linux/WSL - XDG autostart (commonly missed):**
```bash
# User-level (runs at GUI login)
ls -la ~/.config/autostart/ 2>/dev/null
# System-wide (affects all users — higher severity if unexpected)
ls -la /etc/xdg/autostart/ 2>/dev/null
```

**Linux - dynamic linker preload (CRITICAL severity if non-empty/unexpected — preloads code into every dynamically-linked process; classic rootkit vector):**
```bash
ls -la /etc/ld.so.preload 2>/dev/null && cat /etc/ld.so.preload
```

**All platforms - shell rc backdoors (grep is a FIRST PASS ONLY — it catches crude curl/base64 droppers; patterns like `echo <base64> | base64 -d | python` evade it entirely, so manually review the rc files themselves before declaring clean):**
```bash
grep -nE "(curl|wget|nc -|base64|eval|python|perl)" ~/.zshrc ~/.bashrc ~/.profile ~/.zprofile 2>/dev/null
```

Distinguish errors: "no crontab" is normal; "permission denied" on your own account's files is itself a finding.

### Phase 4: Recent Activity

**Recently modified files:**
```bash
find ~ -maxdepth 3 -name "*.sh" -mtime -7
find ~ -maxdepth 2 -name "*.service" -mtime -7
find ~/Library/LaunchAgents -mtime -30 2>/dev/null
```

**SSH configuration:**
```bash
ls -la ~/.ssh/
grep -E "(command=|from=)" ~/.ssh/authorized_keys 2>/dev/null
# An authorized_keys entry with command= forces a specific command for that key — legitimate for automation
# (e.g., backup scripts, git servers) but is also a classic backdoor if you didn't add it
```

### Phase 5: IDE/AI Tool Analysis

**AI IDEs (platform-specific paths):**
```bash
# Antigravity IDE (macOS/Linux)
ls -la ~/.antigravity/extensions/

# Windsurf (Codeium)
ls -la ~/.codeium/windsurf/

# Cursor
ls -la ~/.cursor/

# Continue
ls -la ~/.continue/
```

**Browser native messaging hosts (common malware persistence vector on macOS):**
```bash
for d in "Google/Chrome" "Microsoft Edge" "Mozilla" "BraveSoftware/Brave-Browser" "Chromium"; do ls -la ~/Library/Application\ Support/$d/NativeMessagingHosts/ 2>/dev/null; done
```

See `reference/EXTENSIONS.md` for the full per-IDE audit checklist.

## Output Format

Provide findings in this structure:

### Summary
- Overall assessment (Clean / Suspicious / Compromised)
- Platform detected
- Number of items investigated
- Risk level (Low / Medium / High)

### Findings by Category
Classify every finding as `allowlisted` / `known-apple` / `unknown`. Only `unknown` items drive the risk level.
- **Processes**: List any suspicious processes with details
- **Network**: Document unexpected connections
- **Persistence**: List any persistence mechanisms found
- **Extensions**: Document unknown IDE extensions

### Recommendations
- Suggested actions (investigate further, remove, quarantine)
- Any items that warrant deeper analysis

## Structured Findings Log (diffable audits)

Alongside the prose report, write a JSONL log so consecutive audits can be diffed:

```bash
mkdir -p ~/.cache/live-system-forensics
# one line per finding; clean runs still write the file (zero unknown entries)
~/.cache/live-system-forensics/$(hostname)-$(date +%Y%m%d-%H%M).jsonl
```

Line schema:
```json
{"ts": "ISO-8601", "category": "persistence|process|network|extension|baseline", "item": "com.example.updater", "class": "allowlisted|known-apple|unknown", "severity": "low|med|high|critical", "note": "why this classification"}
```

Include *every* persistence item and unexplained process/destination — not just suspicious ones — so the log is a full inventory baseline.

**Drift check** (escalate in the report any unknown item not present last time):
```bash
cd ~/.cache/live-system-forensics && ls -t *.jsonl | head -2
diff <(jq -r 'select(.class=="unknown") | .item' <(newest) | sort) \
     <(jq -r 'select(.class=="unknown") | .item' <(previous) | sort)
```
No `jq`? `grep '"class":"unknown"' <file> | sed 's/.*"item":"\([^"]*\)".*/\1/' | sort` per file, then `comm -13`.

This is the one sanctioned write during recon — everything else stays read-only.

**Retention:** logs are pruned to `FORENSICS_LOG_KEEP` newest files (default 30) by the drift watcher (see `reference/SCHEDULED-BASELINE.md` for the opt-in scheduled baseline).

**Scheduled baseline (opt-in):** between full audits, `scripts/drift-watch.sh` can watch persistence drift with zero tokens — see `reference/SCHEDULED-BASELINE.md`. The skill never installs it itself.

## Security Considerations

- Always validate file paths before analysis
- Document all findings for incident response
- Use `trash` for any file removal, never `rm -rf`. On Linux without Homebrew `trash`: use `trash-cli` or `gio trash`; if no trash utility exists, move to a quarantine directory instead of deleting
- Obtain user consent before any remediation actions
- Don't modify system files without explicit permission
- Recon runs read-only by default; remediation is a separate, user-approved phase
