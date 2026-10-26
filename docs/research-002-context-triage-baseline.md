# research-002: context triage for agent-harness audits with the System One API, measured on jev-latest

**Date:** 2026-10-02
**Companion:** `skills/auditing-agent-harnesses` (corpus in `assets/`, harness in
`scripts/`, baseline results in `references/`)

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
`skills/auditing-agent-harnesses` (PR #64). The skill ships the harness
itself (PR #95): `scripts/context-triage.py`, with the corpus in
`assets/corpus.jsonl`. It instructs the agent to use the harness when
`TYPESAFE_API_KEY` is present and to skip cleanly when it is absent.
OpenAI-compatible aggregators such as OpenRouter and Vercel AI Gateway
do not serve Jev, because the System One API has its own protocol. The
harness accepts `TYPESAFE_BASE_URL` for a future compatible endpoint. The measured threshold applies only to this
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

## Skill provenance

History for the `auditing-agent-harnesses` skill itself, kept out of the
portable package — PR numbers and campaign details mean nothing to a
user who installed the skill on its own:

- The skill came out of a 2026-09 audit campaign across six blind
  baselines. The failure mode it targets was observed directly: earlier
  unaudited rounds had missed the real update channel (C4), credential
  file modes (C6), and capture-API sweeps (C1).
- PR #64 (2026-10-04) added the skill. PR #95 made it self-contained —
  harness in `scripts/`, corpus in `assets/`, receipts and corpus README
  in `references/`; #98 removed the last `docs/evals` leftovers; #99
  added the README context split, pinned measured model versions
  (jev-1.13.0, jev-1.14.0), and gate-review fixes.
- The public corpus inside the skill is the sanitized mirror; the
  unsanitized canonical lives in a private repo (see the sanitization
  notice in the skill's `references/corpus-README.md`).
- `metadata.version` in the skill's frontmatter is the package label;
  bump it in the same PR as any skill-content change. Git history and
  the PR numbers above remain the real changelog.
