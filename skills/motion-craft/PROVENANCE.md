# Provenance — motion-craft

- **Naming:** vendored here as `motion-craft` (2026-09-15). Upstream name was
  `emil-design-eng` (personal-brand naming); the rename describes what the
  skill does rather than who wrote it, and avoids implying more Emil Kowalski
  skills will be vendored as a family.
- **Source:** [emilkowalski/skills](https://github.com/emilkowalski/skills),
  `skills/emil-design-eng/SKILL.md` @ `d23d7f8` (HEAD 2026-08-21), pinned.
- **License:** MIT. Covered by the `LICENSE` file in this directory
  (© Emil Kowalski, copied verbatim from upstream); no exclusion from this
  repository's Apache-2.0 needed.
- **Fidelity:** NOT a byte-true copy — this is a restructured port. All
  technical values (easing curves, durations, spring params, thresholds) are
  verbatim from upstream; none were invented or altered.
- **Departures from upstream:**
  1. Split the single 27KB `SKILL.md` into a slim `SKILL.md` (decision
     framework, quick values, review format) plus `reference/techniques.md`
     (component patterns, clip-path, transforms, springs, gestures) and
     `reference/performance.md` (GPU rules, reduced motion, debugging) —
     progressive disclosure per skill-authoring best practice.
  2. Removed the "Initial Response" section that scripted a canned greeting
     and forbade answering until questioned — an anti-pattern for a skill.
  3. Removed course/product marketing (`animations.dev` course plugs); kept
     neutral curve references (easings.co, easing.dev) as tools.
  4. Generalized personal/employer anecdotes (Vercel dashboard, Family
     drawer, Sonner download counts) to neutral phrasing while keeping the
     instructive point; the "Sonner Principles" section is retitled
     "Component principles" with substance intact.
  5. Rewrote the frontmatter `description` as a third-person, trigger-oriented
     scoping statement, and added a scoping line distinguishing it from
     `frontend-design` (aesthetic direction) — this skill owns execution
     craft. Mirrors the dataviz/dataviz-tufte split rationale.
  6. Added attribution line at the end of `SKILL.md`.
- **Refresh:** pull the new upstream `SKILL.md`, re-apply the split structure
  and the removals above, diff values section by section (the exact values
  are the asset — a silent drift there defeats the pin), bump the pin, and
  note the refresh date here.
