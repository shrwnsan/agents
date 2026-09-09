# Live System Forensics

Perform live forensic analysis on Unix systems to detect malware and suspicious activity.

## Features

- **Process Analysis**: Identify running processes and detect anomalies
- **Network Inspection**: Analyze active network connections
- **Persistence Detection**: Audit startup items (systemd, LaunchAgents, cron)
- **Recent Activity**: Find recently modified files and scripts
- **IDE Extension Audit**: Examine AI IDE extensions (Antigravity, Cursor, etc.)

## Supported Platforms

- macOS (LaunchAgents, LaunchDaemons)
- Linux (systemd, cron)
- WSL (systemd, cron + Windows interop)

## Installation

Copy (or symlink) this directory into your agent's skills directory. The repo follows the `~/.agents/skills/` convention; Claude Code users should symlink or copy to `~/.claude/skills/`:

```bash
git clone https://github.com/shrwnsan/agents.git
mkdir -p ~/.agents/skills
cp -R agents/skills/live-system-forensics ~/.agents/skills/
# Claude Code users:
ln -s ~/.agents/skills ~/.claude/skills   # one-time symlink, or: cp -R ~/.agents/skills/* ~/.claude/skills/
```

Restart your agent to pick up the new skill. `reference/ALLOWLIST.md` ships as an empty template — populate it from your first clean audit, and keep your real entries private.

## Usage

When you want to analyze your system for suspicious activity:

```
Analyze my system for malware
Check for suspicious processes
Audit startup items
Investigate Antigravity IDE
Check system security
```

## Requirements

- Unix-like system (macOS, Linux, WSL)
- Read access to standard directories (~, /Library, /etc)
- Standard Unix utilities (ps, lsof, ls, systemctl on Linux)
