# Context-triage corpus and baseline for `auditing-agent-harnesses`

A labeled corpus and harness that measure whether TypeSafe's System One
API (jev-latest) can work as an **advisory** triage layer for
binary-audit context extraction. Measured results (per run) are in the
Results section below; each receipt pins the resolved model version in
its rows, since "jev-latest" is a moving alias. Adopted as
advisory-only. It auto-resolves at confidence of 0.75 or higher and
escalates everything else. A pipeline-shaped context auto-resolves only
when Jev reads it as a pipeline; any other class escalates regardless of
confidence. The full rationale is in
[docs/research-002-context-triage-baseline.md](https://github.com/shrwnsan/agents/blob/main/docs/research-002-context-triage-baseline.md)
(in the skill's source repo).

## Contents

- `../assets/corpus.jsonl` holds 25 labeled byte-window excerpts with
  the labels `benign-vendored`, `declared-telemetry`, `feature-wired`,
  and `pipeline-indicator`. They come from real desktop-app audit
  rounds, plus 7 synthetic positives reconstructed from public
  forensics (`synthetic: true`). All seven synthetic positives now carry
  `pipeline_shaped: true`, matching the corrected canonical annotations.
  Only those flags changed; context text is unchanged. The corpus includes hard negatives:
  a route-vocabulary list containing `upload-credential`/`snapshot`
  tokens, a size-limited feedback-attachment endpoint, and a
  request-body masking function. All are benign, and all share keywords
  with a real data-ingestion pipeline; they carry
  `pipeline_shaped: true`, and the gate escalates any of them that scores
  as anything other than a pipeline, regardless of confidence. Added 2026-10-23:
  `zcode-3163-capture-repo-snapshot` — a pipeline-shaped name on a dead
  flag (the function never reads the argument), trimmed to the
  attributed construct.
- `../scripts/context-triage.py` sends each context as `state` to
  `POST https://api.typesafe.ai/v1/systemone` with a two-question
  decision, a 4-way `choice` plus a `noul` upload-risk question, and
  enforces the gate in code. Scoring requires `TYPESAFE_API_KEY` in the
  environment and exits with `SKIP_REASON` when the key is absent; the
  `probe` mode needs no key. Set `TYPESAFE_BASE_URL` to point at a
  gateway or compatible endpoint. Receipts default to the current working
  directory with a timestamped name (`.jsonl` in contexts mode); a
  default path that would land inside the skill directory relocates to
  TMPDIR with a stderr note, and an `--out` inside the skill directory
  is refused.
- `baseline-results.json` (this directory) is the latest baseline
  receipt. It is refreshed by re-running `context-triage.py baseline
  --out references/baseline-results.json --force` whenever the corpus or
  the model changes; earlier receipts remain in git history.
  The pinned receipt dates from the 1.2.x harness: its per-row `gate`
  column applies the pre-1.3.0 rule, so `zcode-feedback-attachment`
  (pipeline-shaped, read as `feature-wired` at 0.99) shows
  `auto-resolve` where the 1.3.0 gate escalates, and its summary
  predates the `pipeline_shaped_missed` field. Its rows are the
  measurement record of the 2026-11-03 run, and rewriting the gate
  column would falsify that record; regenerate it with the 1.3.0
  harness on the next model change. The seven synthetic positives were
  unflagged in that run; their current corpus flags do not alter the
  historical receipt.

## Rules

- Trim extracted windows to the attributed construct before scoring. A
  window that bleeds into neighboring code shifts labels (the
  feedback-masker window that includes the upload client reads
  `feature-wired`; the masker alone is `benign-vendored`).
- Mark any context that packages, encrypts, or uploads user material
  `pipeline_shaped: true`. The flag defaults to false, and the harness
  prints a stderr warning naming the rows that omit it, because the
  broadened rule cannot fire on a context it cannot see.
- The threshold of 0.75 is **model-specific**, so re-run the harness
  before trusting it on any other model or provider.
- Single-shot confidences drift between identical runs (2026-11-02: 15/25
  items, two crossings of the 0.75 line). In `contexts` mode the harness
  re-scores once when a confidence lands in the 0.70–0.80 band (0.70
  inclusive, 0.80 exclusive) and keeps the lower-confidence answer; a
  re-score that flips the class escalates the context regardless of
  confidence. `baseline --reps N` uses majority
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
  0.28 — label-agreeing, and escalated by the confidence threshold
  (0.28 < 0.75); the regardless-of-confidence rule was a backstop that
  never fired, so the safety invariant held: no pipeline-shaped needle
  auto-resolved.
- 2026-11-02, jev-1.14.0 (alias unchanged), 25/25 scored across three runs
  (two single-shot pre-refactor, one pinned from the 1.2.0 harness): raw
  accuracy 0.80 in all three on the same misclassification set. The one
  near-miss was not a false-clear but the opposite-shaped hazard:
  `syn-capture-stage`, a synthetic pipeline positive (not flagged
  `pipeline_shaped` at the time), read as `feature-wired` at 0.61–0.71 — under the
  0.75 line, so the threshold caught it, by a margin smaller than the
  measured drift. That near-miss motivated the 1.3.0 broadening of the
  pipeline rule. Version 1.3.1 flags all seven synthetic positives in
  the corpus so that rule applies to them. `baseline` still warns about
  any unflagged pipeline positives in other input corpora. Run-to-run confidence drift
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
