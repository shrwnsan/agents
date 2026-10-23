#!/usr/bin/env python3
"""Context-triage harness for auditing-agent-harnesses (TypeSafe System One API; measured on jev-latest).

Modes:
  baseline   Score assets/corpus.jsonl against its labels (reproduces the
             2026-10-02 eval-024 baseline; refresh receipts land in
             references/baseline-results.json).
  contexts   Triage new byte-window contexts from a JSONL file
             (rows: id, context, optional pipeline_shaped). Emits one JSONL
             row per context: predicted label, confidence, gate decision.

Gating (advisory only — Jev never issues the audit verdict):
  auto-resolve  confidence >= 0.75 AND NOT (pipeline_shaped AND benign prediction)
  escalate      everything else; a pipeline-shaped needle scoring benign
                escalates regardless of confidence (false-clear is disqualifying)

The 0.75 threshold is model-specific (measured on jev-latest only) — re-run
`baseline` before trusting it on any other model or provider.

Output defaults to the current working directory with a timestamped name
(the documented deliverable location for skill scripts) and refuses to
overwrite; TRIAGE_OUT_DIR moves receipts elsewhere. Receipts are never
written inside the skill directory.

Usage:
  context-triage.py baseline [--corpus PATH] [--delay S] [--out PATH] [--force]
  context-triage.py contexts FILE [--delay S] [--out PATH] [--force]

Env: TYPESAFE_API_KEY (required; presence-checked, never printed),
TYPESAFE_BASE_URL (gateway/compat override).
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

API = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1/systemone")
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_CORPUS = os.path.join(SKILL_DIR, "assets", "corpus.jsonl")

AUTO_RESOLVE_THRESHOLD = 0.75

QUESTIONS = {
    "classification": {
        "type": "choice",
        "instructions": (
            "This is a raw byte-window excerpt extracted from a macOS desktop "
            "app binary during a privacy audit. Classify what the excerpt "
            "shows, judging only from the excerpt itself."
        ),
        "criteria": {
            "pipeline-indicator": (
                "Code that packages the user's files or workspace (for example "
                ".git directories) into an archive, encrypts it with keys "
                "supplied by a server, uploads it to cloud storage, or requests "
                "credentials to do so — a silent data-ingestion pipeline"
            ),
            "declared-telemetry": (
                "Analytics, crash-reporting, or metrics SDK code that sends "
                "events or crash reports to a telemetry vendor endpoint"
            ),
            "feature-wired": (
                "A user-facing product feature that legitimately touches "
                "sensitive resources: screen recording, remote-control relay, "
                "chat-bot integration, app update checking, or attaching a file "
                "to a support ticket the user filed"
            ),
            "benign-vendored": (
                "Vendored library internals, asset filenames, media-format "
                "parser strings, public-suffix lists, name-only vocabulary "
                "lists, or unrelated identifiers that merely resemble "
                "sensitive keywords"
            ),
        },
    },
    "upload_risk": {
        "type": "noul",
        "instructions": (
            "This excerpt shows code that sends the user's files or workspace "
            "content to a remote server without the user asking for it."
        ),
    },
}


def call_jev(state: str, delay: float) -> dict:
    body = json.dumps(
        {"state": state, "model": "jev-latest", "questions": QUESTIONS}
    ).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(delay * 4 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def open_out(path: str | None, kind: str, force: bool) -> str:
    """Resolve the output path: --out wins; default is CWD timestamped
    (never inside the skill dir — accidental skill pollution guard)."""
    if path is None:
        name = f"{kind}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        path = os.path.join(
            os.environ.get("TRIAGE_OUT_DIR", os.getcwd()), name
        )
        path = os.path.abspath(path)
        if path.startswith(SKILL_DIR + os.sep):
            path = os.path.join(
                os.environ.get("TMPDIR", "/tmp"), name
            )
    path = os.path.abspath(path)
    if os.path.exists(path) and not force:
        sys.exit(f"output exists: {path} (--force to overwrite)")
    return path


def gate(predicted: str | None, confidence: float | None, pipeline_shaped: bool) -> str:
    if confidence is None or confidence < AUTO_RESOLVE_THRESHOLD:
        return "escalate"
    if pipeline_shaped and predicted == "benign-vendored":
        return "escalate"  # false-clear direction is disqualifying
    return "auto-resolve"


def run_baseline(corpus_path: str, delay: float, out: str | None, force: bool) -> int:
    with open(corpus_path) as f:
        corpus = [json.loads(line) for line in f if line.strip()]

    rows = []
    for s in corpus:
        try:
            r = call_jev(s["context"], delay)
            cls = r.get("answers", {}).get("classification", {})
            predicted, confidence = cls.get("choice"), cls.get("confidence")
            rows.append({
                "id": s["id"],
                "label": s["label"],
                "predicted": predicted,
                "confidence": confidence,
                "pipeline_shaped": s.get("pipeline_shaped", False),
                "gate": gate(predicted, confidence, s.get("pipeline_shaped", False)),
                "model": r.get("model"),
            })
        except Exception as e:  # noqa: BLE001 — record and continue
            rows.append({"id": s["id"], "label": s["label"], "error": str(e)})
        time.sleep(delay)

    out_path = open_out(out, "triage-baseline", force)
    with open(out_path, "w") as f:
        json.dump({"summary": summarize_baseline(rows), "rows": rows}, f, indent=2)
    print(json.dumps(summarize_baseline(rows), indent=2))
    print(f"receipt: {out_path}")
    return 0


def summarize_baseline(rows: list[dict]) -> dict:
    labeled = [r for r in rows if "error" not in r]
    correct = [r for r in labeled if r.get("predicted") == r["label"]]
    n = len(labeled)
    conf_ok = [r["confidence"] for r in correct if r.get("confidence") is not None]
    conf_bad = [
        r["confidence"] for r in labeled
        if r.get("predicted") != r["label"] and r.get("confidence") is not None
    ]
    pipeline_benign = [
        r for r in labeled
        if r.get("pipeline_shaped") and r.get("predicted") == "benign-vendored"
    ]
    return {
        "total": len(rows),
        "scored": n,
        "errors": len(rows) - n,
        "accuracy": round(len(correct) / n, 3) if n else 0.0,
        "mean_confidence_correct": round(sum(conf_ok) / len(conf_ok), 3) if conf_ok else None,
        "mean_confidence_wrong": round(sum(conf_bad) / len(conf_bad), 3) if conf_bad else None,
        "pipeline_false_clears": len(pipeline_benign),
        "misclassified": [
            {"id": r["id"], "label": r["label"], "predicted": r.get("predicted"),
             "confidence": r.get("confidence")}
            for r in labeled if r.get("predicted") != r["label"]
        ],
    }


def run_contexts(path: str, delay: float, out: str | None, force: bool) -> int:
    with open(path) as f:
        contexts = [json.loads(line) for line in f if line.strip()]

    out_path = open_out(out, "triage-contexts", force)
    with open(out_path, "w") as f:
        for c in contexts:
            try:
                r = call_jev(c["context"], delay)
                cls = r.get("answers", {}).get("classification", {})
                predicted, confidence = cls.get("choice"), cls.get("confidence")
                row = {
                    "id": c["id"],
                    "predicted": predicted,
                    "confidence": confidence,
                    "pipeline_shaped": c.get("pipeline_shaped", False),
                    "gate": gate(predicted, confidence, c.get("pipeline_shaped", False)),
                }
            except Exception as e:  # noqa: BLE001
                row = {"id": c["id"], "error": str(e)}
            f.write(json.dumps(row) + "\n")
            print(json.dumps(row))
            time.sleep(delay)
    print(f"receipt: {out_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)

    b = sub.add_parser("baseline", help="score assets/corpus.jsonl against labels")
    b.add_argument("--corpus", default=DEFAULT_CORPUS)
    b.add_argument("--delay", type=float, default=0.4)
    b.add_argument("--out", default=None)
    b.add_argument("--force", action="store_true")

    c = sub.add_parser("contexts", help="triage new contexts from a JSONL file")
    c.add_argument("file")
    c.add_argument("--delay", type=float, default=0.4)
    c.add_argument("--out", default=None)
    c.add_argument("--force", action="store_true")

    args = ap.parse_args()

    if not os.environ.get("TYPESAFE_API_KEY"):
        print("SKIP_REASON=TYPESAFE_API_KEY not set", file=sys.stderr)
        return 2

    print(
        f"threshold {AUTO_RESOLVE_THRESHOLD} is model-specific "
        "(measured on jev-latest); re-run baseline before trusting other models",
        file=sys.stderr,
    )
    if args.mode == "baseline":
        return run_baseline(args.corpus, args.delay, args.out, args.force)
    return run_contexts(args.file, args.delay, args.out, args.force)


if __name__ == "__main__":
    sys.exit(main())
