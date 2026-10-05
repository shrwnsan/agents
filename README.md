# agents

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![Skills: 24](https://img.shields.io/badge/skills-23-green.svg)
[![skills.sh](https://skills.sh/b/shrwnsan/agents)](https://skills.sh/shrwnsan/agents)

Personal hub for AI agent skills, prompts, and configurations.

## Skills

Skills are self-contained packages with a `SKILL.md` instruction file and optional scripts/binaries. They are loaded by agents that support the `~/.agents/skills/` convention.

The full catalog — 24 skills across Development, Design & Content, Workflow, Security, System, and Crypto, with sources, provenance pins, and the acceptance rules — lives in [skills/README.md](skills/README.md). Evaluated-and-rejected candidates are recorded in [rejected-skills.json](rejected-skills.json).

Skills from vibekit are automatically synced via GitHub Actions. Upstream skills are synced manually via [sync-upstream](.github/workflows/sync-upstream.yml) — sources in [.upstream.yml](.upstream.yml).

## Usage

Copy skills into your agent's skills directory:

```bash
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/* ~/.agents/skills/
```

Skills follow the `~/.agents/skills/` convention. Claude Code users should symlink or copy to `~/.claude/skills/` instead:

```bash
ln -s ~/.agents/skills ~/.claude/skills
# or
cp -r ~/.agents/skills/* ~/.claude/skills/
```

For platform-specific setup guides, see [docs/](docs/).

## Global rules

[global/AGENTS.md](global/AGENTS.md) holds the rules every agent follows in every repo: workspace layout, file safety, Git and GitHub conventions, and quality checks. A repo's own AGENTS.md or CLAUDE.md wins on conflict. The rules are personal, so adapt the Workspace section before reusing them. For what the file deliberately leaves out and why, see [docs/ref-004-agents-md-consolidation.md](docs/ref-004-agents-md-consolidation.md).

Copy it to `~/.agents/AGENTS.md`, then point each harness's global path at that copy:

| Harness | Global instructions |
|---------|---------------------|
| Droid | `~/.agents/AGENTS.md` (read directly) |
| Claude Code | `~/.claude/CLAUDE.md` containing `@~/.agents/AGENTS.md` (an import, not a link) |
| Codex | `~/.codex/AGENTS.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |
| Pi | `~/.pi/agent/AGENTS.md` |
| Amp | `~/.config/AGENTS.md` |

```bash
mkdir -p ~/.agents
cp /tmp/agents/global/AGENTS.md ~/.agents/AGENTS.md   # clone from Usage above
ln -s ~/.agents/AGENTS.md ~/.codex/AGENTS.md          # same for the OpenCode, Pi, and Amp paths
```

`global/AGENTS.md` is the published copy. The live one is `~/.agents/AGENTS.md`: edit that, then copy it here to publish.

Don't link Gemini CLI or Qwen Code. Their memory tools append to their global files, which would write into the shared rules.

## Recipes

Recipes are integration playbooks. Unlike skills, they are **not** agent-executable capabilities — they are reference material documenting production-hardened integration architectures and patterns. See [docs/research-001-claw-recipes-vs-skills.md](docs/research-001-claw-recipes-vs-skills.md) for the recipe vs skill distinction.

### Maintained in this repo

- **[model-bakeoff-gate](recipes/model-bakeoff-gate/)** — Pre-deletion guard + model bakeoff harness for risky agent actions. Deterministic git checks hard-block first; a model call judges only the fuzzy remainder, with provider failover (TypeSafe Jev → Vercel AI Gateway → OpenRouter) and keyless fail-closed degradation. Ships its three runnable files (`lab.py`, `run_evals.py`, `guard.py`) under `scripts/` as a working stdlib-only harness.
- **[listening-post](recipes/listening-post.md)** — Bounded, polite tailnet capture of a logged-in web community you belong to, with sanitize-at-ingest discipline and a committed classifier calibration. No API keys.

### Synced from upstream repos

- **twilio-voice-brain** — Phone-to-knowledge pipeline via Twilio + voice AI. From [garrytan/gbrain](https://github.com/garrytan/gbrain). Tracked read-only from upstream.

## License

Apache 2.0
