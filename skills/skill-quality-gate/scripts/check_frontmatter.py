#!/usr/bin/env python3
"""Static frontmatter validator for an agent skill's SKILL.md.

Parses only the leading `---` fenced block with a minimal YAML-subset parser
(flat `key: value`, `>` / `|` block scalars with chomping indicators, double /
single-quoted scalars, inline `[a, b]` lists, `- item` block lists, one level
of nested `key: value` mapping -- enough for `metadata`). Anything outside
that subset is a FAIL with a line number, per spec.

Field rules follow docs/ref-001-skill-frontmatter.md (agentskills.io open
standard + Claude Code extensions). Unknown top-level keys are SKIP, never
FAIL: CC extensions like `user-invocable` are legitimate.

Usage: python3 check_frontmatter.py <skill-dir> [--json]
Exit codes: 0 = no FAIL findings, 1 = at least one FAIL, 2 = usage/IO error.
Python 3.9+, stdlib only.
"""

import argparse
import json
import os
import re
import sys

PHASE = "frontmatter"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):(?:[ \t]+(.*))?$")
LIST_ITEM_RE = re.compile(r"^-\s+(.*)$")

# agentskills.io open standard (ref-001)
STANDARD_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
# Claude Code extensions (ref-001)
CC_KEYS = {
    "argument-hint", "disable-model-invocation", "user-invocable", "model",
    "effort", "context", "hooks", "paths", "shell",
}
KNOWN_KEYS = STANDARD_KEYS | CC_KEYS

FIRST_PERSON = ("I ", "We ", "This skill will")

# A chain of >=3 comma-separated phrases each starting with a third-person
# singular verb ("It reads X, detects Y, and writes Z") narrates an execution
# sequence -- a workflow the agent may follow instead of reading the body.
# Imperative/base-form verbs ("Scan for and remove temp files") are the
# recommended what+when style and deliberately do not match.
WORKFLOW_VERBS = (
    "reads", "detects", "normalizes", "deduplicates", "parses", "writes",
    "scans", "extracts", "converts", "validates", "loads", "runs", "iterates",
    "filters", "sorts", "merges", "splits", "copies", "deletes", "removes",
    "generates", "creates", "builds", "checks", "compares", "computes",
    "applies", "fetches", "queries", "resolves", "renders", "uploads",
    "downloads", "executes", "invokes", "calls", "trims", "cleans", "formats",
    "serializes", "deserializes", "walks", "maps", "reduces", "counts",
    "summarizes", "reports", "confirms", "prompts", "verifies",
)


class FmError(Exception):
    def __init__(self, line_no, msg):
        super().__init__("line {}: {}".format(line_no, msg))
        self.line_no = line_no
        self.msg = msg


class IoError(Exception):
    """Unreadable file -- maps to exit code 2."""


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError as exc:
        raise IoError("cannot read {}: {}".format(path, exc.strerror or exc))


# --------------------------------------------------------------------------
# Minimal YAML-subset parser
# --------------------------------------------------------------------------

def split_frontmatter(text):
    """Return (fm_lines, first_line_no_1based) or raise FmError."""
    lines = text.split("\n")
    if lines and lines[0].startswith("\ufeff"):  # tolerate a leading BOM
        lines[0] = lines[0][1:]
    if not lines or lines[0].rstrip("\r").strip() != "---":
        raise FmError(1, "no frontmatter block: file does not start with '---'")
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\r").strip() == "---":
            return [ln.rstrip("\r") for ln in lines[1:idx]], 2
    raise FmError(1, "frontmatter block not closed: missing closing '---'")


def unquote_scalar(s):
    """Strip quotes / trailing comment from a scalar string."""
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        body = s[1:-1]
        for esc, ch in (('\\"', '"'), ("\\\\", "\\"), ("\\n", "\n"), ("\\t", "\t")):
            body = body.replace(esc, ch)
        return body
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    hash_idx = s.find(" #")  # ' #' starts a comment on plain scalars
    if hash_idx != -1:
        s = s[:hash_idx]
    return s.strip()


