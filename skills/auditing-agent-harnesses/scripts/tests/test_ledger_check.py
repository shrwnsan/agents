#!/usr/bin/env python3
"""Offline tests for ledger-check.py and generate-coverage-table.py.

Run from the skill directory:

    python3 scripts/tests/test_ledger_check.py
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parents[1] / "ledger-check.py"
GEN = Path(__file__).resolve().parents[1] / "generate-coverage-table.py"

VALID = {
    "round_date": "2026-11-12",
    "version": "3.18.1.10376",
    "app": "zcode",
    "validation": "dual-run",
    "coverage": {f"C{i}": "evidence" for i in range(1, 10)},
}


def run_check(rows):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
        path = f.name
    return subprocess.run(
        [sys.executable, str(CHECK), path], capture_output=True, text=True
    )


class LedgerCheckTests(unittest.TestCase):
    def test_valid_line_passes(self):
        r = run_check([VALID])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 rounds", r.stdout)

    def test_missing_class_fails(self):
        row = dict(VALID, coverage={f"C{i}": "evidence" for i in range(1, 9)})
        r = run_check([row])
        self.assertEqual(r.returncode, 1)
        self.assertIn("C9", r.stdout)

    def test_unknown_class_fails(self):
        row = dict(VALID, coverage={**VALID["coverage"], "C10": "evidence"})
        r = run_check([row])
        self.assertEqual(r.returncode, 1)
        self.assertIn("C10", r.stdout)

    def test_bad_validation_enum_fails(self):
        r = run_check([dict(VALID, validation="vibes")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("dual-run|solo", r.stdout)

    def test_carryover_after_round_date_fails(self):
        row = dict(
            VALID,
            round_date="2026-11-12",
            validation="carryover:2026-11-20",
            coverage={f"C{i}": "carryover:2026-11-20" for i in range(1, 10)},
        )
        r = run_check([row])
        self.assertEqual(r.returncode, 1)
        self.assertIn("after this round", r.stdout)

    def test_carryover_provenance_passes(self):
        row = dict(
            VALID,
            validation="carryover:2026-10-23",
            coverage={f"C{i}": "carryover:2026-10-23" for i in range(1, 10)},
        )
        r = run_check([row])
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_auto_below_threshold_fails(self):
        row = dict(
            VALID,
            jev={"model": "jev-1.14.0", "threshold": 0.75,
                 "windows": [{"conf": 0.31, "auto": True, "rule": "below-threshold"}]},
        )
        r = run_check([row])
        self.assertEqual(r.returncode, 1)
        self.assertIn("below threshold", r.stdout)

    def test_high_conf_benign_rule_passes(self):
        row = dict(
            VALID,
            jev={"model": "jev-1.14.0", "threshold": 0.75,
                 "windows": [{"conf": 0.89, "auto": False, "rule": "pipeline-benign-regardless"}]},
        )
        r = run_check([row])
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_high_conf_below_threshold_rule_fails(self):
        row = dict(
            VALID,
            jev={"model": "jev-1.14.0", "threshold": 0.75,
                 "windows": [{"conf": 0.89, "auto": False, "rule": "below-threshold"}]},
        )
        r = run_check([row])
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot be below-threshold", r.stdout)

    def test_unknown_rule_fails(self):
        row = dict(
            VALID,
            jev={"model": "jev-1.14.0", "threshold": 0.75,
                 "windows": [{"conf": 0.31, "auto": False, "rule": "vibes"}]},
        )
        r = run_check([row])
        self.assertEqual(r.returncode, 1)
        self.assertIn("rule", r.stdout)


class GeneratorTests(unittest.TestCase):
    def test_table_lists_round_and_version(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps(VALID) + "\n")
            path = f.name
        r = subprocess.run(
            [sys.executable, str(GEN), path], capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("2026-11-12", r.stdout)
        self.assertIn("3.18.1.10376", r.stdout)
        self.assertIn("GENERATED", r.stdout)
        self.assertIn("✓ | ✓", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
