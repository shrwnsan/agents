---
id: model-bakeoff-gate
name: Model Bakeoff -> Calibrated Pre-Delete Guard
version: 0.1.0
description: Evaluate candidate models against a labeled ground-truth harness before trusting one with destructive automation, then wire the winner as a calibrated gate layered over deterministic checks. Three model families compared in one pass; each leg self-disables without its key.
category: verify
requires: [python3-3.10+, git, pip]
secrets:
  - name: TYPESAFE_API_KEY
    description: TypeSafe AI key for the direct Jev leg (System One model - calibrated structured decisions)
    where: console.typesafe.ai - optional, leg self-disables without it
  - name: AI_GATEWAY_API_KEY
    description: Vercel AI Gateway key for the LLM baseline legs (gpt-4o-mini et al)
    where: Vercel dashboard > AI Gateway > API Keys - optional, leg self-disables without it
  - name: ZAI_BASE_URL_OPENAI + ZAI_MODEL + ZAI_API_KEY
    description: Optional BYOK direct-provider leg (e.g. Z.ai coding endpoint + glm-5.3-flash). LOCAL MACHINES ONLY - do not add these to CI
    where: your provider account - all three required for the leg, absence = leg skipped
health_checks:
  - "python3 guard.py --selftest && echo 'Guard deterministic layer: OK' || echo 'Guard selftest: FAIL'"
  - "python3 -c 'import typesafe_sdk, system_one_adapter' 2>/dev/null && echo 'SDKs: OK' || echo 'SDKs missing - pip install typesafe-sdk system-one-adapter[openai]'"
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

**Step 1 - Prerequisites.** python3, git, and
`pip install typesafe-sdk 'system-one-adapter[openai]'` (SDK imports are lazy;
keyless legs still run). Export whichever keys you have - every leg degrades
independently, and absent keys skip legs cleanly.

**Step 2 - Write the two harness files** exactly as given below
(`run_evals.py`, `guard.py` - lab code is inlined), then
`python3 -m py_compile run_evals.py guard.py`.

**Step 3 - Verify the deterministic layer.** `python3 guard.py --selftest`
must print 5 OK lines and exit 0 (a fail-safe note when no key is set is
expected and correct).

**Step 4 - Run the bakeoff.** `python3 run_evals.py all` - one JSONL row per
leg per case lands in `results/run-<timestamp>.jsonl`. Keep these files; they
are your before/after record when models or pricing change.

**Step 5 - Interpret.** Accuracy ties are expected on easy labeled sets; rank
legs by (a) confidence behavior on the *ambiguous* cases - mid-band honesty
beats confident wrongness for guardrails, (b) latency, (c) token cost.

**Step 6 - Wire the gate (optional).** `guard.py <branch> [--worktree <path>]`
exit codes: 0 safe, 1 hard block (deterministic, non-negotiable), 2 human
review (model uncertain or refuses), 3 fail-closed (AI unavailable on a soft
case), 4 usage. Default threshold 0.8. The AI layer can NEVER override a
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

## File: run_evals.py

