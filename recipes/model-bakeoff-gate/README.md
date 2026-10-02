---
id: model-bakeoff-gate
name: Model Bakeoff -> Calibrated Pre-Delete Guard
version: 0.2.2
description: Evaluate candidate models against a labeled ground-truth harness before trusting one with destructive automation, then wire the winner as a calibrated gate layered over deterministic checks. Three model families compared in one pass; each leg self-disables without its key. Ships its three harness files (lab.py, run_evals.py, guard.py) as real py_compile-checkable files; lab.py is the shared provider-failover module the runner and guard import.
category: verify
requires: [python3-3.10+, git]
secrets:
  - name: TYPESAFE_API_KEY
    description: TypeSafe AI key for the direct Jev leg (System One model - calibrated structured decisions)
    where: console.typesafe.ai - optional, leg self-disables without it
  - name: AI_GATEWAY_API_KEY
    description: Vercel AI Gateway key for the LLM baseline legs (gpt-4o-mini et al)
    where: Vercel dashboard > AI Gateway > API Keys - optional, leg self-disables without it
  - name: OPENROUTER_API_KEY
    description: OpenRouter key - third key-precedence leg for the System One contract (used when TYPESAFE_API_KEY and AI_GATEWAY_API_KEY are absent)
    where: openrouter.ai/keys - optional, leg self-disables without it
  - name: ZAI_BASE_URL_OPENAI + ZAI_MODEL + ZAI_API_KEY
    description: Optional BYOK direct-provider leg (e.g. Z.ai coding endpoint + glm-5.3-flash). LOCAL MACHINES ONLY - do not add these to CI
    where: your provider account - all three required for the leg, absence = leg skipped
health_checks:
  - "python3 guard.py --selftest && echo 'Guard deterministic layer: OK' || echo 'Guard selftest: FAIL'"
  - "python3 -m py_compile lab.py run_evals.py guard.py && echo 'Harness files: OK' || echo 'Harness compile: FAIL'"
  - "python3 -c 'from lab import make_jev_client' && echo 'lab import: OK' || echo 'lab import: FAIL'"
setup_time: 15 min
cost_estimate: "<$0.01 per full 7-case eval across all legs (Jev output free; LLM legs ~650-950 input + ~40-150 output tokens per call). Harness is local-first; CI use requires an explicit secrets decision."
---

# Model Bakeoff -> Calibrated Pre-Delete Guard

Two related capabilities in one recipe:

1. **Model bakeoff** - evaluate candidate models against a labeled
   ground-truth harness (7 cases, 3 question types) before trusting one with
   automated decisions. Accuracy is usually commoditized; the differentiators
   are **calibration honesty**, latency, and cost.
2. **Pre-delete guard** - a destructive-operation gate with layered authority:
   deterministic git checks hard-block first, the model judges only the
   genuinely fuzzy remainder (untracked content), and the system fails
   closed when the model is unavailable.

**Reference results** (7 labeled cases, macOS host, 2026-09): accuracy 7/7 on
all three legs - accuracy is commoditized. The differences: Jev hedged
identically across runs on ambiguous cases (confidence 0.26-0.61) while chat
LLMs asserted 1.0 unconditionally; Jev median latency ~850ms vs ~1.9s for the
gateway LLM; Jev output tokens free. Calibration honesty is a *design choice*
for guardrails: mid-band confidence lets a threshold route uncertain cases to
a human instead of silently proceeding.

## IMPORTANT: Instructions for the Agent

**You are the installer/operator.** Execute on behalf of the user. All model
legs self-disable when their keys are absent - the deterministic layers run
keyless, so CI never accidentally uses personal credentials.

**Stop points (pause and verify):**

- After Step 3: `guard.py --selftest` exits 0. If not, fix before evals.
- After Step 4: every enabled leg reports [OK]/[MISS] per case - never accept
  a run where all legs errored.
- Before Step 6: the user has confirmed the threshold policy (default 0.8).

**Step 1 - Prerequisites.** python3 and git. No pip installs - the harness is
stdlib-only (lab.py talks to every leg's uniform `/v1/systemone` endpoint via
urllib). Export whichever keys you have - every leg degrades independently,
and absent keys skip legs cleanly.

**Step 2 - Verify the harness files.** The three files ship in this
directory (`lab.py`, `run_evals.py`, `guard.py`); check them with
`python3 -m py_compile lab.py run_evals.py guard.py`.

**Step 3 - Verify the deterministic layer.** `python3 guard.py --selftest`
must print 10 OK lines and exit 0 (a fail-safe note when no key is set is
expected and correct).

