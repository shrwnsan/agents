# Provenance — nothing-design

- **Naming:** vendored as `nothing-design` (2026-10-19), same as upstream —
  the name describes the design language the skill delivers (Nothing Tech's
  industrial-monochrome aesthetic), which is what a user asks for by name.
- **Source:** [dominikmartn/nothing-design-skill](https://github.com/dominikmartn/nothing-design-skill),
  `nothing-design/` @ `74affbb` (HEAD 2026-04-01), pinned.
- **License:** MIT. Covered by the `LICENSE` file in this directory
  (© Dominik Martin, copied verbatim from upstream); no exclusion from this
  repository's Apache-2.0 needed.
- **Fidelity:** byte-true copy of upstream `SKILL.md`, `references/`
  (tokens, components, platform-mapping), and `LICENSE` — sha256-verified at
  vendoring time. Nothing added, removed, or rewritten.
- **Excluded from upstream:** `README.md` (repo landing page) and
  `preview.gif` (~3.6 MB demo asset) — not part of the skill package.
- **Frontmatter note:** upstream carries a non-standard `version: 3.0.0`
  top-level key; left verbatim (clients ignore unknown keys; the repo's
  skill-quality-gate records it as an informational SKIP, not a failure).
- **Upstream status:** frozen — created 2026-04-01, three commits total, no
  maintenance since. Treat as a finished artifact; if fixes are needed they
  land here as local patches and get listed under departures below.
- **Departures from upstream:** none.
- **Vetting (2026-10-19):** skill-quality-gate — structure PASS, frontmatter
  PASS; behavioral dry-run with 3 benign canaries (declare-fonts step, ask-mode
  step, end-to-end workflow) and one refusal probe: all PASS, no credential
  access, no writes outside scratch dirs (skill bundles no scripts; nothing
  executed under containment). Known upstream quirk, non-blocking:
  platform-mapping.md §3 references a `get_font_family_info` tool that not
  every harness provides; it sits off the HTML/CSS code path, so the primary
  workflow is unaffected.
