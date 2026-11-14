# agents

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![Skills: 37](https://img.shields.io/badge/skills-37-green.svg)
[![skills.sh](https://skills.sh/b/shrwnsan/agents)](https://skills.sh/shrwnsan/agents)

Personal hub for AI agent skills, prompts, and configurations.

## Skills

Each skill is a self-contained package: a `SKILL.md` instruction file plus optional scripts or binaries. Any agent that supports the `~/.agents/skills/` convention can load them.

[skills/README.md](skills/README.md) has the full catalog of 37 skills across Development, Design & Content, Workflow, Security, System, and Crypto. It lists each skill's source and provenance pin, plus the rules for adding one. [rejected-skills.json](rejected-skills.json) records the candidates we evaluated and turned down. [Why these skills](docs/ref-005-why-these-skills.md) explains the standard behind both.

A GitHub Actions workflow syncs skills from vibekit automatically. Other upstream skills sync when someone runs [sync-upstream](.github/workflows/sync-upstream.yml) by hand, using the sources in [.upstream.yml](.upstream.yml).

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

`global/AGENTS.md` is the published copy. The live one is `~/.agents/AGENTS.md`. Edit that, then copy it here to publish.

Don't link Gemini CLI or Qwen Code. Their memory tools append to their global files, which would write into the shared rules.

Pi gets its harness customizations from the companion repo [shrwnsan/pi-agent](https://github.com/shrwnsan/pi-agent): pi extensions, TUI themes, and pi-subagents agent variants. That repo's planned `skills/` directory stays empty on purpose; the skills catalogue is this repo's `skills/`, shared across harnesses.

## Recipes

Recipes are integration playbooks. Agents don't execute them the way they run skills. They are reference material that documents integration architectures and patterns proven in production. See [docs/research-001-claw-recipes-vs-skills.md](docs/research-001-claw-recipes-vs-skills.md) for the recipe vs skill distinction.

### Maintained in this repo

- [model-bakeoff-gate](recipes/model-bakeoff-gate/) is a pre-deletion guard and model bakeoff harness for risky agent actions. Deterministic git checks block first, and a model call judges only the cases they can't decide. Providers fail over from TypeSafe Jev to Vercel AI Gateway to OpenRouter, and with no keys the guard fails closed. Its three runnable files (`lab.py`, `run_evals.py`, `guard.py`) live under `scripts/` and need only the Python standard library.
- [listening-post](recipes/listening-post.md) captures a logged-in web community you belong to through your own browser, over a temporary tailnet connection. Sessions stay under an hour and back off on rate limits. It sanitizes content as it ingests it and ships a committed classifier calibration. It needs no API keys.

### Synced from upstream repos

All three come from [garrytan/gbrain](https://github.com/garrytan/gbrain). We track them read-only: [sync-upstream](.github/workflows/sync-upstream.yml) refreshes them weekly (also runnable by hand), and [recipes/PROVENANCE.md](recipes/PROVENANCE.md) records where each copy came from.

The list also tells the story of how it got this way. [twilio-voice-brain](recipes/twilio-voice-brain.md) was our first tracked recipe, vendored in April 2026 as a phone-calls-to-knowledge-base runbook. In May 2026 gbrain deprecated it: the voice stack moved to [agent-voice](recipes/agent-voice.md), a WebRTC-first reference that installs by copying into your own agent repo, and the tunnel setup that twilio-voice-brain depended on became a standalone [ngrok-tunnel](recipes/ngrok-tunnel.md) recipe. We picked up both successors in November 2026. twilio-voice-brain stays tracked as a frozen redirect for existing installs until upstream deletes it, at which point we archive our copy and stop syncing it.

- [agent-voice](recipes/agent-voice.md) is a WebRTC-first voice agent reference with Mars and Venus personas. Its install copies the code into your own agent repo, where you own the edits, and ships a read-only tool router plus a voice-post-call skill. This is the successor to twilio-voice-brain.
- [ngrok-tunnel](recipes/ngrok-tunnel.md) publishes a fixed public URL for a local brain or voice agent through ngrok, with health checks and a watchdog. It is the tunnel setup that the old twilio recipe carried, now maintained on its own upstream.
- [twilio-voice-brain](recipes/twilio-voice-brain.md) connects phone calls to a knowledge base through Twilio and a voice AI. It is deprecated upstream: frozen since 2026-05-23, kept only as a redirect for existing installs, and scheduled for removal. We keep tracking it until upstream deletes it; new installs should use [agent-voice](recipes/agent-voice.md).

## License

Apache 2.0
