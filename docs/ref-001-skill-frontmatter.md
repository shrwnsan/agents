# SKILL.md Frontmatter Reference

Reference for YAML frontmatter fields recognized by skill clients. Covers the [agentskills.io](https://agentskills.io) open standard and Claude Code's official implementation.

Sources:
- agentskills.io spec: <https://github.com/agentskills/agentskills>
- Claude Code docs: <https://code.claude.com/docs/en/skills#frontmatter-reference>
- Claude Code best practices: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>

## Open Standard (agentskills.io)

Six fields. Any agent implementing the standard should recognize these.

| Field | Required | Constraints | Notes |
|-------|----------|-------------|-------|
| `name` | Yes | Max 64 chars. Lowercase alphanumeric + hyphens. Must match directory name. | |
| `description` | Yes | Max 1024 chars. Should describe what + when. | |
| `license` | No | License name or file reference. | |
| `compatibility` | No | Max 500 chars. Free-text environment requirements. | e.g. "Requires git, docker, jq" |
| `metadata` | No | Arbitrary string-to-string key-value map. | Escape hatch for custom data. Use unique key names. |
| `allowed-tools` | No | Space-delimited tool list (experimental). | e.g. `allowed-tools: Bash(git:*) Read` |

## Claude Code Extension

Claude Code supports all agentskills.io fields **plus** these additional fields. Other clients will ignore them.

| Field | Required | Description |
|-------|----------|-------------|
| `argument-hint` | No | Placeholder shown when invoking (e.g. `[issue-number]`). |
| `disable-model-invocation` | No | `true` prevents Claude from auto-triggering. User must invoke via `/name`. |
| `user-invocable` | No | `false` hides from `/` menu. Use for background knowledge skills. |
| `model` | No | Override model when skill is active. |
| `effort` | No | Effort level: `low`, `medium`, `high`, `max`. |
| `context` | No | `fork` or `agent` — runs skill in isolated subagent. |
| `hooks` | No | Hook configuration within the skill. |
| `paths` | No | Path-specific rules. |
| `shell` | No | Shell to use: `bash` or `powershell`. |

## Differences Summary

| Concern | agentskills.io | Claude Code |
|---------|---------------|-------------|
| `name` | Required | Optional (falls back to directory name) |
| `description` | Required, max 1024 chars | Recommended, truncated at 250 chars in listing |
| `allowed-tools` format | Space-delimited string | Space-separated string **or** YAML list |
| `user-invocable` | Not defined | `false` hides from `/` menu |
| `disable-model-invocation` | Not defined | `true` prevents auto-trigger |
| `metadata` | Arbitrary KV map | Recognized but no specific keys defined |

## Agent-Specific Targeting

There is no standard field for targeting skills at specific agents or platforms. The recommended approaches:

1. **`compatibility`** (standard, free-text) — human-readable, not machine-parseable.
   ```yaml
   compatibility: Designed for Claude Code
   ```

2. **`metadata`** (standard, arbitrary KV) — the spec's official escape hatch.
   ```yaml
   metadata:
     agent_affinity: nanoclaw
     upstream: heredotnow/skill
     upstream_version: "1.11.0"
   ```

3. **Claude Code-specific fields** — `disable-model-invocation`, `user-invocable`, etc. Only recognized by Claude Code, ignored by other clients.

## Current Skill Compliance

| Skill | agentskills.io compliant | Claude Code compliant | Notes |
|-------|------------------------|----------------------|-------|
| crafting-commits | Yes | Yes | Uses `user-invocable` (CC extension) |
| handoff-context | Yes | Yes | Uses `user-invocable`, `disable-model-invocation` (CC extensions) |
| systematic-debugging | Yes | Yes | Uses `user-invocable` (CC extension) |
| meta-search | Yes | Yes | Standard fields only |
| frontend-design | Yes | Yes | Standard fields only |
| here-now | Yes | Yes | Standard fields only |
