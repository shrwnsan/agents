# Provenance: unslop

- **Source:** [cursor/plugins](https://github.com/cursor/plugins), `pstack/skills/unslop/` @ `bc697d0a5a163cec979e362b601e36f5616083fd` (upstream commit 2026-10-12), pinned.
- **License:** MIT. The `LICENSE` file in this directory is a verbatim copy of `pstack/LICENSE` at the same commit (© 2026 Lauren Tan). No exclusion from this repo's Apache-2.0 is needed.
- **Fidelity:** byte-true copy of `SKILL.md` (git blob `97f5b64`). Upstream ships only that one file. There are no scripts.
- **Departures from upstream:** none. The name stays `unslop` because other pstack skills cite it and its rule numbers by name.
- **Invocation:** `disable-model-invocation: true`, so the skill costs no context until a user calls `/unslop`. Clients that ignore that field may auto-trigger it from the short description.
- **Relationship:** the writing counterpart to `no-ai-design-slop` and `audit-ai-design-slop`, which cover UI. Rule 33 (over-compression) is the opposite of `caveman`. Both are explicit modes, so they don't collide unless a user invokes both.
- **Rule ids:** the numbering has deliberate gaps (1, 2, 4, 6, 21). Upstream treats the numbers as stable ids that other skills cite. Don't renumber.
- **Refresh:** re-pull `SKILL.md` and `pstack/LICENSE` at the new commit, diff the rules (a removed or renumbered rule breaks citations), then bump the pin and date here. A bump repeats the full vetting pass from `skills/README.md`.
