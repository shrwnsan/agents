# Context-triage baseline for `auditing-agent-harnesses`

A labeled corpus and harness that measure whether TypeSafe's System One
API (jev-latest) can work as an **advisory** triage layer for
binary-audit context extraction. Result (2026-10-02): adopted as
advisory-only. It auto-resolves at confidence of 0.75 or higher and
escalates everything else. Any pipeline-shaped needle that scores benign
escalates regardless of confidence. The full rationale is in
`docs/research-002-context-triage-baseline.md`.

## Contents

- `corpus.jsonl` holds 24 labeled byte-window excerpts with the labels
  `benign-vendored`, `declared-telemetry`, `feature-wired`, and
  `pipeline-indicator`. They come from real desktop-app audit rounds,
  plus 7 synthetic positives reconstructed from public forensics
  (`synthetic: true`). The corpus includes hard negatives. One is a
  route-vocabulary list containing `upload-credential`/`snapshot`
  tokens, and the other is a size-limited feedback-attachment endpoint.
  Both are benign, and both share keywords with a real data-ingestion
  pipeline.
- `run.py` sends each context as `state` to
  `POST https://api.typesafe.ai/v1/systemone` with a two-question
  decision, a 4-way `choice` plus a `noul` upload-risk question. It
  scores the answers against the labels and reports accuracy and
  confidence calibration. It requires `TYPESAFE_API_KEY` in the
  environment and exits with `SKIP_REASON` when the key is absent. Set
  `TYPESAFE_BASE_URL` to point at a gateway or compatible endpoint. The
  threshold of 0.75 is **model-specific**, so re-run the harness before
  trusting it on any other model or provider.
- `results.json` is the run output for this corpus.

## Results (2026-10-02, jev-latest, 24/24 scored)

Raw accuracy was 0.79, and 0.857 on synthetic positives. There were
**0 pipeline false-clears**. Mean confidence was 0.866 when correct and
0.588 when wrong.

## Sanitization notice

This is a sanitized mirror. The canonical corpus lives in a private
repo, and changes reach this copy through a sanitization pass. One
value was replaced for publication. A **live Sentry DSN** (public key,
org, and project id) became a placeholder with the same shape. The
original value is withheld because a DSN is a write credential to a
vendor's crash-reporting project. All other contexts are verbatim. Two
of the 24 contexts are short excerpts from proprietary desktop-app
binaries, included as security-research evidence so the audit can be
reproduced. Trademarks and code remain the property of their
respective owners, and we will remove them on request.

## Threat model

According to the vendor's documentation, the model does not treat
`state` as hostile, so injected instructions can change its answers.
Audit inputs come from binaries that may be hostile. Jev triage is
therefore an advisory signal. It is never the verdict, and it never
replaces independent re-execution (dual-run) on public audit verdicts.
Adversarial-sample testing has not been done yet and is tracked as
follow-up.