def split_top_commas(s):
    """Split on commas that are outside quotes and not nested in [] or {}."""
    parts, buf, quote, depth = [], [], None, 0
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf)
    if tail.strip():
        parts.append(tail)
    return parts


def parse_inline_map(s, line_no):
    if not s.endswith("}"):
        raise FmError(line_no, "unterminated inline map: " + s[:60])
    out = {}
    for part in split_top_commas(s[1:-1]):
        if ":" not in part:
            raise FmError(line_no, "unparseable inline map entry: " + part.strip()[:60])
        k, v = part.split(":", 1)
        out[unquote_scalar(k)] = unquote_scalar(v)
    return out


def parse_block_scalar(lines, i, indicator, base_ln):
    """`key: >` / `key: |` with optional -, + chomping. Returns (value, consumed)."""
    style = indicator[0]
    chomp = indicator[1:]
    if chomp not in ("", "-", "+"):
        raise FmError(base_ln + i, "unparseable block scalar indicator: " + indicator)
    n, j, chunk, block_indent = len(lines), i + 1, [], None
    while j < n:
        nxt = lines[j]
        if not nxt.strip():
            chunk.append("")
            j += 1
            continue
        if nxt[0] not in " \t":
            break
        indent = len(nxt) - len(nxt.lstrip(" "))
        if block_indent is None:
            block_indent = indent
        chunk.append(nxt[block_indent:] if indent >= block_indent else nxt.lstrip())
        j += 1
    while chunk and chunk[-1] == "":
        chunk.pop()
    if style == ">":
        value = " ".join(" ".join(chunk).split())
    else:
        value = "\n".join(chunk)
    if chomp == "-":
        value = value.rstrip()
    return value, (j - i)


def parse_value(lines, i, match, base_ln):
    """Parse the value for the key at lines[i]. Returns (value, consumed)."""
    rest = (match.group(2) or "").strip()
    ln = base_ln + i
    if rest:
        if rest[0] in "|>":
            return parse_block_scalar(lines, i, rest, base_ln)
        if rest.startswith("["):
            if not rest.endswith("]"):
                raise FmError(ln, "unterminated inline list: " + rest[:60])
            return [unquote_scalar(p) for p in split_top_commas(rest[1:-1])], 1
        if rest.startswith("{"):
            return parse_inline_map(rest, ln), 1
        return unquote_scalar(rest), 1

    # Empty after the colon: block list, one-level nested map, or null.
    n = len(lines)
    j = i + 1
    while j < n and (not lines[j].strip() or lines[j].strip().startswith("#")):
        j += 1
    if j >= n or lines[j][0] not in " \t":
        return None, 1

    items, submap, is_list, is_map, sub_indent = [], {}, False, False, None
    last_key = None
    while j < n:
        nxt = lines[j]
        s = nxt.strip()
        if not s or s.startswith("#"):
            j += 1
            continue
        if nxt[0] not in " \t":
            break
        indent = len(nxt) - len(nxt.lstrip(" "))
        if sub_indent is None:
            sub_indent = indent
        ml, mm = LIST_ITEM_RE.match(s), KEY_RE.match(s)
        if indent > sub_indent:
            # Deeper than the first nested level: a `- item` run under a
            # subkey is a nested list -- record it so the field check FAILs
            # it; anything else genuinely exceeds the supported subset.
            if is_map and ml and last_key is not None:
                if not isinstance(submap.get(last_key), list):
                    submap[last_key] = []
                submap[last_key].append(unquote_scalar(ml.group(1)))
            else:
                raise FmError(base_ln + j, "nested maps/lists deeper than one level are not supported")
            j += 1
            continue
        if ml:
            if is_map:
                raise FmError(base_ln + j, "list item under a mapping key")
            is_list = True
            item = unquote_scalar(ml.group(1))
            if re.search(r":\s", item):
                raise FmError(base_ln + j, "list items must be plain scalars: " + item[:60])
            items.append(item)
        elif mm:
            if is_list:
                raise FmError(base_ln + j, "mapping entry under a list key")
            is_map = True
            last_key = mm.group(1)
            submap[last_key] = unquote_scalar(mm.group(2)) if mm.group(2) else None
        else:
            raise FmError(base_ln + j, "unparseable indented line (expected '- item' or 'key: value'): " + s[:60])
        j += 1
    if is_list:
        return items, (j - i)
    if is_map:
        return submap, (j - i)
    return None, 1