```python
#!/usr/bin/env python3
"""jev-lab runner: evaluates Jev (and gateway LLM baseline) on two labeled
decision tasks from the tailroute workflow review.

Usage:
    python3 run_evals.py pr-gate
    python3 run_evals.py worktree-guard
    python3 run_evals.py all
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import os
from datetime import datetime, timezone

from lab import (
    GW_BASELINE_MODEL,
    ask,
    make_byok_legs,
    make_gateway_llm_client,
    make_jev_client,
    pr_gate_questions,
    worktree_guard_questions,
)

REPO = os.environ.get("TAILROUTE_REPO", os.path.expanduser("~/Developer/sandbox/tailroute"))


# ---------------------------------------------------------------- helpers ----

def run(cmd: list[str], cwd: str | None = None) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed:\n{out.stderr.strip()}")
    return out.stdout.strip()


def baseline_legs() -> list:
    """(label, adapter client, provider) per configured baseline model.

    GW_BASELINE_MODELS is comma-separated gateway model slugs; defaults to
    GW_BASELINE_MODEL. Labels use the slug suffix, e.g. "gw:gpt-4o-mini".
    """
    raw = os.environ.get("GW_BASELINE_MODELS", GW_BASELINE_MODEL)
    legs = []
    for model in [m.strip() for m in raw.split(",") if m.strip()]:
        client, provider = make_gateway_llm_client(model)
        legs.append((f"gw:{model.split('/')[-1]}", client, provider))
    return legs


def render(result, leg: str) -> dict:
    result.leg = leg
    return {
        "leg": leg,
        "latency_ms": round(result.latency_ms, 1),
        "usage": result.usage,
        **result.answers,
    }


RUN_STARTED = datetime.now(timezone.utc)
RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "results", f"run-{RUN_STARTED:%Y%m%d-%H%M%S}.jsonl"
)


def record(eval_name: str, case_id: str, expected: str, results: list[dict]) -> None:
    """Append one JSONL line per leg to results/run-<ts>.jsonl (best-effort)."""
    try:
        os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
        with open(RESULTS_PATH, "a") as f:
            for r in results:
                f.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "eval": eval_name,
                    "case": case_id,
                    "expected": expected,
                    **r,
                }, default=str) + "\n")
    except OSError as e:
        print(f"[warn] could not write results file: {e}")


def show(title: str, case: str, expected: str, results: list[dict]) -> bool:
    print(f"\n--- {title} / {case} (expected: {expected}) ---")
    ok_all = True
    for r in results:
        got = r.get("gate", {}).get("choice", "?")
        conf = r.get("gate", {}).get("confidence")
        verdict = "OK " if got == expected else "MISS"
        if got != expected:
            ok_all = False
        extra = ""
        if "touches_source" in r:
            extra += f"  touches_source={r['touches_source'].get('noul')}"
        if "has_unique_work" in r:
            extra += f"  unique_work={r['has_unique_work'].get('noul')}"
        if "reversibility" in r:
            extra += f"  reversibility={r['reversibility'].get('score')}"
        if "data_loss_risk" in r:
            extra += f"  data_loss={r['data_loss_risk'].get('score')}"
        print(f"[{verdict}] {r['leg']:>8}: {got} (conf={conf}, {r['latency_ms']}ms){extra}")
        if r["usage"]:
            print(f"           usage: {r['usage']}")
    return ok_all


# --------------------------------------------------------------- pr gate ----

PR_LABELS = {10: "auto_merge", 12: "auto_merge", 11: "human_review"}


def pr_state(repo: str, num: int) -> str:
    """Condensed, non-sensitive PR metadata. No diffs, no code content."""
    raw = run(
        [
            "gh", "pr", "view", str(num), "--repo", "shrwnsan/tailroute", "--json",
            "number,title,state,author,additions,deletions,changedFiles,files,labels",
        ]
    )
    pr = json.loads(raw)
    files = [
        {"path": f["path"], "+": f["additions"], "-": f["deletions"]}
        for f in pr.get("files", [])[:25]
    ]
    state = {
        "repository": "tailroute (macOS Tailscale+VPN daemon; Swift app in macos/, bash+Go CLI in cli/ submodule; docs in docs/)",
        "auto_merge_policy": "docs/chore-only PRs may auto-merge; app or CLI source requires human review",
        "pr": {
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "total_additions": pr.get("additions"),
            "total_deletions": pr.get("deletions"),
            "changed_file_count": pr.get("changedFiles"),
            "labels": [l["name"] for l in pr.get("labels", [])],
            "files": files,
        },
    }
    return json.dumps(state, indent=1)


def eval_pr_gate() -> None:
    try:
        jev = make_jev_client()
    except SystemExit:
        jev = None  # leg degrades gracefully like all others
    try:
        alt_legs = baseline_legs()
    except SystemExit:
        alt_legs = []
    alt_legs += make_byok_legs()  # independent: BYOK works even without a gateway key

    questions = pr_gate_questions()
    tally = {}
    for num, expected in PR_LABELS.items():
        state = pr_state(REPO, num)
        results = []
        if jev is not None:
            results.append(render(ask(jev, questions, state), "jev"))
        for leg_label, leg_client, leg_provider in alt_legs:
            try:
                results.append(render(ask(leg_client, questions, state, adapter_model=leg_provider), leg_label))
            except Exception as e:
                print(f"[skip] {leg_label} on PR #{num}: {type(e).__name__}: {e}")
        show("pr-gate", f"PR #{num}", expected, results)
        record("pr-gate", f"PR #{num}", expected, results)
        for r in results:
            tally.setdefault(r["leg"], [0, 0])
            tally[r["leg"]][1] += 1
            if r["gate"]["choice"] == expected:
                tally[r["leg"]][0] += 1

    _summary("pr-gate", tally)


# ------------------------------------------------------- worktree guard ----

def build_worktree_cases() -> list[dict]:
    """Synthesize branches with known ground truth in a throwaway repo.

    A: fully merged                     -> safe
    B: unique unmerged commit           -> unsafe
    C: fully cherry-picked (new SHA)    -> safe   (calibration case)
    D: diverged edit, patch differs     -> unsafe
    """
    cases = []
    with tempfile.TemporaryDirectory(prefix="jev-lab-wt-") as tmp:
        def g(*cmd: str) -> str:
            # containment: refuse to run git outside the temp repo
            toplevel = run(["git", "rev-parse", "--show-toplevel"], cwd=tmp)
            if os.path.realpath(toplevel) != os.path.realpath(tmp):
                raise RuntimeError(f"selftest containment failure: git toplevel is {toplevel!r}")
            return run(["git", *cmd], cwd=tmp)

        run(["git", "init", "-q", "-b", "main", "."], cwd=tmp)  # containment check needs a repo
        g("config", "user.email", "lab@local"); g("config", "user.name", "jev-lab")
        g("commit", "-q", "--allow-empty", "-m", "base")

        # A: merged branch
        g("checkout", "-q", "-b", "feat-a"); g("commit", "-q", "--allow-empty", "-m", "docs: add notes")
        g("checkout", "-q", "main"); g("merge", "-q", "--no-ff", "feat-a", "-m", "merge feat-a")

        # B: unique unmerged work
        g("checkout", "-q", "-b", "feat-b"); g("commit", "-q", "--allow-empty", "-m", "feat: unique unmerged work")

        # C: cherry-picked elsewhere (patch-equivalent, new SHA)
        g("checkout", "-q", "-b", "feat-c", "main")
        with open(os.path.join(tmp, "c.txt"), "w") as f: f.write("hello\n")
        g("add", "c.txt"); g("commit", "-q", "-m", "fix: c file")
        c_sha = g("rev-parse", "feat-c")
        g("checkout", "-q", "main"); g("cherry-pick", "-x", c_sha)
        # -x appends "(cherry picked from ...)" to the message: different SHA,
        # same patch-id — exactly the real-world case git cherry detects.

        # D: diverged edit on same file
        g("checkout", "-q", "-b", "feat-d", "main")
        with open(os.path.join(tmp, "d.txt"), "w") as f: f.write("branch version\n")
        g("add", "d.txt"); g("commit", "-q", "-m", "change: d (branch side)")
        d_sha = g("rev-parse", "feat-d")
        g("checkout", "-q", "main")
        with open(os.path.join(tmp, "d.txt"), "w") as f: f.write("main version\n")
        g("add", "d.txt"); g("commit", "-q", "-m", "change: d (main side)")

        for branch, expected, story in [
            ("feat-a", "safe_delete", "Branch was merged into main via a merge commit; branch label kept around."),
            ("feat-b", "keep_review", "Branch has a commit never merged anywhere."),
            ("feat-c", "safe_delete", "Branch commit was cherry-picked to main (different SHA, same change)."),
            ("feat-d", "keep_review", "Branch edited a file that main also edited differently; patch-ids differ."),
        ]:
            ahead = run(["git", "rev-list", "--count", f"main..{branch}"], cwd=tmp)
            behind = run(["git", "rev-list", "--count", f"{branch}..main"], cwd=tmp)
            cherry = run(["git", "cherry", "main", branch], cwd=tmp)
            equivalent = sum(1 for l in cherry.splitlines() if l.startswith("-"))
            unique = sum(1 for l in cherry.splitlines() if l.startswith("+"))
            state = json.dumps({
                "branch": branch,
                "story": story,
                "commits_ahead_of_main": int(ahead),
                "commits_behind_main": int(behind),
                "git_cherry_patch_equivalent_commits": equivalent,
                "git_cherry_unique_commits": unique,
                "worktree_dirty_files": 0,
                "recent_branch_commits": run(["git", "log", "--format=%s", "-3", branch], cwd=tmp).splitlines(),
            }, indent=1)
            cases.append({"branch": branch, "expected": expected, "state": state})
    return cases


def eval_worktree_guard() -> None:
    try:
        jev = make_jev_client()
    except SystemExit:
        jev = None  # leg degrades gracefully like all others
    try:
        alt_legs = baseline_legs()
    except SystemExit:
        alt_legs = []
    alt_legs += make_byok_legs()  # independent: BYOK works even without a gateway key

    questions = worktree_guard_questions()
    tally = {}
    for case in build_worktree_cases():
        state = case["state"]
        results = []
        if jev is not None:
            results.append(render(ask(jev, questions, state), "jev"))
        for leg_label, leg_client, leg_provider in alt_legs:
            try:
                results.append(render(ask(leg_client, questions, state, adapter_model=leg_provider), leg_label))
            except Exception as e:
                print(f"[skip] {leg_label} on {case['branch']}: {type(e).__name__}: {e}")
        show("worktree-guard", case["branch"], case["expected"], results)
        record("worktree-guard", case["branch"], case["expected"], results)
        for r in results:
            tally.setdefault(r["leg"], [0, 0])
            tally[r["leg"]][1] += 1
            if r["gate"]["choice"] == case["expected"]:
                tally[r["leg"]][0] += 1

    _summary("worktree-guard", tally)


# ---------------------------------------------------------------- summary ----

def _summary(name: str, tally: dict) -> None:
    print(f"\n=== {name}: per-leg accuracy ===")
    for leg, (correct, total) in tally.items():
        print(f"  {leg:>8}: {correct}/{total}")
    print(f"  results: {RESULTS_PATH}")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("pr-gate", "all"):
        eval_pr_gate()
    if which in ("worktree-guard", "all"):
        eval_worktree_guard()
```

