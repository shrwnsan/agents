# Claw recipes vs skills

Research into the recipe/skill distinction in the OpenClaw/Hermes/*Claw ecosystem, and whether recipes are a standardized concept or an ad-hoc pattern.

Date: 2026-04-13
Sources: garrytan/gbrain, openclaw/openclaw, NousResearch/hermes-agent, JIGGAI/ClawRecipes, agentskills.io

## Ecosystem context

| Project | Stars | Role |
|---------|-------|------|
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 355k | Open-source personal AI assistant. Multi-channel gateway (WhatsApp, Telegram, Slack, etc.) with skill system. |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 65k | Personal AI agent with learning loop. OpenClaw-compatible (`hermes claw migrate`). |
| [garrytan/gbrain](https://github.com/garrytan/gbrain) | 5.9k | Personal knowledge brain (memex) that runs on top of OpenClaw or Hermes. Git-backed markdown files + pgvector retrieval. |

The `*Claw` ecosystem centers on OpenClaw as the agent harness and runtime. Skills, defined by the [AgentSkills spec](https://agentskills.io), are the standard way to distribute capabilities.

## Skills (the standard)

Skills are reusable procedural capabilities that teach the agent how to do something.

- **Format**: `SKILL.md` in a directory, with YAML frontmatter (`name`, `description`, optional `metadata`)
- **Spec**: [agentskills.io](https://agentskills.io), an open standard supported by OpenClaw, Hermes, and Claude Code
- **Lifecycle**: Invoked repeatedly as slash commands (e.g., `/briefing`, `/enrich`)
- **Discovery**: `/skills` command, [ClawHub](https://clawhub.ai) registry
- **Install**: `openclaw skills install <slug>`

Frontmatter reference: [docs/ref-001-skill-frontmatter.md](ref-001-skill-frontmatter.md)

## Recipes (emergent pattern)

Recipes are installation and integration playbooks that teach the agent how to set up an external capability end to end.

### GBrain's recipe format

Garry Tan's GBrain repo has 7 recipes in its `recipes/` directory as of 2026-04-13:

```yaml
---
id: twilio-voice-brain
name: Voice-to-Brain
version: 0.8.1
description: Phone calls create brain pages via Twilio + voice pipeline + GBrain MCP
category: sense
requires: [ngrok-tunnel]          # dependency on other recipes
secrets:                          # API keys with instructions
  - name: TWILIO_ACCOUNT_SID
    description: Twilio account SID (starts with AC)
    where: https://www.twilio.com/console
health_checks:                    # validation commands
  - 'curl -sf ... && echo OK || echo FAIL'
setup_time: 30 min
cost_estimate: "$15-25/mo"
---
```

Key properties:
- Written as **agent-executable instructions** ("You are the installer. Follow these instructions precisely.")
- Sequential with stop-points and validation after each step
- Handles credential collection, dependency resolution, and health checks
- Runs once or rarely to set up infrastructure, and skills then operate on that infrastructure

Available GBrain recipes: `calendar-to-brain`, `credential-gateway`, `email-to-brain`, `meeting-sync`, `ngrok-tunnel`, `twilio-voice-brain`, `x-to-brain`.

### JIGGAI's ClawRecipes format

[JIGGAI/ClawRecipes](https://github.com/JIGGAI/ClawRecipes) (97 stars, created 2026-02-09):

- Full OpenClaw plugin (`@jiggai/recipes`) with a CLI, a scaffolding engine, and a workflow runner
- Different frontmatter: `kind`, `requiredSkills`, `templates`, `files`, `tools`
- Different purpose: agent personas and team workflows, not integrations
- Supporting tools: ClawKitchen, a web dashboard, and ClawMarket, a marketplace

### Comparison

| Aspect | GBrain (Tan) | ClawRecipes (JIGGAI) |
|--------|-------------|---------------------|
| Created | Apr 2026 | Feb 2026 |
| Format | Single `.md` file | YAML + templates + scaffolding |
| Purpose | External integration setup | Agent personas and team workflows |
| Tooling | None (agent-executable markdown) | CLI, scaffolding, web dashboard |
| Cross-references | No | No |

## Community adoption status

### Official projects

| Project | "Recipe" in docs? | "Recipe" in code? |
|---------|-------------------|-------------------|
| openclaw/openclaw | No | No |
| NousResearch/hermes-agent | No | No |
| openclaw/clawhub | No | No |
| VoltAgent/awesome-openclaw-skills | No (only cooking recipes) | N/A |

**Neither OpenClaw nor Hermes recognizes "recipe" as a concept.**

### Broader signal

A GitHub search for "openclaw recipe" returns about 28 repos. Most are:
- Low-effort cookbook-style collections with 0-2 stars
- Web automation patterns

None of them include RFCs, working groups, or formal standardization proposals.

### Verdict

"Recipe" is an **emergent, fragmented pattern**, not a standardized concept:

- Two notable independent implementations (GBrain, ClawRecipes) with incompatible formats
- No cross-pollination between implementations
- No official recognition from OpenClaw or Hermes
- No community effort to unify or standardize
- GBrain's implementation is the most thoughtful, hardened in production and shaped by real deployment lessons, but it remains a personal convention

## Decision framework

From Garry Tan's "Thin Harness, Fat Skills" essay:

| Question | Answer | Use |
|----------|--------|-----|
| Agent needs to think, adapt, ask questions? | Yes | **Skill** |
| Same input always produces same output? | Yes | **Code** |
| Requires judgment about user's environment? | Yes | **Skill** |
| Setting up an external integration? | Yes | **Recipe** |
| One-time setup with credential collection? | Yes | **Recipe** |

Recipes produce the infrastructure that skills then operate on.

## Implications for this repo

Recipes are worth tracking as upstream references because their production patterns and architecture notes are useful. They are not worth adopting as a first-class concept unless the ecosystem standardizes them.

For now, this repo tracks selected recipes as read-only reference material in `recipes/`, separate from the `skills/` directory, which follows the agentskills.io standard.
