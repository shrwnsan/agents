# auditing-agent-harnesses

Privacy/capability audits for agent-harness desktop apps (Electron/asar,
Tauri, thin-shell-plus-sidecar) on macOS, producing verdicts that are
defensible in public. The operational contract lives in
[`SKILL.md`](SKILL.md); this README carries the background, history, and
measured results that an agent does not need at audit time.

## Background

The skill is a **coverage-contract skill**: it does not teach audit
technique (byte sweeps, asar parsing, endpoint attribution are assumed
competent). It exists because the failure mode of real audit rounds was
silent omission — earlier rounds missed the real update channel (C4),
credential file modes (C6), and capture-API sweeps (C1) before the
coverage rule existed. Provenance and validation history (six blind
baselines, adoption timeline):
[docs/research-002](https://github.com/shrwnsan/agents/blob/main/docs/research-002-context-triage-baseline.md).

## Layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Operational contract: phases, concern classes, gates |
| `scripts/context-triage.py` | Context-triage harness (baseline + contexts modes) |
| `assets/corpus.jsonl` | 25 labeled byte-window excerpts (sanitized mirror) |
| `references/corpus-README.md` | Corpus contents, rules, results, sanitization, threat model |
| `references/baseline-results.json` | Latest baseline receipt (refreshed by re-running the harness) |

## Context-triage accelerator: history and results

The context-triage layer was adopted on 2026-10-02 as an **optional,
advisory** Phase-2 accelerator. Payoff: the false-positive attribution
grind disappears — the baseline auto-resolved about 19 of 24 contexts,
absorbing the ~6–8 extraction round-trips and ~15–30K main-thread
tokens a real audit spends on noise, at about $0.002 per audit.

Measured baselines (jev-latest is a moving alias; each receipt pins the
resolved version in its rows):

| Date | Model | Scored | Raw accuracy | Mean conf (correct) | Mean conf (wrong) | Pipeline false-clears |
|---|---|---|---|---|---|---|
| 2026-10-02 | jev-1.13.0 | 24/24 | 0.79 | 0.866 | 0.588 | 0 |
| 2026-10-23 | jev-1.14.0 | 25/25 | 0.80 | 0.82 | 0.698 | 1 (escalated) |

The 2026-10-23 false-clear is `zcode-route-vocab` scoring `benign-vendored`
at 0.28 — the regardless-of-confidence rule escalated it, so no
pipeline-shaped needle auto-resolved. The 2026-10-23 re-run held accuracy
but narrowed the correct/wrong
confidence spread, so calibration is treated as **drifting**: re-run
`context-triage.py baseline` on every model update. The ≥0.75
auto-resolve threshold is model-specific and applies only to
jev-latest until re-measured.

Why advisory only: the model produced a 0.95-confidence error on its
own baseline (a sample-env placeholder DSN read as live telemetry),
and the vendor documents that `state` is not treated as hostile —
injected instructions can move the answer — while audit inputs come
from potentially hostile binaries. Jev never issues the verdict and
never replaces the dual-run cross-validation on public verdicts.

Adversarial-sample testing has not been done yet and is tracked as
follow-up. Full corpus details, sanitization notice, and per-context
results: [`references/corpus-README.md`](references/corpus-README.md)
and `references/baseline-results.json`.
