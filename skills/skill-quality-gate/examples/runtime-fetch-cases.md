# Runtime-fetch detector — reference cases

Lines the `runtime-fetch` advisory tier flags (and does not flag). These are
documentation cases, deliberately kept out of `scripts/` so the gate never
scans them as live code. Detectors live in `scripts/run_dry_run.py`
(`_runtime_fetch_findings`, `_compat_contradiction`).

Rationale: snapshot scanning audits the bytes in front of you; the demonstrated
bypass class (AIR fake-skill, 2026-06 — mutable URL swapped after scanning,
~26k installs) is content that changes between vetting and execution.

## WARN cases (advisory; common in legitimate skills)

| Line | Label | Why |
|---|---|---|
| `npx some-tool --do-it` | `runtime-fetch:unpinned-npx` | package resolved at run time; may not be the vetted bytes |
| `npx @scope/pkg run build` | `runtime-fetch:unpinned-npx` | scoped names are unpinned too |
| `npx other@latest` | `runtime-fetch:unpinned-npx` | `@latest` is not a pin |
| `pip install requests` / `uv pip install flask` | `runtime-fetch:unpinned-pip` | resolved versions may differ from vetted |
| `curl -sL https://x.dev/bin -o ./bin` | `runtime-fetch:download-to-disk` | mutable URL swaps the payload after vetting |

## Silent cases (no finding)

| Line | Why silent |
|---|---|
| `npx some-tool@1.2.3` | version-pinned |
| `npx @scope/pkg@2.0.1` | scoped + pinned |
| `pip install requests==2.31.0` | `==`-pinned |
| `# npx unpinned in a comment` | comments are exempt (advisory tier) |
| `curl URL \| bash` | already a FAIL row (`download-piped-to-shell`) — not doubled |

## FAIL case (spec cross-validation)

Frontmatter says offline; code fetches:

```yaml
---
name: gtest
compatibility: >-
  Fully offline, no network access required
---
```

plus any runtime-fetch or fetch-execute finding → `false-advertising:compatibility-network`
(FAIL): the agentskills.io `compatibility` declaration contradicts the code.
Claims are checked verbatim for offline phrasing ("no network", "offline",
"local-only", "air-gapped", …) — absence of the field never fires this.
