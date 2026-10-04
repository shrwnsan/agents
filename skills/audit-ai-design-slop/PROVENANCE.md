# Provenance — audit-ai-design-slop

- **Naming:** vendored under the upstream name. Unlike the motion-craft
  rebrand, the upstream name is already descriptive and discovery-oriented
  ("audit AI design slop" maps token-for-token to how the request is phrased),
  and it is one half of a named pair — renaming one half would break the
  pair's cross-references and the sibling's workflow text, which names this
  skill explicitly.
- **Source:** [MengTo/Skills](https://github.com/MengTo/Skills),
  `agent-skills/ui/audit-ai-design-slop/` @ `944d57806eb3b286f4a3f4c852ab8789d5b731c0`
  (upstream HEAD 2026-10-04), pinned.
- **License:** MIT. Covered by the `LICENSE` file in this directory
  (© Meng To, copied verbatim from upstream); no exclusion from this
  repository's Apache-2.0 needed.
- **Fidelity:** byte-true copy of `SKILL.md` and `REFERENCES.md`. All audit
  classes, boundaries, and catalog references are verbatim from upstream.
- **Departures from upstream:**
  1. `agents/openai.yaml` (Codex interface metadata) not vendored — this hub
     targets the `~/.agents/skills/` convention and Claude Code.
  2. No other changes. The SKILL.md cross-link to
     `../no-ai-design-slop/ARTICLE.md` resolves because the sibling skill is
     vendored alongside — **vendor the pair together or neither**.
- **Relationship:** the review layer of the design cluster —
  `frontend-design` directs aesthetics, `motion-craft` executes motion, this
  pair audits and gates. Splits the same way dataviz (generate) splits from
  dataviz-tufte (review).
- **Behavioral dry-run (2026-10-04, vendoring vetting):** PASS-with-notes
  against a live published noindex Kibo-style research page — ran
  start-to-finish with the cross-link resolving, all four tested boundaries
  held (no redesign prescription, no technique-rejection in isolation, no
  numeric score, no AI-authorship guessing), and the removal test correctly
  cleared intentional devices. Three upstream doc nits to re-check on
  refresh (kept byte-true here, not patched): (1) the output template has no
  end-slot for the Feedback Rules' mandated "largest single improvement"
  line; (2) no lean-artifact escape from "five to eight findings" (pressure
  to pad below 5 real findings); (3) "use only the relevant catalog
  sections" leaves Philosophy/High-Signal-Clusters membership undefined.
- **Refresh:** re-pull both dirs of the pair from upstream, diff (the
  cross-link and the ARTICLE catalog are the coupling points), keep the pair
  in lockstep, check whether upstream closed the three dry-run nits, bump
  the pin and date here and in the sibling's PROVENANCE.
