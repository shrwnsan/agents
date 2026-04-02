# agents

Skills, tools, and configurations for NanoClaw agent containers.

## Skills

Container skills installed into `~/.claude/skills/` at runtime. Synced from `container/skills/` in the NanoClaw project.

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

These skills are installed into NanoClaw via `container/skills/`. The NanoClaw container-runner syncs them into each group's `~/.claude/skills/` at startup.

```bash
# Clone into NanoClaw's container skills
cd nanoclaw/container/skills
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/here-now ./here-now
cp -r /tmp/agents/skills/frontend-design ./frontend-design
rm -rf /tmp/agents
```
