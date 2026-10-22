# Why These Skills

The [catalog](../skills/README.md) says what is on the shelf. This page says why, so the next addition or removal can be judged against the same taste.

## The thesis

Left alone, an agent reaches for the median: the purple gradient, the plausible fix, the confident guess. Each skill here exists to pull one recurring job off the median and toward what a careful senior person would do.

The shelf is edited, not accumulated. Every skill costs something each time it loads: tokens, attention, and a chance to fire at the wrong moment. So the bar is not "useful." The bar is "worth loading on every agent I run."

## What earns a place

**A real job, done better.** Each skill answers work that keeps coming back, not work that might. [fare-verdict](../skills/fare-verdict/) and [vercel-domain-search](../skills/vercel-domain-search/) exist because real decisions needed better evidence. When a new skill does an old one's job better, the old one leaves in the same commit.

**Taste as a capability.** Design is the largest cluster because it is where agents most visibly default to slop. The skills split the work the way a good design team does. [frontend-design](../skills/frontend-design/) sets direction, [motion-craft](../skills/motion-craft/) executes, [no-ai-design-slop](../skills/no-ai-design-slop/) guards while building, [audit-ai-design-slop](../skills/audit-ai-design-slop/) reviews after, and [extract-design-tokens](../skills/extract-design-tokens/) reads taste off a live site. Making and judging stay separate roles: [dataviz](../skills/dataviz/) builds charts and [dataviz-tufte](../skills/dataviz-tufte/) critiques them, because the hand that made something rarely sees its flaws.

**Math where math decides, judgment where it must.** [fare-verdict](../skills/fare-verdict/) is arithmetic on Google's own price data, with no model in the loop. [skill-quality-gate](../skills/skill-quality-gate/) returns the same findings for the same input. [branch-hygiene](../skills/branch-hygiene/) shows its evidence before anything is deleted. Models judge only the fuzzy remainder, and uncertainty escalates to a person ([ADR-001](adr-001-advisory-judge-for-skill-quality-gate.md)).

**Honest scope.** A good skill says what it won't do. [sandboxed-run](../skills/sandboxed-run/) calls itself "process hygiene, not a jail." fare-verdict is not a booking tool. [nothing-design](../skills/nothing-design/) runs only when you name it. Overclaiming is a defect, and the quality gate checks for it.

**Safe by default.** Reversible beats fast. Trash instead of delete, read-only classification before cleanup, credential-free runs for untrusted code, secret scans before anything is published. Keyless wherever possible: a skill that wants your wallet or API key has to be worth that trust, and none of the Binance hub's wallet or trading skills were.

**Borrowed taste, earned trust.** We take freely from people whose craft we admire: Anthropic, Cloudflare, Emil Kowalski, MengTo. Every vendored skill is pinned to a recorded commit, read end to end, and run once in a sandbox before it lands. A version bump earns that trust again from scratch. Native skills fill the gaps upstream leaves.

**Context is a budget.** [caveman](../skills/caveman/) compresses replies. [handoff-context](../skills/handoff-context/) carries a thread forward without dragging all of it along. The same instinct drives rejections: `find-skills` was turned down for putting 5 KB in every prompt to save a one-line CLI call.

## The shape of the shelf

| Job | What it buys | For example |
|-----|--------------|-------------|
| Ship with craft | Work that doesn't look generated | frontend-design, motion-craft, no-ai-design-slop |
| Keep the code honest | Reviews, commits, and fixes a senior engineer would sign | review-pr, systematic-debugging, skill-quality-gate |
| Contain risk | Untrusted code and machines stay in their lane | sandboxed-run, security-audit, live-system-forensics |
| Ask the real world | Answers grounded in live data, not recall | fare-verdict, meta-search, og-social-cards |
| Keep momentum | Sessions and environments that pick up where they left off | handoff-context, caveman, docker-agent-browser |

## What we say no to

The [rejection log](../rejected-skills.json) is half the point. It is where taste is most legible: too narrow, auth for little gain, a duplicate of something better, or a behavior change everywhere for value somewhere. Each no is written down the day it's decided, with one line of why, so the next enthusiastic install doesn't reopen it.

## How it evolves

The shelf should get sharper, not bigger. Add a skill when a job keeps recurring and agents keep getting it wrong. Re-vet when upstream moves. Retire a skill once models have learned what it teaches; the generic anti-slop rules left the global AGENTS.md for exactly that reason ([ref-004](ref-004-agents-md-consolidation.md)).

One test covers most decisions: would a thoughtful lead want this loaded on every agent on the team?
