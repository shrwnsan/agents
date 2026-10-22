# Agent PR review framework

This doc maps agent failure modes across two approaches that complement each other: proactive decomposition (ref-002) and reactive review of agent output (from a GitHub Engineering article).

Source: github.blog/2025-06-05-agent-pull-requests-are-everywhere-heres-how-to-review-them

## Two angles, one problem

| Approach | Scope | When it acts |
|----------|-------|-------------|
| **Proactive decomposition** (ref-002) | How to structure agent work before it runs | Upfront. Design the system so its structure suppresses failure modes |
| **Reactive PR review** (this doc) | How to evaluate agent output after it runs | After the fact. Catch what slips through |

Neither is enough alone. Good decomposition leaves fewer places for failures to occur, and good review catches the rest.

## Mapping red flags to decomposition

| PR review red flag | What it looks like | Decomposition response |
|-------------------|---------------------|----------------------|
| **Code reuse blindness** | Agent copies existing patterns without understanding why they exist | Adversarial pair. Gilfoyle reviews independently and catches cargo-culted code |
| **Hallucinated correctness** | Agent adds tests that pass but don't test the fix | Adversarial pair, which targets the self-preferential bias failure mode from ref-002. Independent review treats agent claims as provisional |
| **Agentic ghosting** | Agent addresses part of the request, silently ignores the rest | Narrow goal principle. Agents that lose scope get cut, and the pre-decomposition checklist flags ambiguous requirements |
| **Untrusted input** | Agent trusts scraped data, user input, or API responses without validation | The adversarial reviewer's checklist includes a security review |
| **CI gaming** | Agent writes tests to pass CI, not to verify correctness | Resilience checks in the pipeline pattern. The review stage validates intent, not just coverage |

## Reactive review checklist for a 10-minute agent PR review

From the GitHub article, adapted for our workflow:

1. **Scope check.** Does the PR address the full request, or did the agent ghost part of it?
2. **Correctness check.** Do the tests check the fix, or do they only pass? Read them.
3. **Reuse check.** Is copied code appropriate for this context, or cargo-culted?
4. **Input validation.** Does the code validate external inputs such as API responses, user data, and scraped content?
5. **CI integrity.** Does the CI config verify quality, or has the agent gamed it?

## When to use which

| Signal | Action |
|--------|--------|
| Reviewing a PR from an unknown agent | Full reactive checklist |
| Reviewing output from our adversarial pair | Skip checks 2 and 3. Gilfoyle already caught these |
| Setting up a new agent workflow | Start with proactive decomposition, then add reactive review as a safety net |
| Agent produces consistently clean PRs | Trim the reactive checklist, since the pattern is working |

## Link to ref-002

See [ref-002-agent-decomposition.md](ref-002-agent-decomposition.md) for the proactive framework: failure modes, narrow goal principle, decomposition thresholds, and interaction patterns (fan-out/fan-in, adversarial pair, tournament, pipeline).
