# eval-024: context-triage baseline for `auditing-agent-harnesses`

Labeled corpus + harness for measuring whether TypeSafe's System One API
(jev-latest) can serve as an **advisory** triage layer for binary-audit
context extraction. Result (2026-10-02): adopted as advisory-only —
auto-resolve at confidence ≥ 0.75, escalate everything else, and any
pipeline-shaped needle that scores benign escalates regardless of
confidence. Full rationale: `docs/research-002-context-triage-baseline.md`.

## Contents

- `corpus.jsonl` — 24 labeled byte-window excerpts (labels:
  `benign-vendored` | `declared-telemetry` | `feature-wired` |
  `pipeline-indicator`), drawn from real desktop-app audit rounds plus 7
  synthetic positives reconstructed from public forensics (`synthetic:
  true`). Includes hard negatives: a route-vocabulary list containing
  `upload-credential`/`snapshot` tokens, and a size-limited
  feedback-attachment endpoint — both benign, both keyword-colliding
  with a real data-ingestion pipeline.
- `run.py` — sends each context as `state` to
  `POST https://api.typesafe.ai/v1/systemone` with a two-question
  decision (4-way `choice` + `noul` upload-risk), scores against labels,
  reports accuracy + confidence calibration. Requires `TYPESAFE_API_KEY`
  in the environment; exits with `SKIP_REASON` when absent. Override
  `TYPESAFE_BASE_URL` to point at a gateway or compat endpoint — note
  the ≥0.75 threshold is **model-specific**; re-run the harness before
  trusting it on any other model or provider.
- `results.json` — the run output for this corpus.

## Results (2026-10-02, jev-latest, 24/24 scored)

0.79 raw accuracy (0.857 on synthetic positives) · **0 pipeline
false-clears** · mean confidence 0.866 when correct vs 0.588 when wrong.

## Sanitization notice

This is a sanitized mirror. Canonical corpus lives in a private repo;
changes propagate through a sanitization pass. One substitution was made
for publication: a **live Sentry DSN** (public key + org + project id)
was replaced with a same-shape placeholder. The original value is
withheld — a DSN is a write credential to a vendor's crash-reporting
project. All other contexts are verbatim. Two of the 24 contexts are
short excerpts from proprietary desktop-app binaries, included as
security-research evidence for audit reproducibility; trademarks and
code remain property of their respective owners — removal on request.

## Threat model

Per vendor documentation, the model does not treat `state` as hostile —
injected instructions can move answers — and audit inputs come from
potentially hostile binaries. Jev triage is therefore advisory signal,
never the verdict, and never a replacement for independent re-execution
(dual-run) on public audit verdicts. Adversarial-sample testing is
untested and tracked as follow-up.
