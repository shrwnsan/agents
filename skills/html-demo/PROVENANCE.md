# Provenance — html-demo

- **Source:** [MengTo/Skills](https://github.com/MengTo/Skills),
  `agent-skills/web-design/html-demo/` @ `3cc93458c4949c39a04e938ea7892a1d6d3d40bf`
  (upstream HEAD 2026-11-14), pinned. Upstream extracted the method from
  fil.design/download (October 2026), where it powers Fil for Mac's hero window.
- **License:** MIT. Covered by the `LICENSE` file in this directory
  (© Meng To, copied verbatim from upstream); no exclusion from this
  repository's Apache-2.0 needed.
- **What was transformed:** this is a port, not a byte-true copy. Upstream is
  React-first (`StepWindow.jsx` + a secondary vanilla twin, `step-window.js`,
  clocked by a 40 ms `setInterval`). This skill keeps the upstream method
  exactly — `View({ t })`/`draw(t)` pure-function-of-one-clock frames, fixed
  1200 × 750 stage with one `--k` scale, IntersectionObserver gating, 0.25 s
  dt clamp, scripted pointer, designed reduced-motion end frames, `role="img"`
  stage — and recasts the engine for the vanilla pages this repo targets:
  1. `scripts/demo-window.js` is a single-file, dependency-free engine loaded
     with a plain `<script>` (works from `file://`). The clock is one
     `requestAnimationFrame` loop (same gating and clamp) instead of
     `setInterval`.
  2. Pointer targets are measured from the DOM (`data-aim` + `point(name)`,
     re-measured after the step builds and on `document.fonts.ready`),
     replacing upstream's hard-coded stage coordinates (upstream's React
     contract measures aims in a layout effect; the vanilla twin shipped
     Playwright-measured numbers).
  3. `scripts/demo-window.css` is upstream's `step-window.css` (frame, stage,
     pointer, steps bar) with the header comment updated; the rules are
     unchanged.
  4. `SKILL.md` is rewritten framework-agnostic against this engine; the
     method rules, numbers table and workflow keep upstream's wording and
     values wherever they are engine-independent.
  5. `example/index.html` is new: a complete working page showing a fictional
     invoicing app (four steps, 23.5 s total), with no real-company UI and no
     copied proprietary assets.
- **Not vendored from upstream:** `scripts/StepWindow.jsx`,
  `scripts/example-steps.jsx`, `scripts/preview-plugin.mjs` (Vite-specific),
  `scripts/shoot.mjs` (Playwright harness), `demo/` (Fil for Mac's own
  product demo with its proprietary images — the rules say use only owned
  pictures), `references/` briefs, and `agents/openai.yaml` (Codex interface
  metadata). The helper-agent workflow lives in upstream's
  `references/brief.md`; re-read it there if building many windows at once.
- **Departures from upstream method:** none deliberate. One addition: a rule
  that each step's `html` must carry the state that step starts from, so a
  rebuilt stage never flashes a stale frame at the cut (upstream's keyed
  remount does this implicitly in React).
- **Relationship:** the live-window sibling of `html-reel`, which already
  points here from its boundary line; `frontend-design` directs the look,
  `motion-craft` covers user-triggered interaction motion, and this skill
  owns the scripted, scrubbable demo window.
- **Refresh:** re-pull the upstream dir, diff the method text (the numbers
  table is the asset — silent drift there defeats the pin), port any engine
  change into `demo-window.js`, re-verify `example/index.html` in a headless
  browser, bump the pin and date here.
