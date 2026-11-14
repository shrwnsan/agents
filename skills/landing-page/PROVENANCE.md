# Provenance—landing-page

- **Naming:** vendored under the upstream name.
- **Source:** [MengTo/Skills](https://github.com/MengTo/Skills),
  `agent-skills/web-design/landing-page/` @ `3cc93458c4949c39a04e938ea7892a1d6d3d40bf`
  (upstream HEAD 2026-11-14, pinned), MIT.
- **License:** MIT. Covered by the `LICENSE` file in this directory
  (© Meng To, copied verbatim from the upstream repo root); no exclusion
  from this repository's Apache-2.0 needed.
- **Fidelity:** byte-true copy of `SKILL.md` and `REFERENCES.md`.
- **Departures from upstream:**
  1. `demo/` (a sample output page with preview image) not vendored—the
     skill is the methodology; a bundled demo page adds weight without
     changing behavior.
  2. `agents/openai.yaml` (Codex interface metadata) not vendored—this hub
     targets the `~/.agents/skills/` convention and Claude Code.
- **Relationship:** fills the conversion-methodology gap in the design
  cluster. `frontend-design` directs the visuals, `motion-craft` executes
  motion, the `no-ai-design-slop` pair gates taste, and this one supplies
  structure and copy for a single-offer page (outline, hero contract,
  objection handling, SEO/AEO indexing calls). Complementary, not
  duplicate: JobWire's landing page was built ad hoc to roughly this
  outline; no skill encoded the method before.
- **Refresh:** re-pull the upstream dir, diff `SKILL.md` and
  `REFERENCES.md`, keep the demo/openai.yaml exclusions, bump the pin and
  date here, and update the Source-column pin in `skills/README.md`.
