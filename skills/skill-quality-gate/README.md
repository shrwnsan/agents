# skill-quality-gate

Lightweight, agent-native pre-flight quality gate for Agent Skills. Runs a fast
check on any skill directory and reports whether it is structurally sound,
correctly declared, safe, and honest — ending in a single PASS / WARN / FAIL
verdict. Calibrated against unaided-review baselines (see
`references/pass-fail-criteria.md`): the checks encode the failure modes that
manual review demonstrably misses.

## What it does

Five phases, three scripts plus one agent-judgment pass:

- **Structure** — `SKILL.md` present and non-empty; every internal reference
  resolves; script files sane
- **Frontmatter** — agentskills.io + Claude Code field rules (name regex and
  directory match, description caps, `compatibility`/`metadata` shapes);
  workflow-style descriptions flagged
- **Scripts** — syntax: `py_compile`, `bash -n`, `node --check` when available
- **Safety** — curated pattern scan: download-piped-to-shell, credential
  access, persistence installs, obfuscated execution, destructive roots
- **Dry-run** — generates canary prompts + exactly one harmful-request probe
  for a fresh subagent; grades behavior and refusal. The brief instructs the
  subagent to run the skill under test's bundled scripts through
  [sandboxed-run](../sandboxed-run/) when it is installed; the report's
  `containment:` line records the mode or the absence, and a report with no
  accounted containment line caps at WARN

## Directory structure

```
skill-quality-gate/
├── SKILL.md
├── README.md
├── scripts/
│   ├── check_structure.py
│   ├── check_frontmatter.py
│   └── run_dry_run.py
├── references/
│   ├── checklist.md
│   └── pass-fail-criteria.md
└── examples/
    └── sample-report.md
```

## Quick start

Point the gate at any skill directory:

```
Check the skill at ./some-skill using skill-quality-gate
```

Or run the scripts directly:

```bash
python3 scripts/check_structure.py   ./some-skill
python3 scripts/check_frontmatter.py ./some-skill
python3 scripts/run_dry_run.py       ./some-skill
```

Exit codes: 0 = no FAIL, 1 = FAIL present, 2 = usage/IO error. `--json` and
`--brief-only` supported on `run_dry_run.py`; `--json` on the validators.

## Report format

See [`examples/sample-report.md`](examples/sample-report.md) for a real
transcript. Per-script findings are `LEVEL  [phase] message` lines ending in
`OVERALL: PASS|WARN|FAIL`; the final report adds the behavioral grading table
and a single publish verdict.

## Design goals

- Agent-native — stdlib-only Python, no external CLI required
- Lightweight enough to run after every edit (seconds)
- Deterministic — same input, same findings
- Scoped: structure, spec compliance, safety, honesty. Explicitly **not** a
  domain-correctness audit or a code review — see the out-of-scope list

## Relationship to other tools

- **validate-skills**: strong at static/spec compliance; this gate reuses the
  idea and adds behavioral + safety phases
- **skills-check (CLI)**: deeper external toolkit for security, freshness, and
  token analysis — use when you need that depth
- **Unaided review**: nondeterministic; baseline testing showed careful
  reviewers missing the most common trap (workflow-style descriptions)
  entirely while burning effort hand-rolling these same checks
