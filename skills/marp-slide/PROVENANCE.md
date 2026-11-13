# PROVENANCE — marp-slide

- **Source:** [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit) `skills/marp-slide`
- **Pinned:** `06825f04669d4364a16abc267650c86cf153d349` (2026-01-18, "feat: add 23 curated skills with comprehensive documentation" — the only upstream commit to touch this path)
- **License:** MIT (upstream repo root license; no LICENSE file ships inside the skill directory). This directory is **excluded from the hub's Apache-2.0** — see the vendor-and-pin policy in the skills README.
- **Vendored:** 2026-11-13, byte-true (SKILL.md verified identical to the pin; file set matches: README.md, SKILL.md, assets, references).
- **Tracking:** listed in `.upstream.yml` (`preserve: [PROVENANCE.md]`); refresh by hand-running the sync-upstream workflow, then diff against this pin. Bumping the pin repeats the vetting pass.

## What it does

Creates professional Marp presentation slides with 7 pre-designed themes (default, minimal, colorful, dark, gradient, tech, business), custom theme support, image layouts, and quality best practices baked into the templates.

## Vendor review notes (2026-11-13)

- **Structural gate:** PASS (check_structure + check_frontmatter; description 280 chars, SKIP tier only).
- **Provenance gap closed:** this skill synced via `.upstream.yml` since adoption but shipped without a PROVENANCE.md or `preserve` entry — the only upstream skill outside the vendor-and-pin policy. This file and the manifest `preserve` entry close that gap; the next sync will no longer overwrite provenance with upstream files.
- **Fit:** presentation-specific; no overlap with documents/pptx tooling (those edit existing decks, this authors Marp markdown decks).
