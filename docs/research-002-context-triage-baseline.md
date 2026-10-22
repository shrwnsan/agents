# research-002: context triage for agent-harness audits with the System One API, measured on jev-latest

**Date:** 2026-10-02
**Companion:** `evals/context-triage-baseline/` (corpus, harness, and results)

## Question

Can TypeSafe's System One model (Jev) take over the repetitive judgment
work in agent-harness privacy audits without weakening verdict safety?
That work is classifying byte-window contexts extracted from binaries as
`benign-vendored`, `declared-telemetry`, `feature-wired`, or
`pipeline-indicator`.

## What a skill user gets

- Less manual triage of noise. In real audit rounds, most context hits
  are attribution false positives. The `amplitude` hit came from a PNG
  asset, `segment` from JPEG codec strings, and `ngrok` from the
  public-suffix list. The baseline auto-resolved about 19 of 24. The two
  real audits this corpus comes from each spent about 6 to 8 extraction
  round-trips and about 15K to 30K main-thread tokens on this class of
  work.
- A small escalation queue instead of full review. The measured
  confidence is calibrated. Wrong answers averaged about 0.59 confidence
  and correct ones about 0.87, which makes an auto-resolve threshold of
  0.75 or higher meaningful.
- No safety regression by construction. The baseline had zero pipeline
  false-clears. Anything pipeline-shaped that scores benign escalates
  regardless of confidence. Verdict authority and dual-run
  cross-validation are untouched.
- About $0.002 per audit, with seconds of latency. On flash-tier
  sessions the dollar cost is about the same, and the real gains are
  context-window budget and fewer round-trips. For premium-tier main
  threads, the triage slice is about 30 to 300 times cheaper.

## Verdict

Adopted as an **optional, advisory** Phase-2 accelerator in
`skills/auditing-agent-harnesses` (PR #64). The skill does not contain
an implementation. It instructs the agent to use the harness in
`evals/context-triage-baseline/` when `TYPESAFE_API_KEY` is present and
to skip cleanly when it is absent. OpenAI-compatible aggregators such as
OpenRouter and Vercel AI Gateway do not serve Jev, because the System
One API has its own protocol. `run.py` accepts `TYPESAFE_BASE_URL` for a
future compatible endpoint. The measured threshold applies only to this
model until someone re-runs the eval on another model.

## Limits

- Jev is never the verdict. The baseline itself contains an over-flag at
  0.95 confidence, where the model classified a sample-env template
  string as live telemetry. The error is in the safe direction, but it
  shows that high confidence does not mean a correct answer.
- The vendor documents a risk of injected instructions in hostile
  `state`, and audit inputs may be hostile binaries. Adversarial-sample
  testing is pending.
- Two of the five baseline "misses" were errors in our label taxonomy,
  and the model's answer was defensible. Raw accuracy therefore
  understates agreement.
