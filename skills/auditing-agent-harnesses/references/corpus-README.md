# Context-triage corpus and baseline for `auditing-agent-harnesses`

A labeled corpus and harness that measure whether TypeSafe's System One
API (jev-latest) can work as an **advisory** triage layer for
binary-audit context extraction. Measured results (per run) are in the
Results section below; each receipt pins the resolved model version in
its rows, since "jev-latest" is a moving alias. Adopted as
advisory-only. It auto-resolves at confidence of 0.75 or higher and
escalates everything else. Any pipeline-shaped needle that scores benign
escalates regardless of confidence. The full rationale is in
[docs/research-002-context-triage-baseline.md](https://github.com/shrwnsan/agents/blob/main/docs/research-002-context-triage-baseline.md)
(in the skill's source repo).

## Contents

- `../assets/corpus.jsonl` holds 25 labeled byte-window excerpts with
  the labels `benign-vendored`, `declared-telemetry`, `feature-wired`,
  and `pipeline-indicator`. They come from real desktop-app audit
  rounds, plus 7 synthetic positives reconstructed from public
  forensics (`synthetic: true`). The corpus includes hard negatives:
  a route-vocabulary list containing `upload-credential`/`snapshot`
  tokens, a size-limited feedback-attachment endpoint, and a
  request-body masking function. All are benign, and all share keywords
  with a real data-ingestion pipeline; they carry
  `pipeline_shaped: true`, and the gate escalates any of them scoring
  benign regardless of confidence. Added 2026-10-23:
  `zcode-3163-capture-repo-snapshot` — a pipeline-shaped name on a dead
  flag (the function never reads the argument), trimmed to the
  attributed construct.
- `../scripts/context-triage.py` sends each context as `state` to
  `POST https://api.typesafe.ai/v1/systemone` with a two-question
  decision, a 4-way `choice` plus a `noul` upload-risk question, and
  enforces the gate in code. It requires `TYPESAFE_API_KEY` in the
  environment and exits with `SKIP_REASON` when the key is absent. Set
  `TYPESAFE_BASE_URL` to point at a gateway or compatible endpoint.
  Receipts default to the current working directory with a timestamped
  name (never inside the skill directory); pass `--out` for an explicit
  destination.
- `baseline-results.json` (this directory) is the latest baseline
  receipt. It is refreshed by re-running `context-triage.py baseline
  --out references/baseline-results.json --force` whenever the corpus or
  the model changes; earlier receipts remain in git history.

## Rules

- Trim extracted windows to the attributed construct before scoring. A
  window that bleeds into neighboring code shifts labels (the
  feedback-masker window that includes the upload client reads
  `feature-wired`; the masker alone is `benign-vendored`).
- The threshold of 0.75 is **model-specific**, so re-run the harness
  before trusting it on any other model or provider.
- Single-shot confidences drift between identical runs (2026-11-02: 15/25
  items, two crossings of the 0.75 line). In `contexts` mode the harness
  re-scores once when a confidence lands in the 0.70–0.80 band and keeps
  the lower-confidence answer; `baseline --reps N` uses majority
  prediction and the median of its confidences. Receipts carry the
  resolved model per row in both modes, and `TYPESAFE_MODEL` overrides
  the requested alias.

## Results

- 2026-10-02, jev-1.13.0 ("jev-latest" at the time), 24/24 scored: raw
  accuracy 0.79, 6/7 on synthetic positives, **0 pipeline false-clears**,
  mean confidence 0.866 when correct and 0.588 when wrong.
- 2026-10-23, jev-1.14.0 ("jev-latest" at the time), 25/25 scored: raw
  accuracy 0.80, 6/7 on synthetic positives, mean confidence 0.82 when
  correct and 0.698 when wrong — the correct/wrong confidence spread
  narrowed versus 2026-10-02, so treat calibration as drifting and
  re-run `baseline` per model update. 14 contexts auto-resolved, 11
  escalated. The one
  wrong auto-resolve was `zcode-sentry-placeholder` read as
  `declared-telemetry` at 0.91 (a known hard case: a sample-env
  placeholder DSN). `zcode-route-vocab` scored `benign-vendored` at
  0.28 — label-agreeing, but escalated by the
  regardless-of-confidence rule, so the safety invariant held: no
  pipeline-shaped needle auto-resolved.
- 2026-11-02, jev-1.14.0 (alias unchanged), 25/25 scored across three runs
  (two single-shot pre-refactor, one pinned from the 1.2.0 harness): raw
  accuracy 0.80 in all three on the same misclassification set, 1
  pipeline-shaped false-clear (`syn-capture-stage`, 0.61–0.68, escalated —
  the safety invariant held in every run). Run-to-run confidence drift
  touched 15/25 items (0.03–0.11) and crossed the 0.75 threshold on two
  items without changing class, which motivated the confirm-band rule
  below. Stable hard cases, all in the safe direction: the feedback-masker
  read as `feature-wired` at 0.61–0.72 (exactly the reading the trim rule
  above predicts for the neighboring-client window), the sentry
  placeholder read as `declared-telemetry` at 0.91–0.95, and the shadcn
  and capture-stage entries at 0.65–0.69.

## Sanitization notice

This corpus is a sanitized mirror. The canonical corpus lives in a
private repo, and changes reach this copy through a sanitization pass.
One value was replaced for publication. A **live Sentry DSN** (public
key, org, and project id) became a placeholder with the same shape. The
original value is withheld because a DSN is a write credential to a
vendor's crash-reporting project. All other contexts are verbatim.
Eighteen of the 25 contexts are short excerpts from the shipped
binaries of two proprietary desktop apps, included as
security-research evidence so the audit can be reproduced. Trademarks
and code remain the property of their respective owners, and we will
remove them on request.

## Threat model

According to the vendor's documentation, the model does not treat
`state` as hostile, so injected instructions can change its answers.
Audit inputs come from binaries that may be hostile. Jev triage is
therefore an advisory signal. It is never the verdict, and it never
replaces independent re-execution (dual-run) on public audit verdicts.
Adversarial-sample testing has not been done yet and is tracked as
follow-up.
