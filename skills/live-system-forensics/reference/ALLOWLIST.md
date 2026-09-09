# Per-Host Allowlist

This file is **machine-specific** and **user-maintained**. It lists persistence items, processes, network destinations, and extensions verified as legitimate on *this* host.

> **This shipped copy is a template — it ships empty by design.** Populate it from your own host's first clean audit, and never publish your real entries: your allowlist documents your VPN stack, messaging channels, tooling, and infrastructure. Treat it as sensitive.

**Rules:**
- After every audit that comes back clean, add any new legitimate items you verified here.
- During an audit, classify every finding as: `allowlisted` (in this file) / `known-apple` (Apple-stock, under /System) / `unknown` (investigate).
- Anything not in this file and not vendor-stock = investigate, not ignore.
- Porting this skill to a new machine? Reset this file to empty and rebuild it from that host's first clean audit.

**Integrity limitation:** this file is not cryptographically protected. An attacker with your UID can append their malware's label here to bypass classification. Verify allowlist changes between audits (`git -C ~/.claude/skills diff live-system-forensics/reference/ALLOWLIST.md`) and treat unexplained allowlist growth as a high-severity finding.

## LaunchAgents / LaunchDaemons

| Label | Location | Notes |
|-------|----------|-------|
| _(empty — populate from your first clean audit)_ | | |
| com.example.updater | ~/Library/LaunchAgents | EXAMPLE row — vendor update agent; replace with your own verified items |

## Processes

| Process | Path | Notes |
|---------|------|-------|
| _(empty)_ | | |

## Network destinations

| Process | Destination | Notes |
|---------|-------------|-------|
| _(empty)_ | | |

## Systemd units (Linux hosts)

| Unit | Notes |
|------|-------|
| _(none — populate per Linux host)_ | |

## IDE / browser extensions

| Extension | Publisher | Notes |
|-----------|-----------|-------|
| _(empty — populate from your first audit)_ | | |
