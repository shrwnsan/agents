# Agent Decomposition

Practical working norms for decomposing tasks across subagents. Derived from Claude Code's dynamic workflows feature — where the model writes task-specific JS harnesses spawning independent subagents — and the failure modes that emerge.

Source: x.com/trq212 — Claude Code dynamic workflows

## Failure Modes

Three recurrent failure patterns when delegating to subagents:

| Mode | Symptom | Fix |
|------|---------|-----|
| **Agentic laziness** | Skips steps, declares done after partial work | Re-scan task scope before closing. Count deliverables against requirements. |
| **Self-preferential bias** | Self-review confirms own output without scrutiny | Treat self-review conclusions as provisional. Seek independent verification for anything non-trivial. |
| **Goal drift** | Original constraints erode after context compaction or long sessions | Write requirements to a file immediately. Edge-case constraints ("don't do X") are the first to slip. |

### End-of-session checklist

Before closing a session, verify:
- Did I skip steps or declare done after partial work?
- Did I verify my own output, or just confirm what I produced?
- Are all original requirements still intact?

## Narrow Goal Principle

Every subagent gets **one specific goal**, not a multi-step mission.

- "Check if the scrape ran and report the status" — good
- "Fix the tracker" — too broad, invites scope creep

Narrow scope makes completion unambiguous and failure obvious.

## Decomposition Threshold

| Condition | Approach |
|-----------|----------|
| Task finishes in <3 tool calls | Handle inline |
| Work is parallelizable | Fan-out subagents |
| Needs independent review | Adversarial pair |
| Spans 5+ sequential steps | Pipeline decomposition |

If all answers to "does this need decomposition?" are "maybe" — do it inline.

## Patterns

| Pattern | Use when | How |
|---------|----------|-----|
| **Fan-out/fan-in** | Parallel independent subtasks | Spawn N agents, merge results in main agent |
| **Adversarial pair** | Output needs scrutiny | Agent A produces, Agent B reviews/critiques independently |
| **Tournament** | Choosing between options | Head-to-head comparison, ranked by independent evaluators |
| **Pipeline** | Sequential stages with clear boundaries | Each agent handles one phase, passes output to next |

## Persistence Over Conversation

If a task needs to survive across sessions, write state to a workspace file **immediately** — not "later." After context compaction, conversation-only requirements degrade. If it matters, it goes to disk.

## Pre-decomposition Checklist

Before spawning agents, ask:
1. Does this need parallel work?
2. Does it need independent review?
3. Is the token cost justified?

## Isolation

When subagents modify files, use `isolation: "worktree"` on the Agent tool. This gives each agent its own working tree — prevents conflicts and makes cleanup trivial (uncommitted worktrees are auto-deleted when the agent finishes).
