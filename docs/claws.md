# Claw integration

Claws are personal AI assistants that run agents, ideally in isolated containers. OpenClaw, also known as Clawdis, Moltbot, and Clawdbot, made them popular.

This guide uses examples from [NanoClaw](https://github.com/qwibitai/nanoclaw).

Ideally each group, meaning each chat, gets its own container with a synced `~/.claude/skills/` directory.

## Setup

The container-runner syncs skills from `container/skills/` into each group's `~/.claude/skills/` at container startup:

```bash
cd nanoclaw/container/skills
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/here-now ./here-now
cp -r /tmp/agents/skills/frontend-design ./frontend-design
rm -rf /tmp/agents
```

## here-now credentials

Each Claw group has isolated session data. The here-now skill reads credentials from `~/.herenow/credentials` inside the container, which maps to `data/sessions/{group}/.herenow/credentials` on the host.

Groups are isolated from each other. Credentials never enter containers. NanoClaw's credential proxy serves them at runtime and scopes each key to the requesting container. Set up credentials separately for each group.

> This isolation depends on the credential proxy's integrity. Keep the proxy up to date and avoid exposing its port beyond the Docker bridge.

We recommend storing the API key in [Bitwarden Secrets Manager](https://bitwarden.com/products/secrets-manager/) or [OneCLI](https://www.onecli.sh/) and having the agent write it to `~/.herenow/credentials` at runtime. Credentials never persist in the container, so the key exists only in memory during the session.

## Security hardening context

We hardened the here-now skill after a security review with Nano, a NanoClaw agent. The main finding was:

> Files that need the `file` command to identify their MIME type are often files that shouldn't be published to a public static site.

This changed the upload policy from "detect unknown types and upload" to "block unknown types by default, require explicit opt-in."

The hardening addressed six areas: dangerous extension blocking, suspicious extension warnings, pre-upload secret scanning, world-readable credential detection, unknown MIME type handling, and API key transport safety.
