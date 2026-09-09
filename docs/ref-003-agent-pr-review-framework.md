# Agent PR Review Framework

Mapping agent failure modes across two complementary approaches: proactive decomposition (ref-002) and reactive output review (GitHub Engineering article).

Source: github.blog/2025-06-05-agent-pull-requests-are-everywhere-heres-how-to-review-them

## Two Angles, One Problem

| Approach | Scope | When it acts |
|----------|-------|-------------|
| **Proactive decomposition** (ref-002) | How to structure agent work before it runs | Upfront—design the system so failure modes are structurally suppressed |
| **Reactive PR review** (this doc) | How to evaluate agent output after it runs | After the fact—catch what slips through |

Neither is sufficient alone. Good decomposition reduces the attack surface; good review catches what remains.

## Red Flag → Decomposition Mapping

| PR Review Red Flag | What It Looks Like | Decomposition Response |
|-------------------|---------------------|----------------------|
| **Code reuse blindness** | Agent copies existing patterns without understanding why they exist | Adversarial pair—Gilfoyle reviews independently, catches cargo-culted code |
| **Hallucinated correctness** | Agent adds tests that pass but don't actually test the fix | Same—self-preferential bias failure mode from ref-002; independent review treats agent claims as provisional |
| **Agentic ghosting** | Agent addresses part of the request, silently ignores the rest | Narrow goal principle—agents that lose scope get cut; pre-decomposition checklist flags ambiguous requirements |
| **Untrusted input** | Agent trusts scraped data, user input, or API responses without validation | Security review baked into adversarial reviewer's checklist |
| **CI gaming** | Agent writes tests to pass CI, not to verify correctness | Resilience checks in pipeline pattern; review stage validates intent, not just coverage |

## Reactive Review Checklist (10-minute agent PR review)

From the GitHub article, adapted for our workflow:

1. **Scope check** — Does the PR address the full request, or did the agent ghost part of it?
2. **Correctness check** — Do tests actually test the fix, or just pass? Read them.
3. **Reuse check** — Is copied code appropriate for this context, or cargo-culted?
4. **Input validation** — Are external inputs (API responses, user data, scraped content) validated?
5. **CI integrity** — Does the CI config actually verify quality, or is it gamed?

## When to Use Which

| Signal | Action |
|--------|--------|
| Reviewing a PR from an unknown agent | Full reactive checklist |
| Reviewing output from our adversarial pair | Skip #2 and #3—Gilfoyle already caught these |
| Setting up a new agent workflow | Proactive decomposition first, then add reactive review as safety net |
| Agent produces consistently clean PRs | Trim reactive checklist—pattern is working |

## Link to ref-002

See [ref-002-agent-decomposition.md](ref-002-agent-decomposition.md) for the proactive framework: failure modes, narrow goal principle, decomposition thresholds, and interaction patterns (fan-out/fan-in, adversarial pair, tournament, pipeline).
