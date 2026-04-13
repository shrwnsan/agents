# agents

Personal hub for AI agent skills, prompts, and configurations.

## Skills

Skills are self-contained packages with a `SKILL.md` instruction file and optional scripts/binaries. They are loaded by agents that support the `~/.agents/skills/` convention.

### Synced from [vibekit-claude-plugins](https://github.com/shrwnsan/vibekit-claude-plugins)

Automatically synced via GitHub Actions when updated in the marketplace repo.

- **crafting-commits** — Conventional commit message drafting with collaborative attribution
- **handoff-context** — Context engineering for session handoffs across AI tools
- **systematic-debugging** — Systematic debugging methodology to prevent thrashing
- **meta-search** — Error recovery for web search failures (403, 429, 422) with bundled Tavily/Jina scripts

### Synced from upstream repos

Manually synced via [sync-upstream](.github/workflows/sync-upstream.yml) workflow. Sources configured in [.upstream.yml](.upstream.yml).

- **frontend-design** — Production-grade frontend interfaces. From [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official).
- **marp-slide** — Marp presentation slides with 7 themes. From [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit).
- **caveman** — Ultra-compressed communication mode (~75% token reduction). From [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman).

### Native skills

Authored and maintained directly in this repo.

#### here-now (hardened)

Publish files to live URLs via [here.now](https://here.now). Security-hardened fork of [heredotnow/skill](https://github.com/heredotnow/skill).

- Python-native publisher — zero external dependencies (no curl, no jq)
- Blocks dangerous file types (`.env`, `.pem`, `.key`, etc.)
- Warns on suspicious types (`.bak`, `.tmp`, no extension)
- Pre-upload secret scanning (API keys, tokens, private keys)
- Credential file permission warnings

Based on upstream v2.0.0. See [skills/here-now/SKILL.md](skills/here-now/SKILL.md) for full docs.

## Usage

Copy skills into your agent's skills directory:

```bash
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/* ~/.agents/skills/
```

For platform-specific setup guides, see [docs/](docs/).

## Recipes

Recipes are upstream integration playbooks from the *Claw ecosystem (OpenClaw, Hermes). Unlike skills, they are **not** agent-executable capabilities — they are reference material documenting production-hardened integration architectures and patterns.

Tracked read-only from upstream repos. See [docs/research-001-claw-recipes-vs-skills.md](docs/research-001-claw-recipes-vs-skills.md) for context on the recipe vs skill distinction.

### Synced from upstream repos

- **twilio-voice-brain** — Phone-to-knowledge pipeline via Twilio + voice AI. From [garrytan/gbrain](https://github.com/garrytan/gbrain).

## License

Apache 2.0
