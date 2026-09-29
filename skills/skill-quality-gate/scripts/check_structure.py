#!/usr/bin/env python3
"""Static structure validator for an agent skill directory.

Checks (phase "structure"):
  1. SKILL.md exists and has content after the frontmatter fence
     (fence presence check only -- deep parsing lives in check_frontmatter.py).
  2. Internal references: path-like tokens in SKILL.md / README.md that are
     relative and resolve inside the skill dir must exist.
  3. scripts/*.sh and scripts/*.py must be non-empty; .sh files need the
     executable bit and a shebang (WARN-level). No syntax checking here.
  4. Unexpected top-level entries are reported as informational SKIP.

Usage: python3 check_structure.py <skill-dir> [--json]
Exit codes: 0 = no FAIL findings, 1 = at least one FAIL, 2 = usage/IO error.
Python 3.9+, stdlib only.
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import unquote

PHASE = "structure"
ALLOWED_EXT = (".md", ".sh", ".py", ".js", ".ts", ".json", ".yml", ".yaml", ".txt")
ALLOWED_TOP = {"SKILL.md", "README.md", "scripts", "references", "examples", "assets"}
SCRIPT_EXT = (".sh", ".py")

# Markdown link targets: [text](target "optional title")
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
# Bare path-like tokens; excludes markdown noise chars. Inline-code spans are
# scanned too (that is where `scripts/foo.py` style references live).
TOKEN_RE = re.compile(r"[^\s`<>\"'(),;=\[\]|]+")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


class IoError(Exception):
    """Unreadable file / directory -- maps to exit code 2."""


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as exc:
        raise IoError("cannot read {}: {}".format(path, exc.strerror or exc))


def strip_fenced(lines):
    """Drop lines inside ``` / ~~~ fenced code blocks (example commands are
    not documentation references)."""
    out, inside = [], False
    for line in lines:
        if FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return out


def extract_ref_tokens(lines):
    """Path-like tokens worth checking: contain '/', end in an allowed
    extension, and are not URLs / absolute / home-relative / pure anchors /
    glob patterns."""
    text = "\n".join(lines)
    candidates = [m.group(1) for m in LINK_RE.finditer(text)]
    candidates.extend(m.group(0).rstrip(".,;:!?") for m in TOKEN_RE.finditer(text))

    tokens, seen = [], set()
    for raw in candidates:
        tok = unquote(raw).strip()
        if "#" in tok:  # strip fragment; a pure anchor reduces to ""
            tok = tok[: tok.index("#")]
        if not tok or "/" not in tok:
            continue
        if tok.startswith(("/", "~")) or SCHEME_RE.match(tok):
            continue
        if "*" in tok or "?" in tok:  # glob pattern, not a literal reference
            continue
        if not tok.lower().endswith(ALLOWED_EXT):
            continue
        if tok not in seen:
            seen.add(tok)
            tokens.append(tok)
    return tokens


def check_skill_md(root, findings):
    path = os.path.join(root, "SKILL.md")
    if not os.path.isfile(path):
        findings.append(("FAIL", "SKILL.md is missing"))
        return
    text = read_text(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        # No frontmatter fence: the whole file counts as body content.
        # (Deep frontmatter validation is check_frontmatter.py's job.)
        if not text.strip():
            findings.append(("FAIL", "SKILL.md is empty"))
        else:
            findings.append(("PASS", "SKILL.md present with content (no frontmatter fence)"))
        return
    close = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            close = idx
            break
    if close is None:
        findings.append(("FAIL", "SKILL.md frontmatter fence is not closed (no closing '---')"))
        return
    if "\n".join(lines[close + 1:]).strip():
        findings.append(("PASS", "SKILL.md present with content after frontmatter"))
    else:
        findings.append(("FAIL", "SKILL.md has no content after the frontmatter block"))


def check_references(root, findings):
    checked, dangling = 0, 0
    for fname in ("SKILL.md", "README.md"):
        path = os.path.join(root, fname)
        if not os.path.isfile(path):
            continue
        base = os.path.dirname(path)
        for tok in extract_ref_tokens(strip_fenced(read_text(path).splitlines())):
            checked += 1
            resolved = os.path.normpath(os.path.join(base, tok))
            inside = resolved == root or resolved.startswith(root + os.sep)
            if not inside or os.path.exists(resolved):
                continue
            dangling += 1
            findings.append((
                "FAIL",
                "dangling reference: {} references '{}' (not found: {})".format(
                    fname, tok, os.path.relpath(resolved, root)
                ),
            ))
    if checked and not dangling:
        findings.append(("PASS", "all {} internal reference(s) resolve".format(checked)))


def first_line(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.readline()
    except OSError as exc:
        raise IoError("cannot read {}: {}".format(path, exc.strerror or exc))


def check_scripts(root, findings):
    scripts = os.path.join(root, "scripts")
    if not os.path.isdir(scripts):
        return
    try:
        names = sorted(os.listdir(scripts))
    except OSError as exc:
        raise IoError("cannot list {}: {}".format(scripts, exc.strerror or exc))

    sane, mark = 0, len(findings)
    for name in names:
        if not name.lower().endswith(SCRIPT_EXT):
            continue
        path = os.path.join(scripts, name)
        if not os.path.isfile(path):
            continue
        rel = "scripts/{}".format(name)
        if os.path.getsize(path) == 0:
            findings.append(("FAIL", "{} is empty".format(rel)))
            continue  # shebang/exec warnings are noise on an empty file
        sane += 1
        if name.lower().endswith(".sh"):
            if not os.stat(path).st_mode & 0o111:
                findings.append(("WARN", "{} is not executable".format(rel)))
            if not first_line(path).startswith("#!"):
                findings.append(("WARN", "{} has no shebang on line 1".format(rel)))
    if sane and not any(lvl in ("FAIL", "WARN") for lvl, _ in findings[mark:]):
        findings.append(("PASS", "scripts/: {} script file(s) non-empty with sane modes".format(sane)))


def check_top_level(root, findings):
    try:
        entries = sorted(os.listdir(root))
    except OSError as exc:
        raise IoError("cannot list {}: {}".format(root, exc.strerror or exc))
    extra = [e for e in entries if e not in ALLOWED_TOP]
    if extra:
        findings.append((
            "SKIP",
            "unexpected top-level entries (informational, not a failure): " + ", ".join(extra),
        ))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate agent skill directory structure (SKILL.md, internal refs, scripts/)."
    )
    parser.add_argument("skill_dir", help="path to the skill directory")
    parser.add_argument("--json", action="store_true", help="emit a single JSON object to stdout")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.skill_dir)
    if not os.path.isdir(root):
        print("error: not a directory: {}".format(args.skill_dir), file=sys.stderr)
        return 2

    findings = []
    try:
        check_skill_md(root, findings)
        check_references(root, findings)
        check_scripts(root, findings)
        check_top_level(root, findings)
    except IoError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    levels = [lvl for lvl, _ in findings]
    overall = "FAIL" if "FAIL" in levels else ("WARN" if "WARN" in levels else "PASS")
    if args.json:
        print(json.dumps(
            {
                "skill": args.skill_dir,
                "findings": [{"level": lvl, "phase": PHASE, "message": msg} for lvl, msg in findings],
                "overall": overall,
            },
            indent=2,
        ))
    else:
        for lvl, msg in findings:
            print("{}  [{}] {}".format(lvl, PHASE, msg))
        print("OVERALL: {}".format(overall))
    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
