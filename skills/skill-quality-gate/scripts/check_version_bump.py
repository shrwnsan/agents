#!/usr/bin/env python3
"""Version-drift check for the skill-quality-gate (git-aware, advisory).

Complements check_frontmatter.py: that one validates a skill directory as
it stands; this one diffs skill directories against a base ref and flags
operational changes that shipped without the metadata.version bump the
hub's convention requires (agents research-002: bump in the same PR as
any skill-content change).

Rules:
- Operational change = SKILL.md body changed (frontmatter stripped, so a
  version bump alone never counts) or any file under scripts/ changed.
  → WARN when metadata.version is unchanged or missing on the new side.
- metadata-only frontmatter changes are the bump itself → never operational.
- references/, README, assets-only changes are exempt (#130 precedent:
  docs corrections don't bump).
- New skill dirs without a version field → WARN; with one → PASS.

Output is WARN/INFO/PASS lines plus an OVERALL line; always exit 0 —
advisory, never blocking (the gate FAIL tier is reserved for spec/safety
classes). Exit 2 on usage errors; a missing base ref prints SKIP_REASON
and exits 0.

Usage:
  check_version_bump.py <repo-root> [--base REF]        # REF default: origin/main
  check_version_bump.py --self-test
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
VERSION_LINE = re.compile(r'^\s*version:\s*"?([^"\n]*)"?\s*$', re.M)


def body_and_version(text: str) -> tuple[str, str | None]:
    """Return (frontmatter-stripped body, metadata.version or None)."""
    m = FRONTMATTER.match(text)
    if not m:
        return text, None
    fm, body = m.group(1), text[m.end():]
    v = VERSION_LINE.search(fm)
    return body, v.group(1).strip() if v else None


def git(repo: Path, *args: str, ok_missing: bool = False) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if ok_missing:
            return ""
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


def skill_changes(repo: Path, base: str) -> dict[str, set[str]]:
    """Map skill dir name → set of changed relative paths (worktree vs base)."""
    out = git(repo, "diff", "--name-only", base, "--", "skills/")
    changed: dict[str, set[str]] = {}
    for line in out.splitlines():
        parts = line.split("/")
        if len(parts) >= 3 and parts[0] == "skills":
            changed.setdefault(parts[1], set()).add(line)
    return changed


def check(repo: Path, base: str) -> list[str]:
    findings: list[str] = []
    for skill, files in sorted(skill_changes(repo, base).items()):
        cur_md = repo / "skills" / skill / "SKILL.md"
        new_text = cur_md.read_text() if cur_md.exists() else ""
        old_text = git(repo, "show", f"{base}:skills/{skill}/SKILL.md",
                       ok_missing=True)
        if not old_text and not new_text:
            continue  # only non-SKILL.md files changed
        new_body, new_ver = body_and_version(new_text)
        old_body, old_ver = body_and_version(old_text)

        if not old_text:
            findings.append(
                f"PASS  [version-drift] {skill}: new skill, version={new_ver!r}"
                if new_ver else
                f"WARN  [version-drift] {skill}: new skill has no metadata.version")
            continue
        if not new_text:
            findings.append(f"INFO  [version-drift] {skill}: SKILL.md deleted")
            continue
        if new_ver is None:
            findings.append(
                f"WARN  [version-drift] {skill}: metadata.version removed")
            continue

        body_changed = new_body != old_body
        script_changed = any("/scripts/" in f for f in files)
        if body_changed or script_changed:
            if new_ver == old_ver:
                findings.append(
                    f"WARN  [version-drift] {skill}: operational change without "
                    f"version bump (still {new_ver!r})")
            else:
                findings.append(
                    f"PASS  [version-drift] {skill}: bumped {old_ver!r} -> {new_ver!r}")
        else:
            findings.append(
                f"INFO  [version-drift] {skill}: metadata/docs-only change, exempt")
    return findings


def self_test() -> int:
    failures = []

    def run(name: str, setup, expect: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-q", "-b", "main")
            setup(repo)
            got = "\n".join(check(repo, "base"))
            ok = expect in got
            print(f"{'PASS' if ok else 'FAIL'}  {name}")
            if not ok:
                failures.append(name)
                print(f"  expected substring: {expect!r}\n  got:\n{got}")

    def commit_all(repo: Path, msg: str) -> None:
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-q", "-m", msg)
        git(repo, "branch", "-q", "base")

    def s_body_no_bump(repo: Path) -> None:
        (repo / "skills/s-a").mkdir(parents=True)
        (repo / "skills/s-a/SKILL.md").write_text(
            '---\nname: s-a\nmetadata:\n  version: "1.0.0"\n---\nbody v1\n')
        commit_all(repo, "base")
        (repo / "skills/s-a/SKILL.md").write_text(
            '---\nname: s-a\nmetadata:\n  version: "1.0.0"\n---\nbody v2\n')

    def s_body_bumped(repo: Path) -> None:
        (repo / "skills/s-b").mkdir(parents=True)
        (repo / "skills/s-b/SKILL.md").write_text(
            '---\nname: s-b\nmetadata:\n  version: "1.0.0"\n---\nbody v1\n')
        commit_all(repo, "base")
        (repo / "skills/s-b/SKILL.md").write_text(
            '---\nname: s-b\nmetadata:\n  version: "1.1.0"\n---\nbody v2\n')

    def s_refs_only(repo: Path) -> None:
        (repo / "skills/s-c/references").mkdir(parents=True)
        (repo / "skills/s-c/SKILL.md").write_text(
            '---\nname: s-c\nmetadata:\n  version: "1.0.0"\n---\nbody\n')
        (repo / "skills/s-c/references/r.md").write_text("x\n")
        commit_all(repo, "base")
        (repo / "skills/s-c/references/r.md").write_text("y\n")

    def s_new_unversioned(repo: Path) -> None:
        (repo / "skills/s-d").mkdir(parents=True)
        (repo / "skills/s-d/SKILL.md").write_text(
            '---\nname: s-d\nmetadata:\n  version: "1.0.0"\n---\nbody\n')
        commit_all(repo, "base")
        (repo / "skills/s-e").mkdir(parents=True)
        (repo / "skills/s-e/SKILL.md").write_text("---\nname: s-e\n---\nbody\n")
        git(repo, "add", "-A")  # PR branches carry committed files, not untracked ones

    def s_metadata_only(repo: Path) -> None:
        (repo / "skills/s-f").mkdir(parents=True)
        (repo / "skills/s-f/SKILL.md").write_text(
            '---\nname: s-f\nmetadata:\n  version: "1.0.0"\n---\nbody\n')
        commit_all(repo, "base")
        (repo / "skills/s-f/SKILL.md").write_text(
            '---\nname: s-f\nmetadata:\n  version: "1.1.0"\n---\nbody\n')

    run("body-changed-no-bump-warns", s_body_no_bump, "WARN")
    run("body-changed-with-bump-passes", s_body_bumped, "PASS")
    run("references-only-exempt", s_refs_only, "INFO")
    run("new-skill-unversioned-warns", s_new_unversioned, "WARN  [version-drift] s-e")
    run("metadata-only-change-exempt", s_metadata_only, "INFO")
    print("self-test:", "PASS" if not failures else f"FAIL {failures}")
    return 0 if not failures else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_root")
    ap.add_argument("--base", default="origin/main")
    args = ap.parse_args()
    repo = Path(args.repo_root)
    if not git(repo, "rev-parse", "--verify", args.base, ok_missing=True):
        print(f"SKIP_REASON=base ref {args.base!r} not found", file=sys.stderr)
        return 0
    findings = check(repo, args.base)
    for f in findings:
        print(f)
    overall = "WARN" if any(f.startswith("WARN") for f in findings) else "PASS"
    print(f"OVERALL: {overall}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
