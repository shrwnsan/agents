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

from lab import ask, make_jev_client, worktree_guard_questions

EXIT_SAFE, EXIT_BLOCK, EXIT_REVIEW, EXIT_FAILSAFE, EXIT_USAGE = 0, 1, 2, 3, 4


def run(cmd: list[str], cwd: str | None = None) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {out.stderr.strip()}")
    return out.stdout.strip()


def guard_questions():
    questions = worktree_guard_questions()
    # Conditional question injection: only added by default; jev_verdict
    # drops it when there is no untracked content to judge.
    questions["untracked_ignorable"] = {
        "type": "noul",
        "instructions": (
            "The untracked files in this worktree look like disposable "
            "build/log artifacts rather than author work"
        ),
    }
    return questions


def collect_state(branch: str, repo: str, worktree: str | None = None) -> dict:
    state: dict = {"branch": branch}
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
    """Returns (choice, confidence, result). Raises SystemExit if no API key
    (make_jev_client contract); guard() catches it and fails closed."""
    client = make_jev_client()
    questions = guard_questions()
    if not state.get("worktree_untracked_files"):
        # Nothing untracked to judge — drop the conditional question.
        questions.pop("untracked_ignorable", None)
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
