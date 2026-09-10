# Provenance — tufte-data-viz

- **Source:** [shrwnsan/tufte-data-viz](https://github.com/shrwnsan/tufte-data-viz)
  (maintainer's fork) @ `59162ce`, pinned. Upstream:
  [caylent/tufte-data-viz](https://github.com/caylent/tufte-data-viz) — the
  fork was byte-identical to its parent at the original `ae7ca0d` pin; it has
  since gained one local commit (PR #1): a CVD-aware palette-validation
  paragraph in SKILL.md's Color quick reference.
- **License:** MIT. Covered by the `LICENSE` file in this directory; no
  exclusion from this repository's Apache-2.0 needed (unlike proprietary
  vendored skills).
- **Fidelity:** verbatim copy excluding `.git`, including showcase assets in
  `_docs/` (they are referenced by the README).
- **Departure from byte-true:** the SKILL.md frontmatter `description` is
  rescoped from the upstream "creating, reviewing, or styling charts…" wording
  to a reviewer-only framing. Rationale: this hub's `dataviz` skill owns chart
  generation; scoping tufte-data-viz to audit/review keeps the two
  complementary and avoids trigger collisions in environments where both are
  installed. `name` and `allowed-tools` are unchanged (read-only tools already
  match the reviewer role).
- **Refresh:** sync from the fork, re-apply the description rescope, bump the
  pin. The description rescope should be re-reviewed on refresh — if a future
  dataviz pin changes generation scope, revisit the split. (Re-applied as-is
  at the `59162ce` refresh, 2026-09-10.)
