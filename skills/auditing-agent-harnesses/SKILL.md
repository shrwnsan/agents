---
name: auditing-agent-harnesses
description: Use when a new agent harness or AI-coding desktop app is installed on macOS, an already-audited harness ships a version update, a public claim about such an app needs verification, or a periodic harness privacy sweep is due. Applies to Electron/asar, Tauri, and thin-shell-plus-sidecar apps (ZCode, Conductor, Antigravity, Windsurf-class IDEs).
---

# Auditing Agent Harnesses

## Overview

Produce privacy/capability verdicts on agent-harness desktop apps that are **defensible in public**: every concern class explicitly cleared with evidence, coverage stated, confidence calibrated. This is a **coverage-contract skill** — it does not teach audit technique (byte sweeps, asar parsing, endpoint attribution are assumed competent; validated across 6 blind baselines in a 2026-09 audit campaign). What it enforces is that uncommon concern classes are *never silently skipped* — documented gaps in earlier unaudited rounds included the real update channel, credential file modes, and capture-API sweeps.

## Phase Flow

**Phase 0 — Identity.** Bundle id, version, codesign TeamID, notarization, `codesign --verify --deep --strict`. Hash-seal the exact bytes audited (the receipt line: `sha256 <first-16>…`).

**Phase 1 — Architecture discovery FIRST.** Find where executable logic actually lives before choosing a sweep method: Electron/asar (raw-byte scan, no unpack), Tauri/native Mach-O (strings sweep), or thin shell + sidecar/language_server (the sidecar is the app — sweep *it*). Never assume from vendor fame.

**Phase 2 — Nine concern classes.** Each must be explicitly cleared **with evidence** — a class not mentioned in the report is a class not audited:

| # | Class | Cleared means |
|---|---|---|
| C1 | Capture/surveillance APIs | ScreenCaptureKit/CGDisplayStream/CGEventTap/AVCaptureDevice swept; plist camera/mic strings traced to backing code or marked boilerplate |
| C2 | Telemetry attribution | Every SDK hit (sentry/posthog/segment/amplitude/clearcut) attributed vendored-lib vs app-wired; DSN/key present or absent; opt-out exists? account-tied? |
| C3 | Upload/ingest pipelines | Credential endpoints → envelope crypto → direct-to-storage chains; who holds decryption keys |
| C4 | Update channels — the REAL one | `app-update.yml`/stubs may be superseded by runtime pollers; enumerate pollers, CDNs, force-update hooks |
| C5 | Agent-binary redistribution | Bundled/downloaded agent CLIs: origin, who signs, signature verified |
| C6 | Credentials & sensitive data at rest | Keychain vs plaintext; **file modes** (world-readable = finding) |
| C7 | Persistence | LaunchAgents/Daemons, login items, shell hooks |
| C8 | Remote-exec / relay / tunnel surfaces | Standing WS relays, remote-command channels, ngrok/tunnel allowlists |
| C9 | Third-party extensions inside the host | Their own telemetry **and** self-installation into other tools (e.g. MCP registration into agent CLIs) |

**Phase 3 — Runtime corroboration.** Logs (sizes/mtimes for coverage), live sockets (`lsof +c0 -i -P -n`), data dirs, outbox/queue tables empty-or-not.

**Phase 4 — Verdict + persistence.** Verdict + coverage statement (`9/9 classes cleared`) + confidence + falsifiers ("what would make this wrong"). Persist: per-app guide in your docs repo (`guide-NNN` pattern: facts + regression recipe), memory entry, JSONL forensics log. Dual-run cross-validation (unscaffolded pair, one flash-tier) when the verdict goes public.

## Version-Jump Regression

For already-audited apps: re-grep the signature needles from the app's guide (e.g. ZCode: `upload-credential` + `rsa-oaep-sha256` + `RepoSnapshot`); sweep renamed variants; re-check C4 and C6 — update channels and file modes are where regressions and new exposures surface.

## Boundaries

- System-layer sweeps (processes/persistence/network of the whole machine) → `live-system-forensics`.
- Per-app facts and history → the app's `guide-NNN`, never this skill.
- Sweep technique (byte-window extraction, identifier traps, `grep -c` pitfalls) → in-weights; do not document here.
