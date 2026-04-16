# agents

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![Skills: 9](https://img.shields.io/badge/skills-9-green.svg)

Personal hub for AI agent skills, prompts, and configurations.

## Skills

Skills are self-contained packages with a `SKILL.md` instruction file and optional scripts/binaries. They are loaded by agents that support the `~/.agents/skills/` convention.

| Skill | Category | Source | Description |
|-------|----------|--------|-------------|
| [crafting-commits](skills/crafting-commits/) | Development | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Conventional commit message drafting with collaborative attribution |
| [review-pr](skills/review-pr/) | Development | native | Comprehensive peer code review with severity-tagged findings |
| [systematic-debugging](skills/systematic-debugging/) | Development | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Systematic debugging methodology to prevent thrashing |
| [frontend-design](skills/frontend-design/) | Design & Content | [anthropics](https://github.com/anthropics/claude-plugins-official) | Production-grade frontend interfaces |
| [marp-slide](skills/marp-slide/) | Design & Content | [softaworks](https://github.com/softaworks/agent-toolkit) | Marp presentation slides with 7 themes |
| [handoff-context](skills/handoff-context/) | Workflow | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Context engineering for session handoffs across AI tools |
| [meta-search](skills/meta-search/) | Workflow | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins/tree/main/plugins/search-plus) | Error recovery for web search failures (403, 429, 422) with bundled Tavily/Jina scripts |
| [caveman](skills/caveman/) | Workflow | [JuliusBrussee](https://github.com/JuliusBrussee/caveman) | Ultra-compressed communication mode (~75% token reduction) |
| [here-now](skills/here-now/) | Workflow | native | Security-hardened file publishing via [here.now](https://here.now). Based on [heredotnow/skill](https://github.com/heredotnow/skill) v2.0.0 |

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

## Recipes

Recipes are upstream integration playbooks from the *Claw ecosystem (OpenClaw, Hermes). Unlike skills, they are **not** agent-executable capabilities — they are reference material documenting production-hardened integration architectures and patterns.

Tracked read-only from upstream repos. See [docs/research-001-claw-recipes-vs-skills.md](docs/research-001-claw-recipes-vs-skills.md) for context on the recipe vs skill distinction.

### Synced from upstream repos

- **twilio-voice-brain** — Phone-to-knowledge pipeline via Twilio + voice AI. From [garrytan/gbrain](https://github.com/garrytan/gbrain).

## License

Apache 2.0
