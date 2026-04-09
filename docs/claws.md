# Claw Integration

Claws are personal AI assistants that run agents ideally in isolated containers. It was popularize by the rise of OpenClaw (aka. Clawdis, Moltbot, and Clawdbot).

For our guide, we will share examples from [NanoClaw](https://github.com/qwibitai/nanoclaw).

Ideally each group (chat) gets its own container with a synced `~/.claude/skills/` directory.

## Setup

The container-runner syncs skills from `container/skills/` into each group's `~/.claude/skills/` at container startup:

```bash
cd nanoclaw/container/skills
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/here-now ./here-now
cp -r /tmp/agents/skills/frontend-design ./frontend-design
rm -rf /tmp/agents
```

## here-now Credentials

Each Claw group has isolated session data. The here-now skill reads credentials from `~/.herenow/credentials` inside the container, which maps to `data/sessions/{group}/.herenow/credentials` on the host.

**Groups are isolated** — credentials never enter containers; they're served at runtime via NanoClaw's credential proxy, which scopes keys to the requesting container. Each group needs its own credentials set up independently.

> This isolation depends on the credential proxy's integrity. Keep the proxy up to date and avoid exposing its port beyond the Docker bridge.

Recommended: store the API key in [Bitwarden Secrets Manager](https://bitwarden.com/products/secrets-manager/)/[OneCLI](https://www.onecli.sh/) and have the agent write it to `~/.herenow/credentials` at runtime. Since credentials never persist in the container, this ensures the key is only ever in memory during the session.

## Security Hardening Context

The here-now skill was hardened based on a security review with Nano (a NanoClaw agent). Key insight:

> Files that need the `file` command to identify their MIME type are often files that shouldn't be published to a public static site.

This led to a philosophy shift from "detect unknown types and upload" to "block unknown types by default, require explicit opt-in."

The hardening addressed six areas: dangerous extension blocking, suspicious extension warnings, pre-upload secret scanning, world-readable credential detection, unknown MIME type handling, and API key transport safety.
