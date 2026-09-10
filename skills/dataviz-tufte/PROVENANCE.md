# Provenance — dataviz-tufte

- **Naming:** vendored here as `dataviz-tufte` (2026-09-10) so it sorts
  adjacently to the `dataviz` skill as one generate/review family. Formerly
  `tufte-data-viz`. Upstream assets and demo links still reference the
  original `tufte-data-viz` name.
- **Source:** [shrwnsan/dataviz-tufte](https://github.com/shrwnsan/dataviz-tufte)
  (maintainer's fork of caylent/tufte-data-viz, repo renamed 2026-09-10 —
  old URLs redirect) @ `91f0dee`, pinned. Upstream:
  [caylent/tufte-data-viz](https://github.com/caylent/tufte-data-viz) — the
  fork was byte-identical to its parent at the original `ae7ca0d` pin; it has
  since gained two local commits: a CVD-aware palette-validation paragraph in
  SKILL.md's Color quick reference (PR #1), and the skill rename to
  `dataviz-tufte`.
- **License:** MIT. Covered by the `LICENSE` file in this directory; no
  exclusion from this repository's Apache-2.0 needed (unlike proprietary
  vendored skills).
- **Fidelity:** verbatim copy excluding `.git`, including showcase assets in
  `_docs/` (they are referenced by the README).
- **Departure from byte-true:** the SKILL.md frontmatter `description` is
  rescoped from the upstream "creating, reviewing, or styling charts…" wording
  to a reviewer-only framing. Rationale: this hub's `dataviz` skill owns chart
  generation; scoping this skill to audit/review keeps the two
  complementary and avoids trigger collisions in environments where both are
  installed. `allowed-tools` unchanged (read-only tools already
  match the reviewer role). The `name`/folder rename to `dataviz-tufte` is a
  fork-side change (not a hub departure) — taken verbatim at sync.
- **Refresh:** sync from the fork, re-apply the description rescope, bump the
  pin. The description rescope should be re-reviewed on refresh — if a future
  dataviz pin changes generation scope, revisit the split. (Re-applied as-is
  at the `91f0dee` refresh, 2026-09-10.)
