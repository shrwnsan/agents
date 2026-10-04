#!/usr/bin/env python3
"""Context-triage baseline harness for auditing-agent-harnesses (System One API; measured on jev-latest).

Reads corpus.jsonl (labeled binary-audit byte-window excerpts), sends each
context to the TypeSafe System One API as `state`, and scores Jev's
classification against the audit labels.

Prereq: TYPESAFE_API_KEY in env. No corpus context contains secret values
(code fragments, endpoint names, and a public-by-design Sentry DSN only).

Usage: python3 run.py [--delay 0.4] [--out results.json]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Override via TYPESAFE_BASE_URL to point at a gateway or future compat endpoint
API = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1/systemone")
HERE = os.path.dirname(os.path.abspath(__file__))

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=0.4)
    ap.add_argument("--out", default=os.path.join(HERE, "results.json"))
    args = ap.parse_args()

    if not os.environ.get("TYPESAFE_API_KEY"):
        print("SKIP_REASON=TYPESAFE_API_KEY not set", file=sys.stderr)
        return 2

    with open(os.path.join(HERE, "corpus.jsonl")) as f:
        corpus = [json.loads(line) for line in f if line.strip()]

    rows, errors = [], []
    for s in corpus:
        try:
            r = call_jev(s["context"], args.delay)
            ans = r.get("answers", {})
            cls = ans.get("classification", {})
            row = {
                "id": s["id"],
                "label": s["label"],
                "synthetic": s["synthetic"],
                "predicted": cls.get("choice"),
                "confidence": cls.get("confidence"),
                "probabilities": cls.get("probabilities"),
                "upload_risk": ans.get("upload_risk", {}).get("noul"),
                "model": r.get("model"),
                "usage": r.get("usage"),
            }
        except Exception as e:  # noqa: BLE001 — record and continue
            row = {"id": s["id"], "label": s["label"], "error": str(e)}
            errors.append(row)
        rows.append(row)
        time.sleep(args.delay)

    correct = [
        r for r in rows
        if r.get("predicted") == r["label"]
    ]
    labeled = [r for r in rows if "error" not in r]
    n = len(labeled)
    acc = len(correct) / n if n else 0.0
    conf_ok = [r["confidence"] for r in correct if r.get("confidence") is not None]
    conf_bad = [
        r["confidence"] for r in labeled
        if r.get("predicted") != r["label"] and r.get("confidence") is not None
    ]
    synthetic = [r for r in labeled if r["synthetic"]]
    verbatim = [r for r in labeled if not r["synthetic"]]
    syn_acc = (
        sum(1 for r in synthetic if r.get("predicted") == r["label"]) / len(synthetic)
        if synthetic else None
    )
    verb_acc = (
        sum(1 for r in verbatim if r.get("predicted") == r["label"]) / len(verbatim)
        if verbatim else None
    )

    summary = {
        "total": len(corpus),
        "scored": n,
        "errors": len(errors),
        "accuracy": round(acc, 3),
        "accuracy_verbatim": round(verb_acc, 3) if verb_acc is not None else None,
        "accuracy_synthetic": round(syn_acc, 3) if syn_acc is not None else None,
        "mean_confidence_correct": round(sum(conf_ok) / len(conf_ok), 3) if conf_ok else None,
        "mean_confidence_wrong": round(sum(conf_bad) / len(conf_bad), 3) if conf_bad else None,
        "miscover": [
            {"id": r["id"], "label": r["label"], "predicted": r.get("predicted"),
             "confidence": r.get("confidence")}
            for r in labeled if r.get("predicted") != r["label"]
        ],
    }
    with open(args.out, "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
