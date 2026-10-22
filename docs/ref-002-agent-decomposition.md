# Agent decomposition

These are working norms for splitting tasks across subagents. They come from Claude Code's dynamic workflows feature, in which the model writes a task-specific JavaScript program that spawns independent subagents, and from the ways that setup fails.

Source: x.com/trq212 on Claude Code dynamic workflows

## Failure modes

Delegating to subagents fails in three recurring ways:

| Mode | Symptom | Fix |
|------|---------|-----|
| **Agentic laziness** | Skips steps, declares done after partial work | Re-scan task scope before closing. Count deliverables against requirements. |
| **Self-preferential bias** | Self-review confirms the agent's own output without scrutiny | Treat self-review conclusions as provisional. Seek independent verification for anything non-trivial. |
| **Goal drift** | Original constraints erode after context compaction or long sessions | Write requirements to a file immediately. Edge-case constraints ("don't do X") are the first to slip. |

### End-of-session checklist

Before closing a session, verify:
- Did I skip steps or declare done after partial work?
- Did I verify my own output, or just confirm what I produced?
- Are all original requirements still intact?

## Narrow goal principle

Every subagent gets **one specific goal**, not a multi-step mission.

- Good: "Check if the scrape ran and report the status"
- Too broad: "Fix the tracker". It invites scope creep.

Narrow scope makes completion unambiguous and failure obvious.

## Decomposition threshold

| Condition | Approach |
|-----------|----------|
| Task finishes in fewer than 3 tool calls | Handle inline |
| Work is parallelizable | Fan out to subagents |
| Needs independent review | Adversarial pair |
| Spans 5+ sequential steps | Pipeline decomposition |

If every answer to "does this need decomposition?" is "maybe", do it inline.

## Patterns

| Pattern | Use when | How |
|---------|----------|-----|
| **Fan-out/fan-in** | Parallel independent subtasks | Spawn N agents, merge results in main agent |
| **Adversarial pair** | Output needs scrutiny | Agent A produces the output, and Agent B reviews and critiques it independently |
| **Tournament** | Choosing between options | Head-to-head comparison, ranked by independent evaluators |
| **Pipeline** | Sequential stages with clear boundaries | Each agent handles one phase and passes its output to the next |

## Persistence over conversation

If a task needs to survive across sessions, write its state to a workspace file immediately, not "later." Requirements that live only in the conversation degrade after context compaction. Write anything that matters to disk.

## Pre-decomposition checklist

Before spawning agents, ask:
1. Does this need parallel work?
2. Does it need independent review?
3. Is the token cost justified?

## Isolation

When subagents modify files, use `isolation: "worktree"` on the Agent tool. Each agent then gets its own working tree. That prevents conflicts and makes cleanup trivial, because uncommitted worktrees are deleted automatically when the agent finishes.


## Adopting

Add this to your agent's working norms as a section in CLAUDE.local.md, or save it as a fragment that loads automatically:

### As a fragment that loads every session

Save it as `.claude-fragments/module-agent-decomposition.md` and add this line to CLAUDE.md:

```md
@./.claude-fragments/module-agent-decomposition.md
```

### As a per-group local norm

Append this to CLAUDE.local.md:

```md
## Agent Decomposition (x.com/trq212 — Claude Code dynamic workflows)

### Failure mode checklist
Before closing a session, check:
- **Laziness:** Did I skip steps or declare done after partial work? Re-scan the task scope.
- **Self-preferential bias:** Did I verify my own output? If self-reviewing, treat conclusions as provisional.
- **Goal drift:** Are all original requirements still intact? After compaction, edge-case constraints ("don't do X") are the first to slip.

### Narrow goal principle
Every subagent gets ONE specific goal, not a multi-step mission. "Check if scrape ran" not "fix the tracker." Narrow scope makes completion unambiguous.

### Decomposition threshold
Handle inline if task finishes in <3 tool calls. Consider decomposition when work is parallel, needs independent review, or spans 5+ sequential steps.

### Pattern vocabulary
- **Fan-out/fan-in** — parallel subtasks, merge results
- **Adversarial pair** — independent agent reviews/critiques output
- **Tournament** — rank options via head-to-head comparison
- **Pipeline** — sequential stages, each agent handles one phase

### Persistence over conversation
If a task needs to survive across sessions, write state to a workspace file immediately — not "later." After compaction, conversation-only requirements degrade.

### Pre-decomposition checklist
Before spawning agents: Does this need parallel work? Independent review? Is token cost justified? If all answers are "maybe," do it inline.

### Isolation
Use `isolation: "worktree"` on Agent tool when subagents modify files — prevents conflicts and makes cleanup trivial.
```

Don't use MEMORY.md for this. That file is for recall data, not behavioral instructions.
