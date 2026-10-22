# SKILL.md frontmatter reference

This page lists the YAML frontmatter fields that skill clients recognize. It covers the [agentskills.io](https://agentskills.io) open standard and Claude Code's official implementation.

Sources:
- agentskills.io spec: <https://github.com/agentskills/agentskills>
- Claude Code docs: <https://code.claude.com/docs/en/skills#frontmatter-reference>
- Claude Code best practices: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>

## Open standard (agentskills.io)

The standard defines six fields. Any agent that implements the standard should recognize them.

| Field | Required | Constraints | Notes |
|-------|----------|-------------|-------|
| `name` | Yes | Max 64 chars. Lowercase alphanumeric characters and hyphens. Must match the directory name. | |
| `description` | Yes | Max 1024 chars. Should describe what the skill does and when to use it. | |
| `license` | No | License name or file reference. | |
| `compatibility` | No | Max 500 chars. Free-text environment requirements. | e.g. "Requires git, docker, jq" |
| `metadata` | No | Arbitrary string-to-string key-value map. | The place for custom data. Use unique key names. |
| `allowed-tools` | No | Space-delimited tool list. Experimental. | e.g. `allowed-tools: Bash(git:*) Read` |

## Claude Code extension

Claude Code supports all agentskills.io fields plus the fields below. Other clients ignore them.

| Field | Required | Description |
|-------|----------|-------------|
| `argument-hint` | No | Placeholder shown when invoking (e.g. `[issue-number]`). |
| `disable-model-invocation` | No | `true` stops Claude from triggering the skill on its own. The user must invoke it with `/name`. |
| `user-invocable` | No | `false` hides the skill from the `/` menu. Use it for background knowledge skills. |
| `model` | No | Overrides the model while the skill is active. |
| `effort` | No | Effort level: `low`, `medium`, `high`, `max`. |
| `context` | No | `fork` or `agent`. Runs the skill in an isolated subagent. |
| `hooks` | No | Hook configuration within the skill. |
| `paths` | No | Path-specific rules. |
| `shell` | No | Shell to use: `bash` or `powershell`. |

## Differences summary

| Concern | agentskills.io | Claude Code |
|---------|---------------|-------------|
| `name` | Required | Optional, falls back to the directory name |
| `description` | Required, max 1024 chars | Recommended, truncated at 250 chars in listing |
| `allowed-tools` format | Space-delimited string | Space-separated string or YAML list |
| `user-invocable` | Not defined | `false` hides the skill from the `/` menu |
| `disable-model-invocation` | Not defined | `true` prevents automatic triggering |
| `metadata` | Arbitrary key-value map | Recognized but no specific keys defined |

## Agent-specific targeting

No standard field targets skills at specific agents or platforms. Use one of these approaches instead:

1. **`compatibility`** is a standard free-text field. People can read it, but tools can't parse it.
   ```yaml
   compatibility: Designed for Claude Code
   ```

2. **`metadata`** is a standard map with arbitrary keys. The spec designates it for custom data.
   ```yaml
   metadata:
     agent_affinity: nanoclaw
     upstream: heredotnow/skill
     upstream_version: "1.11.0"
   ```

3. **Claude Code-specific fields**, such as `disable-model-invocation` and `user-invocable`, work only in Claude Code. Other clients ignore them.

## Current skill compliance

| Skill | agentskills.io compliant | Claude Code compliant | Notes |
|-------|------------------------|----------------------|-------|
| crafting-commits | Yes | Yes | Uses `user-invocable`, a Claude Code extension |
| handoff-context | Yes | Yes | Uses `user-invocable` and `disable-model-invocation`, both Claude Code extensions |
| systematic-debugging | Yes | Yes | Uses `user-invocable`, a Claude Code extension |
| meta-search | Yes | Yes | Standard fields only |
| frontend-design | Yes | Yes | Standard fields only |
| here-now | Yes | Yes | Standard fields only |
