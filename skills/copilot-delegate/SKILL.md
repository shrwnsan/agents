---
name: copilot-delegate
license: Apache-2.0
compatibility: Requires the GitHub Copilot CLI (@github/copilot, version-pinned) installed and authenticated once via interactive device flow, and an active Copilot plan—every call consumes the plan's premium-request quota. The wrapper uses python3 stdlib only and makes no network calls of its own; the pinned CLI does all talking to GitHub.
metadata:
  author: shrwnsan
  version: "1.0.0"
description: "Use when the user asks to run a task on GitHub Copilot, spend Copilot plan quota on a subtask, get a second model's answer for comparison, or hand bounded work to the copilot CLI from any agent. Not for questions about what Copilot is, its pricing, or its plans—answer those directly."
---

# Copilot Delegate

## Overview

Hand a bounded subtask to the GitHub Copilot CLI and treat the answer as
untrusted input until it passes a check you control. Ad-hoc `copilot -p` calls
have four recurring failure modes: the delegate edits your repo because a
blanket permission flag was easier, the answer comes back as prose nobody can
validate, nobody tracks how much quota the delegation burned, and secrets ride
along in the prompt. This skill exists to close those four holes. The wrapper
`scripts/copilot_delegate.py` is the whole mechanism—one stdlib script, one
JSONL ledger, no daemon.

Delegation is worth it when a second model's answer is cheap insurance
(reference implementations, cross-checks, bulk boilerplate) and the caller has
a mechanical way to verify the result. It is not worth it for judgment calls
with no verifiable output.

## Preflight

```bash
python3 scripts/copilot_delegate.py check
```

Reports CLI presence, the pinned version in use, auth state (read-only—the
script never starts a login), and ledger writability. If the CLI is missing,
install it pinned and record the pin:

```bash
npm install -g @github/copilot@1.0.105   # replace with the operator's chosen pin
```

Unpinned installs (bare `npx @github/copilot`) are a mutable-reference
hazard—the bytes you vetted are not the bytes you run next week. If auth is
missing, stop and tell the operator to run `copilot` once interactively; the
device flow needs a browser and cannot be scripted from here.

## Run one delegation

```bash
python3 scripts/copilot_delegate.py run \
  --task-label "refund-policy boilerplate" \
  --model "Claude Sonnet 4.5" \
  --timeout 300 \
  --check-command "python3 -m pytest tests/test_refund.py -q" \
  -- "Write a Python function refund_eligible(order_date, policy_days) that returns True when the order is inside the window. Include only the function."
```

What the wrapper does, in order:

1. **Permission posture.** Runs `copilot -p` with no tool-permission flags by
   default. The current CLI requires `--allow-all-tools` before it will run
   tools in prompt mode—so inference-only delegations (the default) cannot
   touch your files at all. When a task genuinely needs tools, the operator
   passes `--need-tools` explicitly and the wrapper forwards
   `--allow-all-tools`; run those delegations inside the `sandboxed-run`
   skill, never against a working tree you care about. The wrapper refuses to
   construct `--share`, `--share-gist`, or `--enable-memory` calls under any
   flag combination.
2. **Output contract.** The prompt is sent with a fixed suffix requiring the
   final fenced block to be one JSON object:
   `{"answer": string, "assumptions": [string], "confidence": "low"|"medium"|"high"}`.
   The wrapper extracts the last fenced block, parses it, and validates the
   shape. One automatic retry with a stricter "JSON only" instruction on
   parse failure; a second failure exits 3.
3. **Caller check.** With `--check-command`, the wrapper runs your verification
   after a parseable answer. On failure it retries once, appending the check's
   output tail to the prompt. A second failure exits 3: do the task locally
   instead—the delegate has had its chance.
4. **Ledger.** Appends one JSON line per attempt
   (`{ts, label, model, seconds, exit, check}`) to
   `$COPILOT_DELEGATE_LEDGER` (default
   `~/.config/copilot-delegate/ledger.jsonl`). Every call burns premium
   requests from the plan; the ledger is how burn stays visible. A failed
   ledger write warns loudly but never kills the task.

Spend summary:

```bash
python3 scripts/copilot_delegate.py report            # last 7 days
python3 scripts/copilot_delegate.py report --days 30
```

## Exit codes

| Code | Meaning | Caller action |
|---|---|---|
| 0 | Answer parsed and check passed | Use it—still read `assumptions` |
| 2 | CLI missing or not authenticated | Fix the environment, not the prompt |
| 3 | Contract or check failed twice | Do the task locally; stop delegating this one |
| 4 | Quota or rate limiting detected | Stop; retrying burns nothing and gains nothing |
| 5 | Timeout | Raise `--timeout` only if the task is genuinely long |
| 6 | Other CLI failure | Read stderr; usually a flag or version mismatch |

## Data boundary

The prompt and every file the delegate reads travel to GitHub's cloud. Before
delegating: strip secrets, tokens, credentials, and customer data from the
prompt—state the shape of the data instead of pasting it. Private repo code is
an operator decision, not a default: point the delegate at named files, not a
whole tree. The CLI sends its own telemetry; the wrapper passes
`--disable-client-telemetry` by default, and server-side handling is GitHub's
policy, not ours. Transcripts stay local unless a human passes `--share`
explicitly—the wrapper never will.

## Model choice

`--model` values are plan- and catalog-dependent; run `copilot` interactively
and use `/model` to see what the plan actually offers, then pin that exact
string in scripts. `auto` is convenient and non-deterministic—avoid it where
the ledger's value depends on comparing like with like.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `check` says not authenticated | Device flow never completed or token expired | Operator runs `copilot` once, interactively |
| CLI demands `--allow-all-tools` on an inference-only run | Older CLI builds require it unconditionally | Pass `--need-tools` plus `sandboxed-run`, or upgrade the CLI pin |
| Answer is prose with the JSON missing | Model ignored the contract twice | Exit 3; rephrase the task tighter or do it locally |
| `check-command` fails identically twice | Task was under-specified or beyond the model | Exit 3 is the system working; do it locally |
| Ledger line missing but the call ran | Ledger path unwritable | Fix `$COPILOT_DELEGATE_LEDGER`; burn happened regardless |

## Scope

One-shot delegations with a mechanical pass/fail check. Multi-step agent
sessions, custom agents (`--agent`), MCP servers, and the Copilot SDK are out
of scope here—configure those directly once a delegation pattern proves out.
The flag surface this skill relies on was verified against CLI 1.0.105; see
[references/flags.md](references/flags.md) before forwarding any flag the
wrapper does not already handle.
