# ADR-001: Advisory judge for skill-quality-gate

**Status:** Proposed, 2026-10-02
**Deciders:** shrwnsan, Telegram Main

## Context

`skills/skill-quality-gate` is deterministic by design: "same input, same findings — unlike unaided review, where two reviewers check different things and both miss the same trap." Two judgment gaps remain after the deterministic phases:

1. **Borderline severity.** The scripts can flag these findings but not classify them as WARN or FAIL. An example is a subshell pattern that is either clever or unsafe depending on context.
2. **False advertising.** A description claims behavior the code does not implement. Today only the behavioral dry-run catches this, and only when the claim affects the canary path.

Meanwhile `recipes/model-bakeoff-gate` ships a layered decision protocol in `guard.py` and `lab.py`. Deterministic checks decide what math can decide. A model judge (Jev) sees only soft signals that already passed the math. An "uncertain" answer goes to human review. Runs without a key fail closed with a visible fail-safe, using an exit ladder from 0 to 4, and never skip silently.

The question came up in review of the sandboxed-run PR (#62). Should skills like the gate integrate decision models like Jev?

## Decision

Yes, but **outside the default verdict path**. The gate gains an opt-in `--judge` deep-audit phase that follows Jev's protocol:

1. **Deterministic phases run first, unchanged.** Only their borderline output is eligible for judgment. That means WARN findings, plus suspicions from the honesty pass (checklist step 6) that a description claims something the code does not do. The honesty pass is manual today. A static claim-vs-code scan inside `check_structure.py` does not exist yet. It is a prerequisite for automating this input, not an existing capability.
2. **Structured question, structured answer.** The judge receives the finding, the evidence, and the gate criteria. It returns one of `fail`, `warn`, or `uncertain`, with a reason. The gate rejects free-text verdicts.
3. **The judge can neither FAIL what the math passed nor PASS a FAIL.** It may move eligible findings between WARN and FAIL-flagged-for-human. `uncertain` always goes to human review.
4. **Pin and log.** The report file records the judge model and version next to each verdict. The repo's pin-and-record rule applies to judge models too.
5. **Fail closed, never silent.** With no key there is no judge. The phase reports `judge: unavailable` and the gate verdict rests on the deterministic phases alone.
6. **Opt-in only.** The default gate stays fast, reproducible, and usable without a key. `--judge` is for release-grade audits of third-party skills, not the everyday pre-flight check.

## Consequences

- The default path keeps its contract. It is reproducible and cheap enough to run every time.
- Cost and latency appear only when someone opts in. The logged judge output keeps verdicts auditable.
- False advertising gains a static detection path, so it no longer depends on the canary run happening to hit the claim.
- The judge's model pin becomes part of the report, so bumping it is a deliberate act.

## Alternatives considered

- **Judge inside the default verdict path.** Rejected. A model in the PASS/FAIL path breaks reproducibility, which is the gate's whole reason to exist, and per-run cost breaks "cheap gate, run always".
- **Port Jev's code directly.** Rejected. The code is specific to its domain of commits, worktrees, and cherry equivalences. Port the shape of the protocol instead: a deterministic core, judgment only on what passes the math, uncertain answers to a human, and fail closed.
- **Do nothing.** Rejected. Borderline-severity calls would stay ad hoc, and catching false advertising would keep depending on luck in the behavioral run.

## Related

- `skills/skill-quality-gate/` is the gate this ADR extends.
- `recipes/model-bakeoff-gate/` is the source of the protocol, with the exit ladder in guard.py and the judge client in lab.py.
- `skills/sandboxed-run/` is complementary. It contains *execution*, and the judge contains *verdicts*. Neither replaces the other.
