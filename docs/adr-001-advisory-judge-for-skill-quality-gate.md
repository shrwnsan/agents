# ADR-001: Advisory judge for skill-quality-gate

**Status:** Proposed — 2026-10-02
**Deciders:** shrwnsan, Telegram Main

## Context

`skills/skill-quality-gate` is deliberately deterministic: "same input, same findings — unlike unaided review, where two reviewers check different things and both miss the same trap." Two judgment gaps survive the deterministic phases:

1. **Borderline severity** — findings the scripts can flag but not classify (WARN vs FAIL calls, e.g. a subshell pattern that is either clever or unsafe depending on context).
2. **False advertising** — a description that claims behavior the code does not implement. Today this is caught only by the behavioral dry-run, and only when the claim affects the canary path.

Meanwhile `recipes/model-bakeoff-gate` ships a layered decision protocol in `guard.py` + `lab.py`: deterministic checks decide what math can decide; a model judge (Jev) sees only soft signals that already passed the math; "uncertain" resolves to human review; keyless runs fail closed with a visible fail-safe (exit ladder 0/1/2/3, never a silent skip).

Question raised in review of the sandboxed-run PR (#62): should skills like the gate integrate decision models like Jev?

## Decision

Yes — but **outside the default verdict path**. The gate gains an opt-in `--judge` deep-audit phase that mirrors Jev's protocol:

1. **Deterministic phases run first, unchanged.** Only their flagged-borderline output (WARN findings, plus description-claim-vs-code suspicions the structure scan can surface) is eligible for judgment.
2. **Structured question, structured answer.** The judge receives the finding, the evidence, and the gate criteria; it returns a structured choice — `fail` / `warn` / `uncertain` — with a reason. Free-text verdicts are rejected.
3. **The judge can neither FAIL what the math passed nor PASS a FAIL.** It may move eligible findings between WARN and FAIL-flagged-for-human; `uncertain` always resolves to human review.
4. **Pin and log.** Judge model + version recorded in the report file next to each verdict (the repo's pin-and-record rule applies to judge models too).
5. **Fail closed, never silent.** No key, no judge: the phase reports `judge: unavailable` and the gate verdict stands on the deterministic phases alone.
6. **Opt-in only.** The default gate stays fast, keyless-friendly, and reproducible; `--judge` is for release-grade audits of third-party skills, not the everyday pre-flight.

## Consequences

- Default path keeps its contract: reproducible, cheap enough to run always.
- Cost and latency appear only when opted in; verdicts remain auditable via the logged judge output.
- False advertising gains a static detection path instead of relying solely on canary luck.
- The judge's model pin becomes part of the report — bumping it is a deliberate act.

## Alternatives considered

- **Judge inside the default verdict path** — rejected: a model in the PASS/FAIL path kills reproducibility (the gate's entire reason to exist) and per-run cost breaks "cheap gate, run always".
- **Port Jev's code directly** — rejected: it is domain-bound (commits, worktrees, cherry equivalences). Port the protocol shape — deterministic core, judgment only on what passes the math, uncertain → human, fail closed — not the code.
- **Do nothing** — rejected: borderline-severity calls would stay ad hoc forever, and false advertising would remain behavioral-luck.

## Related

- `skills/skill-quality-gate/` — the gate this extends
- `recipes/model-bakeoff-gate/` — source of the protocol (guard.py exit ladder, lab.py judge client)
- `skills/sandboxed-run/` — complementary: contains *execution*; the judge contains *verdicts*. Neither substitutes for the other.
