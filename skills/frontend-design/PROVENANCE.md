# Provenance

Vendored from [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official), path `plugins/frontend-design/skills/frontend-design`, at commit `44490cccaf6d9f82fdeec9416fbf7c9bd72575dc` (2026-10-21 — latest commit touching that path). Content is byte-identical to [anthropics/skills](https://github.com/anthropics/skills)/`skills/frontend-design` (Anthropic's canonical flat skills repo); the plugin marketplace repo was chosen as source because it is more frequently updated.

Local changes vs upstream:

- Added this `PROVENANCE.md`.
- The upstream path inside the marketplace plugin is already the flat skill folder, so no restructuring was needed.

## Layout incident (2026-10-21)

An earlier sync (#83) copied the *parent* plugin directory (`plugins/frontend-design/`), which is the marketplace wrapper format — `.claude-plugin/plugin.json` + nested `skills/frontend-design/SKILL.md`, no root `SKILL.md`. That broke skill discovery (gate FAIL: SKILL.md not found) and skills.sh indexing. Fixed by repointing `.upstream.yml` to the inner flat path. When syncing, always sync the **inner** `skills/frontend-design` folder, never the plugin wrapper.
