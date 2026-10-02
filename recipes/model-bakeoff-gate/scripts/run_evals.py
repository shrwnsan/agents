#!/usr/bin/env python3
"""jev-lab runner: evaluates Jev (and gateway LLM baseline) on two labeled
decision tasks from a real-world workflow review.

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
    ask,
    make_byok_legs,
    make_gateway_llm_client,
    make_jev_client,
    pr_gate_questions,
    worktree_guard_questions,
)

GW_BASELINE_MODEL = "openai/gpt-4o-mini"  # default gateway baseline (override via GW_BASELINE_MODELS)

REPO = os.environ.get("BAKEOFF_PR_REPO", "")  # required for pr-gate: any GitHub repo


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
            "gh", "pr", "view", str(num), "--repo", repo, "--json",
            "number,title,state,author,additions,deletions,changedFiles,files,labels",
        ]
    )
    pr = json.loads(raw)
    files = [
        {"path": f["path"], "+": f["additions"], "-": f["deletions"]}
        for f in pr.get("files", [])[:25]
    ]
    state = {
        "repository": repo,
        "auto_merge_policy": "state your merge policy here, e.g. docs/chore-only PRs auto-merge; substantive source requires human review",
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
    if not REPO:
        print("[skip] pr-gate: set BAKEOFF_PR_REPO=<owner/repo> to enable "
              "(any repo with labeled PRs)")
        return
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
