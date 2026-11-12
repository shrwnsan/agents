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

## What a round produces

A round closes with: a verdict and a coverage statement (every concern
class, evidence per class) plus falsifiers; a JSONL forensics receipt in a
durable location; one validated coverage-ledger line per app; and an update
to the app's guide. Public verdicts additionally require a dual-run
reproducer following the mechanical contract in
`references/dual-run-prompt-template.md`.

## Layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Operational contract: phases, concern classes, gates |
| `scripts/context-triage.py` | Context-triage harness (probe + baseline + contexts modes) |
| `scripts/ledger-check.py` | Enum-locks the per-round coverage ledger (Phase 4 artifact) |
| `scripts/generate-coverage-table.py` | Renders a ledger as the guide's coverage table (build artifact) |
| `scripts/tests/` | Offline tests for the harness and ledger tooling (no API key) |
| `assets/corpus.jsonl` | 25 labeled byte-window excerpts (sanitized mirror) |
| `references/corpus-README.md` | Corpus contents, rules, results, sanitization, threat model |
| `references/dual-run-prompt-template.md` | Mechanical contract for the unscaffolded dual-run reproducer |
| `references/baseline-results.json` | Latest baseline receipt (refreshed by re-running the harness) |

## Coverage ledger (since 1.4.0)

Each audit round appends one validated JSONL line to the app's ledger file
(`docs/guides/ledger/<app>.jsonl` in the docs repo): validation level
(dual-run / solo / multi-agent / carryover with source round), per-class
coverage with staleness dates (`evidence`, `carryover:<round_date>`, `n/a`),
and per-window Jev outcomes with the gate rule that decided them.
`scripts/ledger-check.py` enum-locks this schema at round close; a round
whose ledger line fails the check is not closed. Coverage tables in the
app guide are generated from the ledger by
`scripts/generate-coverage-table.py` and are build artifacts: regenerate,
never hand-edit. The ledger is the only hand-written record; a class
without a ledger line is a class not audited.

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
| 2026-11-02 | jev-1.14.0 | 25/25 | 0.80 | 0.816 | 0.666 | 1 (escalated) |

The 2026-10-23 false-clear is `zcode-route-vocab` scoring `benign-vendored`
at 0.28. What actually escalated it was the confidence threshold
(0.28 < 0.75); the regardless-of-confidence rule was a backstop that never
fired, a distinction that matters once drift pushes such reads upward. The
2026-10-23 re-run held accuracy
but narrowed the correct/wrong
confidence spread, so calibration is treated as **drifting**: re-run
`context-triage.py baseline` on every model update. The ≥0.75
auto-resolve threshold is model-specific and applies only to
jev-latest until re-measured.

The 2026-11-02 runs (two single-shot pre-refactor runs plus the pinned run
from the 1.2.0 harness) held accuracy at 0.80 on the same misclassification
set, and the jev-1.14.0 alias did not move. Identical single-shot runs
differed in confidence on 15/25 items (drift 0.03–0.11) and two items
crossed the 0.75 line without changing class, so single-shot auto-resolve
has a live boundary band: `contexts` now re-scores once inside 0.70–0.80
and keeps the lower-confidence answer, and `baseline --reps N` scores with
majority prediction and the median of its confidences. The stable hard
cases are documented in the corpus results.

Harness 1.3.0 (2026-11-09) broadened the pipeline rule: a pipeline-shaped
context now escalates on any read other than `pipeline-indicator`, at any
confidence. The trigger was a near-miss in the other direction: a real
pipeline positive (`syn-capture-stage`) read as `feature-wired` at
0.61–0.71 across the 2026-10-26 and 2026-11-02 runs, under the line but by
a margin smaller than the measured drift. The same release escalates on a
confirm-band class flip, warns on stderr when a row omits
`pipeline_shaped`, refuses `--out` inside the skill directory, and
rejects malformed input rows before any receipt is written.

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

## Operational caveats

- `codesign --verify --deep --strict` and `spctl` can be sandbox-blocked
  in some agent sessions. Record the gap in the round receipt and carry
  the last passing check forward with its date.
- Accelerator egress to api.typesafe.ai varies by session. `probe` settles
  it with one unauthenticated request before a scored run.
- The 0.75 auto-resolve threshold rides a moving model alias. Re-run
  `baseline` on every model update; receipts pin the resolved version.
- Audit needles must match document language. The 2026-11-12
  privacy-policy check false-negatived on English keywords against a
  Chinese-language policy; search in the vendor's language.

## Versions

- 1.4.0 (#145): coverage ledger, `ledger-check.py` round-close check, coverage-table generator.
- 1.3.1 (#143): `pipeline_shaped` on every synthetic pipeline row; offline regression tests.
- 1.3.0 (#132): broadened pipeline gate (any non-pipeline read escalates regardless of confidence), confirm-band class-flip escalation, stricter receipts and input rows.
- 1.2.1 (#128, #130): dual-run template counts positions, not lines; corrected the Local Network worked example.
- 1.2.0 (#115): probe mode, `TYPESAFE_MODEL` override, confirm-band re-scoring, dual-run prompt template, durable forensics-log convention.
- 1.1.0 (#100): harness and corpus packaged into the skill; portable provenance and `metadata.version`.
- 1.0.0: coverage-contract phases and the advisory context-triage baseline ([docs/research-002](https://github.com/shrwnsan/agents/blob/main/docs/research-002-context-triage-baseline.md)).
