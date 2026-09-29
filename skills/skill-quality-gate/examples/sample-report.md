# Skill Quality Gate Report

**Skill:** `broken-skill` (`/tmp/sqg-fixtures/broken-skill`, synthetic negative control)
**Date:** 2026-09-29
**Verdict:** **FAIL — DO NOT PUBLISH** (8 blocking findings)

---

## Phase: structure — `check_structure.py` (exit 1)

```
PASS  [structure] SKILL.md present with content after frontmatter
FAIL  [structure] dangling reference: SKILL.md references 'references/usage.md' (not found: references/usage.md)
FAIL  [structure] dangling reference: README.md references 'references/usage.md' (not found: references/usage.md)
FAIL  [structure] dangling reference: README.md references 'examples/demo.md' (not found: examples/demo.md)
PASS  [structure] scripts/: 2 script file(s) non-empty with sane modes
OVERALL: FAIL
```

## Phase: frontmatter — `check_frontmatter.py` (exit 1)

```
PASS  [frontmatter] name length OK (13/64 chars)
FAIL  [frontmatter] name 'Broken_Skill!' does not match ^[a-z0-9]+(-[a-z0-9]+)*$ (lowercase alphanumeric + hyphens)
FAIL  [frontmatter] name 'Broken_Skill!' does not match directory basename 'broken-skill'
FAIL  [frontmatter] required key 'description' is missing or empty
OVERALL: FAIL
```

## Phase: scripts + safety — `run_dry_run.py` (exit 1)

```
PASS  [scripts] scripts/deploy.sh: /opt/homebrew/bin/bash -n clean
FAIL  [scripts] scripts/setup.sh: syntax error: … setup.sh: line 6: syntax error: unexpected end of file from `if' command on line 3
FAIL  [safety] scripts/deploy.sh:3 [download-piped-to-shell] remote content is fetched and executed in one step; a hostile or compromised URL runs arbitrary code with full user privileges
PASS  [dry-run] dry-run brief generated for 'Broken_Skill!' (2 documented usage line(s) -> 3 benign canaries + 1 harmful probe)
OVERALL: FAIL
```

Dry-run brief was generated (exfil-shaped probe tailored to the description's "deploy" verb). Full brief omitted here — see `run_dry_run.py --brief-only` output format.

## Phase: dry-run grading

**Not dispatched.** Eight static FAILs are open; per checklist step 7, fix and re-run before behavioral grading — there is no value in canary-grading a skill whose installer cannot parse.

## Findings to fix

1. Rename to a lowercase-kebab name matching the directory (`broken-skill`)
2. Add a triggering-conditions `description` (≤1024 chars)
3. Create `references/usage.md` and `examples/demo.md`, or remove the references
4. Fix the unclosed `if` in `scripts/setup.sh`
5. Remove the `curl … | bash` installer in `scripts/deploy.sh` (vendor the payload with a checksum, or drop it)

Re-run the full gate from checklist step 1 after fixing; findings cascade.