def parse_block(lines, base_ln):
    """Parse the frontmatter lines into a flat mapping.

    Returns (mapping, ordered_keys, duplicates, errors) where duplicates and
    errors are lists of (line_no, message).
    """
    mapping, order, dups, errors = {}, [], [], []
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        ln = base_ln + i
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if raw[0] in " \t":
            errors.append((ln, "unexpected indented line outside any key: " + stripped[:60]))
            i += 1
            continue
        match = KEY_RE.match(raw)
        if not match:
            errors.append((ln, "unparseable line (expected 'key: value'): " + stripped[:60]))
            i += 1
            continue
        key = match.group(1)
        if key in mapping:
            dups.append((ln, key))
        try:
            value, consumed = parse_value(lines, i, match, base_ln)
        except FmError as exc:
            errors.append((exc.line_no, exc.msg))
            value = None
            # Consume the rest of this key's indented block so its lines do
            # not re-report as cascading "unexpected indented line" errors.
            k = i + 1
            while k < n and lines[k][:1] in (" ", "\t"):
                k += 1
            consumed = k - i
        if key not in mapping:  # first definition wins on duplicates
            mapping[key] = value
            order.append(key)
        i += consumed
    return mapping, order, dups, errors


# --------------------------------------------------------------------------
# Field checks
# --------------------------------------------------------------------------

def longest_verb_chain(text):
    """Longest run of consecutive comma-separated phrases starting with a
    third-person singular workflow verb."""
    chain = best = 0
    for seg in text.split(","):
        seg = re.sub(r"^(and|or)\s+", "", seg.strip(), flags=re.I).lower()
        if any(seg.startswith(v + " ") for v in WORKFLOW_VERBS):
            chain += 1
            best = max(best, chain)
        else:
            chain = 0
    return best


def check_name(root, mapping, findings):
    raw = mapping.get("name")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        findings.append(("FAIL", "required key 'name' is missing or empty"))
        return
    if isinstance(raw, (list, dict)):
        findings.append(("FAIL", "'name' must be a plain scalar, got a list/map"))
        return
    name = str(raw).strip()
    if len(name) > 64:
        findings.append(("FAIL", "name is {} chars (max 64): {!r}".format(len(name), name[:64] + "...")))
    else:
        findings.append(("PASS", "name length OK ({}/64 chars)".format(len(name))))
    if not NAME_RE.match(name):
        findings.append((
            "FAIL",
            "name {!r} does not match ^[a-z0-9]+(-[a-z0-9]+)*$ "
            "(lowercase alphanumeric + hyphens)".format(name),
        ))
    base = os.path.basename(root)
    if name != base:
        findings.append(("FAIL", "name {!r} does not match directory basename {!r}".format(name, base)))
    else:
        findings.append(("PASS", "name matches directory basename {!r}".format(base)))


