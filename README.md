# agents

Skills, tools, and configurations for AI agent containers.

## Skills

Skills are self-contained packages with a `SKILL.md` instruction file and optional scripts/binaries. They are loaded by agents that support the `~/.agents/skills/` convention.

### here-now (hardened)

Publish files to live URLs via [here.now](https://here.now). Security-hardened fork of [heredotnow/skill](https://github.com/heredotnow/skill).

- Blocks dangerous file types (`.env`, `.pem`, `.key`, etc.)
- Warns on suspicious types (`.bak`, `.tmp`, no extension)
- Pre-upload secret scanning (API keys, tokens, private keys)
- No `file` command dependency — unknown types blocked instead of detected
- Bundled `jq` binary — no system dependency
- Credential file permission warnings

Based on upstream v1.11.0. See [skills/here-now/SKILL.md](skills/here-now/SKILL.md) for full docs.

### frontend-design

Guides creation of distinctive, production-grade frontend interfaces that avoid generic AI aesthetics. From [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official).

## Usage

Copy skills into your agent's skills directory:

```bash
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/* ~/.agents/skills/
```

For platform-specific setup guides, see [docs/](docs/).

## License

Apache 2.0
