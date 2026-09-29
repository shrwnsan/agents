# Global AGENTS.md Consolidation

How the global agent rules went from a 184-line copy repeated per repo to a 71-line canonical file, and why each section was cut.

## Context

Before the consolidation, global agent rules lived as per-repo copies of one original file. The last pre-consolidation revision stays in history: [shrwnsan/shrwnsan @ 182fc65](https://github.com/shrwnsan/shrwnsan/blob/182fc65/AGENTS.md). That repo then removed its copy entirely, since nothing in it was repo-specific.

The canonical rules now live at [global/AGENTS.md](../global/AGENTS.md), published from the live `~/.agents/AGENTS.md`. Six harnesses load it in every session; see the README's [Global rules](../README.md#global-rules) section for the wiring. Every line therefore costs tokens in every repo, every session. That cost is the reason for the cuts below.

## Principles

1. **A global rule must change behavior in every repo.** Anything niche pays a token cost everywhere for effect in a few places.
2. **No restatement.** If another line already enforces it, the duplicate goes.
3. **Reference material for humans moves out of the rules file** — into human-facing notes, not agent context.
4. **Niche or harness-specific content lives where it operates**, not in the shared file.

## What was cut, and why

| Old section | Reason |
|-------------|--------|
| Design Philosophy (anti-AI-slop) | Affects frontend and design work only, so it fails the every-repo test. Detailed taste guidance lives in the `frontend-design` skill, which loads when design work happens; the generic bullets (purple gradients, Inter/Roboto) are knowledge models already carry. |
| Development Philosophy ("ship small, iterate often") | Pure restatement: the Git section already enforces small, reviewable commits. |
| Filename prefix table (purpose, phase, example columns) | The operative rule is one line: `<prefix>-NNN-<slug>.md`, with the seven prefixes inline. The columns restated the prefix list or were derivable from the pattern; the full table and timeline flow moved to a human-facing guide. |
| `tasks-{m}-prd-{n}` special case, retro use cases, timeline flow | Derivable from the naming pattern; reference material for humans. |
| Tools Reference | gh and trash rules appear where they are used (GitHub and Files sections); a reference section mostly restates what models already know. |
| Slash Commands | Claude-only, pointing at machine-local dirs Claude Code loads natively; the other five harnesses ignore it. |
| Browser Automation details | The operative line stays in Stacks: the open/snapshot/click/fill workflow, plus "ask before installing". The install command and external link are discoverable. |
| CI & Quality Gates, Pull Requests | Merged into Quality and GitHub. "No ship without docs (if applicable)" was vague; the Docs section now requires updates on change. |
| Code Style | Folded into Quality: match repo patterns, simple direct code, no speculative abstractions. |
| Critical Thinking | Folded into the header and Quality: root causes, conflicting instructions, safer path. |
| Test-Driven Bug Fixes (four steps) | Compressed to one operative sentence (failing test first, then fix, then confirm it passes); the debug test-plan path kept. |
| Important Locations | Folded into Workspace; the `~/.claude/` entry cut because Claude Code knows its own directory. |
| Maintenance, Learn More links, Inspired by | Guidance for the file's maintainer and links for humans; moved to human-facing notes. |
| Welcome header, Agent Protocol wrapper | Zero effect on behavior. |

## What was kept

Everything still in [global/AGENTS.md](../global/AGENTS.md) is operative in every repo: workspace layout and the clone convention, file safety (`trash`, size split), security (secrets files, env vars, staged-diff check), Git and GitHub conventions including the worktree and post-merge cleanup rules, quality gates, subagent delegation, docs naming, and stack defaults.

Net effect: 184 lines to 71, with nothing operative lost.

## References

- [global/AGENTS.md](../global/AGENTS.md) — the canonical rules.
- [Global rules wiring](../README.md#global-rules) — how each harness loads the file.
- [Pre-consolidation version](https://github.com/shrwnsan/shrwnsan/blob/182fc65/AGENTS.md) — shrwnsan/shrwnsan @ 182fc65, the last revision before removal.