def check_description(mapping, findings):
    raw = mapping.get("description")
    if isinstance(raw, (list, dict)):
        findings.append(("FAIL", "'description' must be a plain scalar, got a list/map"))
        return
    if raw is None or not str(raw).strip():
        findings.append(("FAIL", "required key 'description' is missing or empty"))
        return
    desc = str(raw)
    length = len(desc)
    if length > 1024:
        findings.append(("FAIL", "description is {} chars (max 1024)".format(length)))
    elif length > 250:
        findings.append((
            "SKIP",
            "description is {} chars (>250; Claude Code listing truncates at 250)".format(length),
        ))
    else:
        findings.append(("PASS", "description present ({} chars)".format(length)))

    if desc.startswith(FIRST_PERSON):
        findings.append((
            "WARN",
            "description opens first-person ({!r}); lead with what it does and "
            "when to trigger it".format(next(p for p in FIRST_PERSON if desc.startswith(p)).strip()),
        ))
    if re.search(r"\b1\.", desc) or re.search(r"step\s*1\s*:", desc, re.I):
        findings.append((
            "WARN",
            "description contains a numbered workflow ('1.'/'Step 1:'); it should give "
            "triggering conditions, not a procedure the agent will follow instead of the body",
        ))
    chain = longest_verb_chain(desc)
    if chain >= 3:
        findings.append((
            "WARN",
            "description narrates a {}-step workflow ('...reads X, detects Y, and writes Z'); "
            "give triggering conditions instead of an execution sequence".format(chain),
        ))


def check_remaining(root, mapping, order, findings):
    comp = mapping.get("compatibility")
    if comp is not None:
        if isinstance(comp, (list, dict)):
            findings.append(("FAIL", "'compatibility' must be a plain scalar, got a list/map"))
        elif len(str(comp)) > 500:
            findings.append(("FAIL", "compatibility is {} chars (max 500)".format(len(str(comp)))))
        else:
            findings.append(("PASS", "compatibility OK ({}/500 chars)".format(len(str(comp)))))

    meta = mapping.get("metadata")
    if meta is not None:
        if isinstance(meta, list):
            findings.append(("FAIL", "'metadata' must be a string-to-string map, got a list"))
        elif isinstance(meta, dict):
            for k, v in meta.items():
                if isinstance(v, (list, dict)):
                    findings.append((
                        "FAIL",
                        "metadata['{}'] must be a string or plain scalar, got a {}".format(
                            k, "list" if isinstance(v, list) else "map"
                        ),
                    ))
            if not any(isinstance(v, (list, dict)) for v in meta.values()):
                findings.append(("PASS", "metadata: {} string value(s)".format(len(meta))))
        else:
            findings.append((
                "WARN",
                "metadata is a bare scalar; the field is a string-to-string map "
                "(use indented 'key: value' entries)",
            ))

    if mapping.get("license") is not None:
        findings.append(("PASS", "license declared: {}".format(str(mapping["license"]).strip())))

    unknown = [k for k in order if k not in KNOWN_KEYS]
    if unknown:
        findings.append((
            "SKIP",
            "unknown top-level keys (informational; CC extensions like user-invocable "
            "are legitimate): " + ", ".join(unknown),
        ))


def run(skill_dir, findings):
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md):
        findings.append(("FAIL", "SKILL.md not found -- cannot validate frontmatter"))
        return
    text = read_text(md)
    try:
        fm_lines, base_ln = split_frontmatter(text)
    except FmError as exc:
        findings.append(("FAIL", "line {}: {}".format(exc.line_no, exc.msg)))
        findings.append(("FAIL", "required key 'name' is missing (frontmatter unparseable)"))
        findings.append(("FAIL", "required key 'description' is missing (frontmatter unparseable)"))
        return

    mapping, order, dups, errors = parse_block(fm_lines, base_ln)
    for ln, key in dups:
        findings.append(("FAIL", "line {}: duplicate top-level key '{}'".format(ln, key)))
    for ln, msg in errors:
        findings.append(("FAIL", "line {}: {}".format(ln, msg)))
    if not order and not dups:
        findings.append(("FAIL", "frontmatter block is empty"))
        findings.append(("FAIL", "required key 'name' is missing"))
        findings.append(("FAIL", "required key 'description' is missing"))
        return

    check_name(skill_dir, mapping, findings)
    check_description(mapping, findings)
    check_remaining(skill_dir, mapping, order, findings)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate agent skill SKILL.md frontmatter (ref-001 rules)."
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
        run(root, findings)
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