## File: guard.py

```python
#!/usr/bin/env python3
"""pre-delete guard: deterministic git checks first, Jev judgment second.

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
  python3 guard.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

from lab import ask, make_jev_client

EXIT_SAFE, EXIT_BLOCK, EXIT_REVIEW, EXIT_FAILSAFE, EXIT_USAGE = 0, 1, 2, 3, 4


def run(cmd: list[str], cwd: str | None = None) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {out.stderr.strip()}")
    return out.stdout.strip()


def guard_questions():
    from typesafe_sdk import Choice, Noul, Score

    questions = {
        "gate": Choice(
            instructions=(
                "The deterministic layer has already proven that no COMMITTED "
                "work would be lost (see deterministic_verdict in the state). "
                "The only remaining question is soft signals: untracked files, "
                "submodule drift, or anything else suggesting author work "
                "outside git's tracked history. Is deletion safe?"
            ),
            criteria={
                "safe_delete": "No author work in untracked files or submodules; nothing ambiguous remains",
                "keep_review": "Author work may exist outside tracked history, or signals are genuinely ambiguous",
            },
        ),
        "has_unique_work": Noul(
            instructions="Author work exists in UNTRACKED files or unsynced submodules (committed work is already proven safe)",
        ),
        "data_loss_risk": Score(
            instructions="If deleted now, how much UNTRACKED or otherwise unrecoverable work would be lost?",
            criteria=[
                "None: no untracked content of value",
                "Minor: disposable artifacts that are easy to regenerate",
                "Real: drafts, notes, or outputs that exist only here",
            ],
        ),
    }
    return questions


def collect_state(branch: str, repo: str, worktree: str | None = None) -> dict:
    state = {"branch": branch}
    state["ahead_of_main"] = int(run(["git", "rev-list", "--count", f"main..{branch}"], cwd=repo))
    state["behind_main"] = int(run(["git", "rev-list", "--count", f"{branch}..main"], cwd=repo))
    cherry = run(["git", "cherry", "main", branch], cwd=repo)
    lines = cherry.splitlines() if cherry else []
    state["patch_equivalent_commits"] = sum(1 for l in lines if l.startswith("-"))
    state["unique_commits"] = sum(1 for l in lines if l.startswith("+"))
    state["recent_commits"] = run(["git", "log", "--format=%s", "-3", branch], cwd=repo).splitlines()
    try:
        state["merged_into_origin_main"] = run(
            ["git", "rev-list", "--count", f"origin/main..{branch}"], cwd=repo
        ) == "0"
    except RuntimeError:
        state["merged_into_origin_main"] = "unknown (no origin/main)"
    if worktree:
        st = run(["git", "-C", worktree, "status", "--porcelain"])
        porcelain = st.splitlines() if st else []
        state["worktree_uncommitted_changes"] = sum(1 for l in porcelain if not l.startswith("??"))
        state["worktree_untracked_files"] = [l[3:] for l in porcelain if l.startswith("??")][:15]
        sm = run(["git", "-C", worktree, "submodule", "status"])
        state["submodules_out_of_sync"] = [
            l for l in sm.splitlines() if l[:1] in ("+", "-", "U")
        ] or []
    return state


def hard_blocks(state: dict) -> list[str]:
    """Deterministic, non-negotiable blocks. The AI layer never sees these."""
    blocks = []
    if state.get("worktree_uncommitted_changes"):
        blocks.append(
            f"{state['worktree_uncommitted_changes']} uncommitted change(s) in the "
            "worktree — commit or stash first"
        )
    if state.get("unique_commits"):
        blocks.append(
            f"{state['unique_commits']} commit(s) not on main in any form "
            "(git cherry) — merge, cherry-pick, or delete deliberately"
        )
    return blocks


def jev_verdict(state: dict):
    """Returns (choice, confidence, result). Raises SystemExit if no API key."""
    client = make_jev_client()
    questions = guard_questions()
    if state.get("worktree_untracked_files"):
        from typesafe_sdk import Noul

        questions["untracked_ignorable"] = Noul(
            instructions=(
                "The untracked files in this worktree look like disposable "
                "build/log artifacts rather than author work"
            )
        )
    result = ask(client, questions, json.dumps(state, indent=1))
    gate = result.answers["gate"]
    return gate["choice"], gate["confidence"], result


def guard(branch: str, repo: str, worktree: str | None, threshold: float, as_json: bool) -> int:
    try:
        tip = run(["git", "rev-parse", "--verify", branch], cwd=repo)
    except RuntimeError:
        print(f"[guard] branch not found: {branch}")
        return EXIT_USAGE
    if not tip:
        print(f"[guard] branch not found: {branch}")
        return EXIT_USAGE

    state = collect_state(branch, repo, worktree)
    state["deterministic_verdict"] = (
        "git cherry math already proven: every commit on this branch is reachable "
        "from main or patch-equivalent to a main commit (0 unique commits); "
        "uncommitted tracked changes: none. No COMMITTED work can be lost by "
        "deleting this branch. Only soft signals remain to judge."
    )
    blocks = hard_blocks(state)
    if blocks:
        print("[guard] HARD BLOCK — deterministic checks failed (non-negotiable):")
        for b in blocks:
            print(f"  - {b}")
        if as_json:
            print(json.dumps({"branch": branch, "verdict": "hard_block", "blocks": blocks, "state": state}, indent=1))
        return EXIT_BLOCK

    # Soft signals are the ONLY thing left for Jev to judge. If there are none,
    # the deterministic layer is complete — allow without an AI call. (Observed
    # across three phrasings: Jev's verdict on patch-equivalent branches flips
    # with framing, so git topology stays out of its hands.)
    soft_signals = bool(state.get("worktree_untracked_files") or state.get("submodules_out_of_sync"))
    if not soft_signals:
        print("[guard] SAFE (deterministic): no unique commits, clean worktree, "
              "no soft signals — nothing for AI to judge.")
        if as_json:
            print(json.dumps({"branch": branch, "verdict": "safe_deterministic", "state": state}, indent=1))
        return EXIT_SAFE

    try:
        choice, conf, result = jev_verdict(state)
    except SystemExit as e:
        print(f"[guard] FAIL-SAFE: AI layer unavailable ({e}).")
        print("  Deterministic checks found nothing unique, but soft signals")
        print("  (untracked files, submodules) were not judged. Decide manually.")
        if as_json:
            print(json.dumps({"branch": branch, "verdict": "failsafe_no_ai", "state": state}, indent=1))
        return EXIT_FAILSAFE
    except Exception as e:
        print(f"[guard] FAIL-SAFE: AI layer error: {type(e).__name__}: {e}")
        return EXIT_FAILSAFE

    extras = {
        k: v for k, v in result.answers.items() if k != "gate"
    }
    aux = {k: (v.get("noul", v.get("score")) if isinstance(v, dict) else v) for k, v in extras.items()}
    print(f"[guard] jev: {choice} (conf={conf})  soft-signals: {aux}")

    if as_json:
        print(json.dumps({"branch": branch, "verdict": choice, "confidence": conf,
                          "soft_signals": aux, "state": state}, indent=1))

    if choice == "safe_delete" and conf >= threshold:
        print(f"[guard] SAFE to delete '{branch}' (conf {conf} >= {threshold}).")
        return EXIT_SAFE
    if choice == "safe_delete":
        print(f"[guard] UNCERTAIN: safe but conf {conf} < threshold {threshold} — human review.")
        return EXIT_REVIEW
    print(f"[guard] KEEP: jev says review before deleting '{branch}'.")
    return EXIT_REVIEW


# ---------------------------------------------------------------- selftest ----

def selftest() -> int:
    """Verifies the deterministic layer on synthetic branches with known truth,
    then (if TYPESAFE_API_KEY is set) the full pipeline including soft signals."""
    deterministic = {"feat-a": [], "feat-b": ["unique"], "feat-c": [], "feat-d": ["unique"]}
    with tempfile.TemporaryDirectory(prefix="jev-lab-guard-") as tmp:
        def g(*cmd):
            # containment: refuse to run git outside the temp repo (a missing
            # cwd once leaked selftest commits into the real repo's main)
            toplevel = run(["git", "rev-parse", "--show-toplevel"], cwd=tmp)
            if os.path.realpath(toplevel) != os.path.realpath(tmp):
                raise RuntimeError(f"selftest containment failure: git toplevel is {toplevel!r}")
            return run(["git", *cmd], cwd=tmp)

        wt = os.path.join(tempfile.mkdtemp(prefix="jev-lab-guard-wt-"), "wt")  # must not exist yet
        run(["git", "init", "-q", "-b", "main", "."], cwd=tmp)  # containment check needs a repo
        g("config", "user.email", "guard@local"); g("config", "user.name", "guard")
        g("commit", "-q", "--allow-empty", "-m", "base")
        g("checkout", "-q", "-b", "feat-a"); g("commit", "-q", "--allow-empty", "-m", "docs: a")
        g("checkout", "-q", "main"); g("merge", "-q", "--no-ff", "feat-a", "-m", "merge feat-a")
        g("checkout", "-q", "-b", "feat-b"); g("commit", "-q", "--allow-empty", "-m", "feat: unique")
        g("checkout", "-q", "main")
        g("checkout", "-q", "-b", "feat-c", "main")
        with open(os.path.join(tmp, "c.txt"), "w") as f: f.write("x\n")
        g("add", "c.txt"); g("commit", "-q", "-m", "fix: c")
        csha = g("rev-parse", "feat-c")
        g("checkout", "-q", "main"); g("cherry-pick", "-x", csha)
        g("checkout", "-q", "-b", "feat-d", "main")
        with open(os.path.join(tmp, "d.txt"), "w") as f: f.write("branch\n")
        g("add", "d.txt"); g("commit", "-q", "-m", "d branch side")

        ok = True
        for branch, expect_blocks in deterministic.items():
            state = collect_state(branch, tmp)
            blocks = hard_blocks(state)
            good = bool(blocks) == bool(expect_blocks)
            ok &= good
            print(f"[{'OK ' if good else 'BAD'}] {branch}: blocks={len(blocks)} "
                  f"(ahead={state['ahead_of_main']}, equiv={state['patch_equivalent_commits']}, "
                  f"unique={state['unique_commits']})")

        # worktree soft-signal scenario: merged branch, worktree has build junk + a draft
        g("worktree", "add", "-q", wt, "feat-a")
        for name in ("buildcache.tmp", "runner-output.bin", "NOTES-draft.md"):
            path = os.path.join(wt, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f: f.write("junk\n")
        state = collect_state("feat-a", tmp, worktree=wt)
        blocks = hard_blocks(state)
        good = not blocks and len(state["worktree_untracked_files"]) >= 1
        ok &= good
        print(f"[{'OK ' if good else 'BAD'}] feat-a worktree: untracked={state['worktree_untracked_files']} hard_blocks={blocks}")

        # end-to-end scenarios: assert exit codes (AI only matters on soft cases)
        scenarios = [
            ("feat-a", None, EXIT_SAFE),   # merged, clean worktree -> deterministic allow, no AI
            ("feat-b", None, EXIT_BLOCK),  # unique commits
            ("feat-c", None, EXIT_SAFE),   # cherry-picked, clean worktree -> deterministic allow
            ("feat-d", None, EXIT_BLOCK),  # diverged
        ]
        for branch, wtp, expected in scenarios:
            code = guard(branch, tmp, wtp, 0.8, False)
            good = code == expected
            ok &= good
            print(f"[{'OK ' if good else 'BAD'}] guard {branch}: exit={code} (expected {expected})")

        # soft-signal case (untracked files incl. a draft-named one): the one
        # scenario where Jev's judgment is the point
        code = guard("feat-a", tmp, wt, 0.8, False)
        if os.environ.get("TYPESAFE_API_KEY"):
            good = code in (EXIT_SAFE, EXIT_REVIEW)  # NOTES-draft.md may legitimately go either way
            print(f"[{'OK ' if good else 'BAD'}] guard feat-a+worktree: exit={code} "
                  f"(0=confident safe, 2=escalated on the draft file — both defensible)")
            ok &= good
        else:
            good = code == EXIT_FAILSAFE
            ok &= good
            print(f"[{'OK ' if good else 'BAD'}] guard feat-a+worktree: exit={code} "
                  f"(fail-safe without key, expected {EXIT_FAILSAFE})")
        return EXIT_SAFE if ok else EXIT_BLOCK


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    p = argparse.ArgumentParser(description="pre-delete guard: git math first, Jev judgment second")
    p.add_argument("branch")
    p.add_argument("--repo", default=os.getcwd(), help="main repository path")
    p.add_argument("--worktree", default=None, help="linked worktree path to inspect for uncommitted/untracked state")
    p.add_argument("--threshold", type=float, default=0.8)
    p.add_argument("--json", action="store_true", help="also print full JSON verdict")
    a = p.parse_args()
    return guard(a.branch, a.repo, a.worktree, a.threshold, a.json)


if __name__ == "__main__":
    sys.exit(main())
```
