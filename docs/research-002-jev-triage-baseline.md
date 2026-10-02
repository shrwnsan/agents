# research-002: Jev as a context-triage layer for harness audits

**Date:** 2026-10-02
**Companion:** `evals/eval-024-jev-baseline/` (corpus + harness + results)

## Question

Can TypeSafe's System One model (Jev) absorb the judgment grind in
agent-harness privacy audits — classifying extracted binary byte-window
contexts as `benign-vendored` / `declared-telemetry` / `feature-wired` /
`pipeline-indicator` — without weakening verdict safety?

## What a skill user gets

- The noise grind disappears: in real audit rounds, most context hits are
  attribution false positives (`amplitude` = a PNG asset, `segment` =
  JPEG codec strings, `ngrok` = public-suffix list). Baseline auto-resolved
  ~19/24; the two real audits this corpus is drawn from each spent
  ~6–8 extraction round-trips and ~15–30K main-thread tokens on this class
  of work.
- A small escalation queue instead of full review: measured calibration
  (wrong ≈ 0.59 mean confidence, correct ≈ 0.87) makes the ≥0.75
  auto-resolve threshold meaningful.
- No safety regression by construction: zero pipeline false-clears in the
  baseline; anything pipeline-shaped scoring benign escalates regardless
  of confidence; verdict authority and dual-run cross-validation are
  untouched.
- ~$0.002/audit, seconds of latency: parity in dollars on flash-tier
  sessions (real win there: context-window budget and fewer round-trips),
  ~30–300× cheaper on the triage slice for premium-tier main threads.

## Verdict

Adopted as an **optional, advisory** Phase-2 accelerator in
`skills/auditing-agent-harnesses` (PR #64). It is not an implementation
inside the skill — the skill instructs the agent to use the harness in
`evals/eval-024-jev-baseline/` when `TYPESAFE_API_KEY` is present and to
skip cleanly when absent. Jev is not served by OpenAI-shaped aggregators
(OpenRouter, Vercel AI Gateway): the System One API has its own protocol;
`run.py` accepts `TYPESAFE_BASE_URL` for a future compat endpoint, and
the measured threshold is model-specific until re-run on another model.

## Limits

- Never the verdict: the baseline itself contains a 0.95-confidence
  over-flag (a sample-env template string classified as live telemetry —
  safe direction, but proof that confidence ≠ correctness).
- Vendor-documented injected-instruction risk on hostile `state`; audit
  inputs are potentially hostile binaries. Adversarial-sample testing is
  pending.
- Two of five baseline "misses" were label-taxonomy errors on our side
  (the model's answer was defensible), so raw accuracy understates
  agreement.
