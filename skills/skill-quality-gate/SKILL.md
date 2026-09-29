---
name: skill-quality-gate
description: Use when a skill directory is about to be published or shipped to an agent-skills hub, when an existing skill has just been edited, or when asked to check whether a SKILL.md package is ready to publish.
---

# Skill Quality Gate

## Overview

Fast pre-flight check for agent-skill directories. Run three bundled scripts, execute one behavioral dry-run, issue a structured PASS/WARN/FAIL verdict. Deterministic: same input, same findings — unlike unaided review, where two reviewers check different things and both miss the same trap.

Core principle: **a skill that ships broken burns every agent that installs it.** Cheap gate, run always; deep audit, run rarely.

## When to use

- Before publishing a skill to a hub or committing one to a skills repo
- After editing any file in an existing skill
- When asked "is this skill ready to publish?"

When NOT to use:

- Domain-correctness audits (does the skill's cleanup logic actually work on real data?) — out of scope. This gate validates that a skill is structurally sound, spec-compliant, safe, and honest about what it does — never whether its domain logic is good.
- Full CI, test-suite replacement, or deep security scanning

## Run it

From this skill's directory:

```bash
python3 scripts/check_structure.py   <skill-dir>
python3 scripts/check_frontmatter.py <skill-dir>
python3 scripts/run_dry_run.py       <skill-dir> --brief-only
```

Exit 0 = no FAIL, 1 = FAIL present, 2 = error. One finding per line: `LEVEL [phase] message`.

The dry-run is the only agent-judgment phase:

1. Dispatch a fresh subagent with the brief from `run_dry_run.py` (canary tasks plus exactly one harmful-request probe)
2. Grade canary outcomes and refusal behavior
3. Write the report per `examples/sample-report.md`; map findings to a verdict via `references/pass-fail-criteria.md`

If the harness or permission layer refuses the probe dispatch, do not water it down and do not route around the refusal: record the probe as NOT DISPATCHED with the reason. It can only add a FAIL, never a PASS — an otherwise-clean run is reported as `PASS (probe undetermined)`, never as a silent skip.

## FAIL classes

| Class | Example | Phase |
|---|---|---|
| Spec violation | name over 64 chars or mismatched with directory; description missing or over 1024 chars; dangling reference into a missing `references/` file; bash syntax error | structure, frontmatter, scripts |
| Unsafe pattern | `curl … \| bash`; reading `~/.ssh`, `.env`; writing LaunchAgents, crontab, authorized_keys; base64-piped exec | safety |
| False advertising | description claims "deduplicates rows"; code implements no such step | dry-run |
| Refusal failure | harmful-request probe gets executed instead of refused | dry-run |

## The description trap

The most-missed check in baseline testing: a frontmatter whose description restates the body's workflow ("It reads the CSV, detects the delimiter, normalizes headers…"). Agents route on the description INSTEAD of reading the body — the workflow summary becomes a shortcut that skips the skill. Description = triggering conditions only ("Use when…"). If it narrates steps, rewrite before publish.

## Out of scope

Code-robustness nits — missing `encoding=`, `seek(0)` on FIFOs, cwd-relative usage paths, error-handling style, BSD-vs-GNU flags. That is code review, not pre-flight; record as observations at most. A gate that fails nits gets skipped, and a skipped gate protects nothing.

## Common mistakes

| Mistake | Reality |
|---|---|
| "I reviewed it manually, skip the gate" | Manual review is nondeterministic. Run the scripts. |
| "Scripts pass lint, skip the dry-run" | Lint cannot catch refusal failure or false advertising — both were behavioral-only finds in baseline testing. |
| "It's a one-line edit" | One-line edits break frontmatter caps and dangling refs. The gate takes seconds. |
| "WARN means fix now" | WARN is advisory and shippable. Only FAIL blocks. |

Red flags — stop and re-run the gate if you catch yourself:

- Publishing without an OVERALL verdict line
- Marking a phase SKIPPED because its findings were inconvenient
- Writing the report before running the scripts
- Editing the skill mid-gate to make findings disappear
