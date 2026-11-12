#!/usr/bin/env python3
"""Validate an app coverage ledger for auditing-agent-harnesses (Phase 4 artifact).

One JSON object per line, one line per audit round:

  {"round_date": "2026-11-12", "version": "3.18.1.10376", "app": "zcode",
   "validation": "dual-run",
   "coverage": {"C1": "evidence", "C2": "carryover:2026-11-02", ..., "C9": "n/a"},
   "jev": {"model": "jev-1.14.0", "threshold": 0.75,
           "windows": [{"conf": 0.89, "auto": false, "rule": "pipeline-benign-regardless"}]}}

The checker is the enforcement behind the coverage contract: a round whose
ledger line does not pass this check is not closed. All failures print with
line numbers and exit 1.

Usage:
  ledger-check.py LEDGER.jsonl [--quiet]
"""

import argparse
import json
import re
import sys

CLASSES = [f"C{i}" for i in range(1, 10)]
VALIDATIONS = {"dual-run", "solo", "multi-agent"}
COVERAGE_PLAIN = {"evidence", "n/a"}
CARRYOVER = re.compile(r"^carryover:(\d{4}-\d{2}-\d{2})$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RULES = {
    "below-threshold",
    "pipeline-benign-regardless",
    "confirm-band-lowered",
    "backfill",
}
REQUIRED = ("round_date", "version", "app", "validation", "coverage")


def check_line(n, row):
    errors = []

    def bad(msg):
        errors.append(f"line {n}: {msg}")

    for key in REQUIRED:
        if key not in row:
            bad(f"missing required key '{key}'")
    if errors:
        return errors

    if not DATE.match(str(row["round_date"])):
        bad(f"round_date '{row['round_date']}' is not YYYY-MM-DD")
    for key in ("version", "app"):
        if not isinstance(row[key], str) or not row[key].strip():
            bad(f"'{key}' must be a non-empty string")

    val = row["validation"]
    carry_src = None
    if val in VALIDATIONS:
        pass
    else:
        m = CARRYOVER.match(str(val))
        if not m:
            bad(f"validation '{val}' is not dual-run|solo|multi-agent|carryover:YYYY-MM-DD")
        else:
            carry_src = m.group(1)
            if not DATE.match(carry_src):
                bad(f"carryover date '{carry_src}' is not YYYY-MM-DD")

    cov = row["coverage"]
    if not isinstance(cov, dict):
        bad("'coverage' must be an object")
    else:
        keys, extra = set(cov), set(CLASSES)
        missing = extra - keys
        unknown = keys - extra
        if missing:
            bad(f"coverage missing classes: {', '.join(sorted(missing))}")
        if unknown:
            bad(f"coverage has unknown classes: {', '.join(sorted(unknown))}")
        for k in CLASSES:
            if k not in cov:
                continue
            v = cov[k]
            if v in COVERAGE_PLAIN:
                continue
            m = CARRYOVER.match(str(v))
            if not m:
                bad(f"coverage[{k}] '{v}' is not evidence|n/a|carryover:YYYY-MM-DD")
                continue
            d = m.group(1)
            if not DATE.match(d):
                bad(f"coverage[{k}] carryover date '{d}' is not YYYY-MM-DD")
            elif carry_src and d > carry_src:
                bad(f"coverage[{k}] carries from {d}, after the validation carryover source {carry_src}")
            elif "round_date" in row and d > row["round_date"]:
                bad(f"coverage[{k}] carries from {d}, after this round {row['round_date']}")

    jev = row.get("jev")
    if jev is not None:
        if not isinstance(jev, dict):
            bad("'jev' must be an object")
        else:
            for key in ("model", "threshold", "windows"):
                if key not in jev:
                    bad(f"jev missing '{key}'")
            thr = jev.get("threshold")
            if thr is not None and not (isinstance(thr, (int, float)) and 0 <= thr <= 1):
                bad(f"jev.threshold {thr!r} is not a number in [0,1]")
            wins = jev.get("windows")
            if wins is not None:
                if not isinstance(wins, list):
                    bad("'jev.windows' must be an array")
                else:
                    for i, w in enumerate(wins):
                        conf, auto, rule = w.get("conf"), w.get("auto"), w.get("rule")
                        if not (isinstance(conf, (int, float)) and 0 <= conf <= 1):
                            bad(f"jev.windows[{i}].conf {conf!r} is not a number in [0,1]")
                        if not isinstance(auto, bool):
                            bad(f"jev.windows[{i}].auto must be a boolean")
                        if rule not in RULES:
                            bad(f"jev.windows[{i}].rule '{rule}' is not one of {sorted(RULES)}")
                            continue
                        if isinstance(conf, (int, float)) and isinstance(auto, bool) and isinstance(thr, (int, float)):
                            if auto and conf < thr:
                                bad(f"jev.windows[{i}] auto=true at conf {conf} below threshold {thr}")
                            if (not auto) and conf >= thr and rule == "below-threshold":
                                bad(f"jev.windows[{i}] auto=false at conf {conf} >= threshold {thr} cannot be below-threshold")
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ledger")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    failures = 0
    rounds = 0
    with open(args.ledger) as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rounds += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                failures += 1
                if not args.quiet:
                    print(f"line {n}: invalid JSON: {e.msg}")
                continue
            for msg in check_line(n, row):
                failures += 1
                if not args.quiet:
                    print(msg)
    if failures:
        print(f"FAIL {args.ledger}: {failures} error(s) across {rounds} rounds")
        return 1
    print(f"OK {args.ledger}: {rounds} rounds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
