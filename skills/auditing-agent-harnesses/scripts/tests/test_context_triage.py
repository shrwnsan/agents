#!/usr/bin/env python3
"""Offline tests for context-triage.py against a loopback mock of the System One API.

No real API traffic and no real key: a local HTTP server answers POSTs from a
per-test marker table (the first marker found as a substring of the request
state wins; a one-element answer list repeats, a longer list is consumed in
order) and answers GETs with a 404. Run from the skill directory:

    python3 scripts/tests/test_context_triage.py
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "context-triage.py"
SKILL_DIR = SCRIPT.parent.parent

ROUTES = {}
ROUTES_LOCK = threading.Lock()
PORT = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            body = {}
        state = body.get("state", "")
        answer = None
        with ROUTES_LOCK:
            for marker, seq in ROUTES.items():
                if marker in state:
                    answer = seq.pop(0) if len(seq) > 1 else seq[0]
                    break
        if answer is None:
            self.send_response(500)  # unregistered marker: loud, not silent
            self.end_headers()
            return
        choice, confidence = answer
        payload = json.dumps({
            "answers": {"classification": {"choice": choice, "confidence": confidence}},
            "model": "mock-jev-0",
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def setUpModule():
    global PORT
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    PORT = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()


def register(marker, answers):
    with ROUTES_LOCK:
        ROUTES[marker] = list(answers)


def write_jsonl(dirpath, name, rows):
    path = Path(dirpath) / name
    with open(path, "w") as f:
        for row in rows:
            f.write((row if isinstance(row, str) else json.dumps(row)) + "\n")
    return path


def run_triage(*args, cwd=None, drop_key=False, extra_env=None, script=None):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TYPESAFE_BASE_URL"] = f"http://127.0.0.1:{PORT}/v1/systemone"
    env.pop("TYPESAFE_MODEL", None)
    if drop_key:
        env.pop("TYPESAFE_API_KEY", None)
    else:
        env["TYPESAFE_API_KEY"] = "test-key"
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(script or SCRIPT), *args],
        capture_output=True, text=True, cwd=cwd, env=env, timeout=60,
    )


def receipt_path(proc):
    lines = [l for l in proc.stdout.splitlines() if l.startswith("receipt: ")]
    assert lines, f"no receipt line in stdout: {proc.stdout!r} stderr: {proc.stderr!r}"
    return Path(lines[-1].split(": ", 1)[1])


def receipt_rows(proc):
    return [json.loads(l) for l in receipt_path(proc).read_text().splitlines()]


class TriageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_env = {"TRIAGE_OUT_DIR": self.tmp.name}

    def contexts(self, rows, marker, answers, *extra_args, **kwargs):
        register(marker, answers)
        source = write_jsonl(self.tmp.name, "contexts.jsonl", rows)
        return run_triage("contexts", str(source), "--delay", "0",
                          *extra_args, extra_env=self.out_env, **kwargs)


class AccessTests(TriageTest):
    def test_probe_needs_no_key(self):
        proc = run_triage("probe", drop_key=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("reachable status=404", proc.stdout)

    def test_baseline_requires_key(self):
        corpus = write_jsonl(self.tmp.name, "corpus.jsonl",
                             [{"id": "a", "label": "benign-vendored", "context": "M_KEY"}])
        proc = run_triage("baseline", "--corpus", str(corpus), drop_key=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("SKIP_REASON=TYPESAFE_API_KEY", proc.stderr)


class GateTests(TriageTest):
    def test_pipeline_benign_read_escalates(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_PBEN", "pipeline_shaped": True}],
            "M_PBEN", [("benign-vendored", 0.99)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(receipt_rows(proc)[0]["gate"], "escalate")

    def test_pipeline_feature_read_escalates(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_PFEAT", "pipeline_shaped": True}],
            "M_PFEAT", [("feature-wired", 0.99)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(receipt_rows(proc)[0]["gate"], "escalate")

    def test_pipeline_pipeline_read_auto_resolves(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_PPIPE", "pipeline_shaped": True}],
            "M_PPIPE", [("pipeline-indicator", 0.99)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(receipt_rows(proc)[0]["gate"], "auto-resolve")

    def test_unflagged_row_warns_and_auto_resolves(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_UNFLAG"}],
            "M_UNFLAG", [("benign-vendored", 0.99)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("pipeline_shaped", proc.stderr)
        row = receipt_rows(proc)[0]
        self.assertEqual(row["gate"], "auto-resolve")
        self.assertFalse(row["pipeline_shaped"])

    def test_below_threshold_escalates(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_LOWCONF", "pipeline_shaped": False}],
            "M_LOWCONF", [("benign-vendored", 0.60)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(receipt_rows(proc)[0]["gate"], "escalate")

    def test_confirm_band_keeps_lower_confidence(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_BAND", "pipeline_shaped": False}],
            "M_BAND", [("feature-wired", 0.77), ("feature-wired", 0.72)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        row = receipt_rows(proc)[0]
        self.assertEqual(row["confidence"], 0.72)
        self.assertTrue(row["confirm_rerun"])
        self.assertNotIn("confirm_class_flip", row)

    def test_confirm_band_class_flip_escalates(self):
        proc = self.contexts(
            [{"id": "t", "context": "M_FLIP", "pipeline_shaped": False}],
            "M_FLIP", [("feature-wired", 0.77), ("benign-vendored", 0.90)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        row = receipt_rows(proc)[0]
        self.assertEqual(row["predicted"], "feature-wired")  # kept lower confidence
        self.assertEqual(row["gate"], "escalate")
        self.assertTrue(row["confirm_class_flip"])


class ReceiptTests(TriageTest):
    def test_receipt_extensions(self):
        register("M_EXT", [("benign-vendored", 0.99)])
        source = write_jsonl(self.tmp.name, "contexts.jsonl",
                             [{"id": "t", "context": "M_EXT", "pipeline_shaped": False}])
        proc = run_triage("contexts", str(source), "--delay", "0", extra_env=self.out_env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(str(receipt_path(proc)).endswith(".jsonl"))

        corpus = write_jsonl(self.tmp.name, "corpus.jsonl",
                             [{"id": "c", "label": "benign-vendored", "context": "M_EXT",
                               "pipeline_shaped": False}])
        proc = run_triage("baseline", "--corpus", str(corpus), "--delay", "0",
                          "--reps", "1", extra_env=self.out_env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(str(receipt_path(proc)).endswith(".json"))

    def test_out_inside_skill_dir_refused(self):
        register("M_OUTGUARD", [("benign-vendored", 0.99)])
        source = write_jsonl(self.tmp.name, "contexts.jsonl",
                             [{"id": "t", "context": "M_OUTGUARD", "pipeline_shaped": False}])
        target = SKILL_DIR / "evil.jsonl"
        self.addCleanup(lambda: target.unlink(missing_ok=True))
        proc = run_triage("contexts", str(source), "--delay", "0",
                          "--out", str(target), extra_env=self.out_env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("skill directory", proc.stderr)
        self.assertFalse(target.exists())

    def test_cwd_inside_skill_dir_relocates_with_notice(self):
        register("M_RELOC", [("benign-vendored", 0.99)])
        source = write_jsonl(self.tmp.name, "contexts.jsonl",
                             [{"id": "t", "context": "M_RELOC", "pipeline_shaped": False}])
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        scratch_real = os.path.realpath(scratch.name)
        proc = run_triage("contexts", str(source), "--delay", "0",
                          cwd=SCRIPT.parent,
                          extra_env={"TMPDIR": scratch_real})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = receipt_path(proc)
        self.assertTrue(str(out).startswith(scratch_real),
                        f"receipt not relocated to TMPDIR: {out}")
        self.assertTrue(str(out).endswith(".jsonl"))
        self.assertIn("skill directory", proc.stderr)

    def test_symlinked_script_still_guards_and_finds_corpus(self):
        register("M_SYMLINK", [("benign-vendored", 0.99)])
        source = write_jsonl(self.tmp.name, "contexts.jsonl",
                             [{"id": "t", "context": "M_SYMLINK", "pipeline_shaped": False}])
        link = Path(self.tmp.name) / "context-triage.py"
        link.symlink_to(SCRIPT)
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        scratch_real = os.path.realpath(scratch.name)
        before = set(SCRIPT.parent.glob("triage-contexts-*"))
        self.addCleanup(lambda: [p.unlink(missing_ok=True)
                                 for p in set(SCRIPT.parent.glob("triage-contexts-*")) - before])
        proc = run_triage("contexts", str(source), "--delay", "0",
                          cwd=SCRIPT.parent, script=link,
                          extra_env={"TMPDIR": scratch_real})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = receipt_path(proc)
        self.assertTrue(str(out).startswith(scratch_real),
                        f"receipt escaped the guard via symlinked script: {out}")
        self.assertFalse(set(SCRIPT.parent.glob("triage-contexts-*")) - before)

        corpus = write_jsonl(self.tmp.name, "corpus.jsonl",
                             [{"id": "c", "label": "benign-vendored", "context": "M_SYMLINK",
                               "pipeline_shaped": False}])
        proc = run_triage("baseline", "--corpus", str(corpus), "--delay", "0",
                          "--reps", "1", script=link, extra_env=self.out_env)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class InputValidationTests(TriageTest):
    def test_non_object_row_rejected_before_receipt(self):
        source = write_jsonl(self.tmp.name, "contexts.jsonl", [
            {"id": "ok", "context": "M_NOBJ", "pipeline_shaped": False},
            ["not", "an", "object"],
        ])
        proc = run_triage("contexts", str(source), "--delay", "0", extra_env=self.out_env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("line 2", proc.stderr)
        self.assertEqual(list(Path(self.tmp.name).glob("triage-contexts-*")), [])

    def test_missing_context_field_rejected(self):
        source = write_jsonl(self.tmp.name, "contexts.jsonl", [{"id": "x"}])
        proc = run_triage("contexts", str(source), "--delay", "0", extra_env=self.out_env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("'context'", proc.stderr)
        self.assertEqual(list(Path(self.tmp.name).glob("triage-contexts-*")), [])

    def test_reps_zero_rejected(self):
        corpus = write_jsonl(self.tmp.name, "corpus.jsonl",
                             [{"id": "a", "label": "benign-vendored", "context": "M_REPS"}])
        proc = run_triage("baseline", "--corpus", str(corpus), "--reps", "0",
                          "--delay", "0", extra_env=self.out_env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--reps", proc.stderr)


class CorpusTests(TriageTest):
    def synthetic_positives(self):
        corpus = SKILL_DIR / "assets" / "corpus.jsonl"
        return [row for line in corpus.read_text().splitlines() if line.strip()
                for row in [json.loads(line)]
                if row.get("synthetic") and row.get("label") == "pipeline-indicator"]

    def test_synthetic_pipeline_positives_are_flagged(self):
        rows = self.synthetic_positives()
        self.assertEqual(len(rows), 7)
        for row in rows:
            self.assertIs(row.get("pipeline_shaped"), True, row["id"])

    def test_packaged_positives_gate_every_prediction_class(self):
        rows = self.synthetic_positives()
        self.assertEqual(len(rows), 7)
        corpus = write_jsonl(self.tmp.name, "positives.jsonl", rows)
        for predicted in ("benign-vendored", "feature-wired",
                          "declared-telemetry", "pipeline-indicator"):
            with self.subTest(predicted=predicted):
                for row in rows:
                    register(row["context"], [(predicted, 0.99)])
                out = Path(self.tmp.name) / f"{predicted}.json"
                proc = run_triage("baseline", "--corpus", str(corpus),
                                  "--delay", "0", "--reps", "1", "--out", str(out),
                                  extra_env=self.out_env)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                receipt = json.loads(receipt_path(proc).read_text())
                self.assertEqual(len(receipt["rows"]), 7)
                expected = "auto-resolve" if predicted == "pipeline-indicator" else "escalate"
                for row in receipt["rows"]:
                    self.assertEqual(row.get("gate"), expected, row["id"])
                    self.assertIs(row.get("pipeline_shaped"), True, row["id"])
                self.assertNotIn("lack pipeline_shaped", proc.stderr)


class BaselineTests(TriageTest):
    def test_unflagged_warning_names_every_row(self):
        register("M_ALL", [("pipeline-indicator", 0.9)])
        rows = [{"id": f"p{i}", "label": "pipeline-indicator", "context": f"M_ALL {i}"}
                for i in range(7)]
        corpus = write_jsonl(self.tmp.name, "corpus.jsonl", rows)
        proc = run_triage("baseline", "--corpus", str(corpus), "--delay", "0",
                          "--reps", "1", extra_env=self.out_env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for i in range(7):
            self.assertIn(f"p{i}", proc.stderr)
        self.assertNotIn(" ...", proc.stderr)

    def test_unflagged_pipeline_positive_warns_and_summary_counts(self):
        register("M_BUNFLAG", [("pipeline-indicator", 0.9)])
        register("M_BMISS", [("benign-vendored", 0.9)])
        register("M_BNEG", [("benign-vendored", 0.9)])
        corpus = write_jsonl(self.tmp.name, "corpus.jsonl", [
            {"id": "pos-unflagged", "label": "pipeline-indicator", "context": "M_BUNFLAG"},
            {"id": "pos-flagged", "label": "pipeline-indicator", "context": "M_BMISS",
             "pipeline_shaped": True},
            {"id": "neg", "label": "benign-vendored", "context": "M_BNEG",
             "pipeline_shaped": False},
        ])
        proc = run_triage("baseline", "--corpus", str(corpus), "--delay", "0",
                          "--reps", "1", extra_env=self.out_env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("pos-unflagged", proc.stderr)
        self.assertNotIn("'neg'", proc.stderr)

        receipt = json.loads(receipt_path(proc).read_text())
        summary = receipt["summary"]
        self.assertEqual(summary["pipeline_false_clears"], 1)
        self.assertEqual(summary["pipeline_shaped_missed"], 1)
        rows = {r["id"]: r for r in receipt["rows"]}
        self.assertEqual(rows["pos-flagged"]["gate"], "escalate")
        self.assertEqual(rows["pos-unflagged"]["gate"], "auto-resolve")
        self.assertEqual(rows["pos-unflagged"]["model"], "mock-jev-0")


if __name__ == "__main__":
    unittest.main()
