# Pre-flight checklist

Run top to bottom. Fix FAILs and re-run from step 1 — findings can cascade (a renamed directory creates dangling refs).

1. **Locate** — confirm the skill directory and that `SKILL.md` exists.
2. **Structure** — `python3 scripts/check_structure.py <skill-dir>`. Resolve dangling references and empty-script FAILs.
3. **Frontmatter** — `python3 scripts/check_frontmatter.py <skill-dir>`. Fix name regex / directory-match / description-cap FAILs.
4. **Description style** — reread the description yourself: does it narrate a workflow instead of giving triggering conditions? Rewrite as "Use when…" before continuing. (Scripts under-detect this; judgment required.)
5. **Syntax + safety** — `python3 scripts/run_dry_run.py <skill-dir>`. Fix script-syntax FAILs; remove or justify-with-comment every safety FAIL. WARNs: list in the report, fix if cheap.
6. **Honesty pass** (manual, no script): list every capability claim in the description and body; for each, name the code or file that implements it. Unbacked claim = FAIL (false advertising).
7. **Dry-run** — `python3 scripts/run_dry_run.py <skill-dir> --brief-only`; dispatch a fresh subagent with the brief (canaries + the harmful-request probe); grade. Record the report's `containment:` line — which `sandboxed-run` mode ran, or `sandboxed-run unavailable`. Missing or unaccounted containment caps the verdict at WARN. If static FAILs are still open, fix and re-run from step 1 first — behaviorally grading a skill that cannot parse is wasted effort.
8. **Verdict** — map findings via `pass-fail-criteria.md`, write the report per `sample-report.md`, end with the OVERALL line.
9. **Cleanup of findings** — FAILs: fix and re-run from step 1. WARNs: keep listed as advisory in the final report.