**Step 4 - Run the bakeoff.** `python3 run_evals.py all` - one JSONL row per
leg per case lands in `results/run-<timestamp>.jsonl`. Keep these files; they
are your before/after record when models or pricing change.
(pr-gate evaluates real PRs: set `BAKEOFF_PR_REPO=<owner/repo>` to point it
at any GitHub repo with labeled PRs 10-12 - without it that leg skips cleanly.)

**Step 5 - Interpret.** Accuracy ties are expected on easy labeled sets; rank
legs by (a) confidence behavior on the *ambiguous* cases - mid-band honesty
beats confident wrongness for guardrails, (b) latency, (c) token cost.

**Step 6 - Wire the gate (optional).** `guard.py <branch> [--worktree <path>]`
exit codes: 0 safe (deterministic allow, or AI confident on soft signals),
1 hard block (deterministic, non-negotiable), 2 human review (model
uncertain or refuses), 3 fail-closed (AI unavailable or unconfigured on a
soft case), 4 usage. Default threshold 0.8. The AI layer can NEVER override a
deterministic block.

**Known gotchas baked into the harness:**

- The gateway's OpenAI-compatible endpoint rejects evaluation models on
  `/chat/completions` by design (400 "evaluation model, not a language
  model") - evaluation APIs have their own route; talk to them directly.
- BYOK legs strip terminal ANSI escapes from env values (copy-pasted model
  slugs often carry invisible escape codes -> "Unknown Model" 400s).
- Prompted-JSON mode (`structured_outputs=False`) is the portable path for
  custom OpenAI-compatible endpoints that ignore json_schema response_format.
- The guard's deterministic layer uses `git cherry` (patch-equivalence), not
  reachability: cherry-picked branches are mathematically safe and must not
  escalate. Never let the model re-derive what deterministic tooling proved.
- Selftest git operations are containment-checked (`rev-parse
  --show-toplevel` must resolve to the temp repo) - a missing cwd once
  leaked selftest commits into a real repo's main branch.
- The direct TypeSafe API serves the rolling aliases `jev-latest` and
  `jev-preview` (GET /v1/models); pinned slugs like `jev-1.13` are rejected
  with 400 "Unknown model". lab.py defaults to `jev-latest`.
- With no soft signals (clean worktree, nothing untracked) the guard's
  deterministic layer short-circuits to exit 0 WITHOUT an AI call - the AI
  layer only sees cases the math cannot settle.

## File: lab.py

Shared provider-failover harness module imported by both files above.
Key precedence: TYPESAFE_API_KEY -> AI_GATEWAY_API_KEY -> OPENROUTER_API_KEY;
no key at all -> make_jev_client() raises SystemExit, which callers catch to
degrade the leg (the harness contract: fail closed, never fail silent).

Shipped as [lab.py](lab.py) (252 lines). The surface the runner and guard use:

```python
class _JevResult:                      # answers, usage, latency_ms, leg
def ask(client: dict, questions: dict, state: str, adapter_model: str | None = None) -> _JevResult:
def make_jev_client() -> dict:
def make_gateway_llm_client(model: str) -> tuple[dict, str]:
def make_byok_legs() -> list:
```

(signatures only - bodies are in the file)

## File: run_evals.py

The bakeoff runner: two labeled eval legs, one JSONL row per leg per case
into `results/run-<timestamp>.jsonl`. Shipped as
[run_evals.py](run_evals.py) (307 lines).

```python
"""jev-lab runner: evaluates Jev (and gateway LLM baseline) on two labeled
decision tasks from a real-world workflow review.

Usage:
    python3 run_evals.py pr-gate
    python3 run_evals.py worktree-guard
    python3 run_evals.py all
"""
```

## File: guard.py

The pre-delete gate. Deterministic git checks are NON-NEGOTIABLE and decide
first; the model only judges soft signals the math cannot settle, and its
confidence drives the exit (default threshold 0.8). Shipped as
[guard.py](guard.py) (282 lines) - its module docstring is the contract:

```python
Authority model (important):
  - Deterministic checks are NON-NEGOTIABLE. Unique commits (per `git cherry`)
    or uncommitted worktree changes hard-block deletion. The AI layer can
    never override a hard block.
  - Jev only judges cases that pass the math: are the remaining soft signals
    (untracked files, submodule drift) safe? Its confidence drives the exit:
    conf >= threshold and "safe_delete" -> allow; anything else -> escalate.

Exit codes:
  0  safe to delete
  1  hard block (deterministic — unique work or uncommitted changes)
  2  human review (Jev uncertain, or Jev says keep)
  3  guard could not complete safely (AI layer unavailable on a soft case)
  4  usage error / branch not found

Usage:
  python3 guard.py <branch> [--repo PATH] [--worktree PATH] [--threshold 0.8] [--json]
```
