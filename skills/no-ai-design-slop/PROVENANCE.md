# Provenance — no-ai-design-slop

- **Naming:** vendored under the upstream name — see the sibling
  `audit-ai-design-slop/PROVENANCE.md` naming note; the pair is named
  explicitly in each other's workflow text, so the names travel together.
- **Source:** [MengTo/Skills](https://github.com/MengTo/Skills),
  `agent-skills/ui/no-ai-design-slop/` @ `944d57806eb3b286f4a3f4c852ab8789d5b731c0`
  (upstream HEAD 2026-10-04), pinned.
- **License:** MIT. Covered by the `LICENSE` file in this directory
  (© Meng To, copied verbatim from upstream); no exclusion from this
  repository's Apache-2.0 needed.
- **Fidelity:** byte-true copy of `SKILL.md`, `ARTICLE.md` (the slop-pattern
  catalog the audit skill leans on), and `REFERENCES.md`.
- **Departures from upstream:**
  1. `agents/openai.yaml` (Codex interface metadata) not vendored — this hub
     targets the `~/.agents/skills/` convention and Claude Code.
  2. No other changes. `ARTICLE.md` must stay at this path: the sibling
     skill links to it as `../no-ai-design-slop/ARTICLE.md`.
- **Relationship:** passive quality gate for UI work (prevent while
  building); the sibling `audit-ai-design-slop` is the explicit review
  workflow (audit without editing). Together they are the review layer of the
  design cluster — `frontend-design` directs, `motion-craft` executes, this
  pair gates and audits.
- **Refresh:** re-pull both dirs of the pair from upstream, diff (the
  ARTICLE catalog is the asset — a silent drift there defeats the pin), keep
  the pair in lockstep, bump the pin and date here and in the sibling's
  PROVENANCE.
