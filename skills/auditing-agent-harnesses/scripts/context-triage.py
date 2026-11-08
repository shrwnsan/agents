#!/usr/bin/env python3
"""Context-triage harness for auditing-agent-harnesses (TypeSafe System One API; measured on jev-latest).

Modes:
  baseline   Score assets/corpus.jsonl against its labels. Receipts
             default to the current working directory; refresh the pinned
             receipt with --out references/baseline-results.json --force
             (latest pin: jev-1.14.0, 2026-11-03).
  contexts   Triage new byte-window contexts from a JSONL file
             (rows: id, context, optional pipeline_shaped). A row without
             pipeline_shaped is treated as false with a stderr warning;
             set it on any context that packages, encrypts, or uploads
             user material. Emits one JSONL row per context: predicted
             label, confidence, gate decision.
  probe      One unauthenticated GET to the API root; any HTTP response
             proves egress. The key is never sent and is not required.

Confidence drifts run-to-run (measured 2026-11-02: 15/25 corpus items,
two crossing the 0.75 line without changing class). contexts re-scores
once when a confidence lands in the 0.70-0.80 confirm band and keeps
the lower-confidence answer; a re-score that returns a different class
escalates the context regardless of confidence. baseline --reps N uses
majority prediction with the median of its confidences.

Gating (advisory only — Jev never issues the audit verdict):
  auto-resolve  confidence >= 0.75, and for pipeline_shaped contexts only
                when the predicted class is pipeline-indicator
  escalate      everything else; a pipeline-shaped context read as any
                other class escalates regardless of confidence
                (false-clear is disqualifying)

The 0.75 threshold is model-specific (measured on jev-latest only) — re-run
`baseline` before trusting it on any other model or provider.

Output defaults to the current working directory with a timestamped name
(the documented deliverable location for skill scripts) and refuses to
overwrite; TRIAGE_OUT_DIR moves receipts elsewhere. A default path that
would land inside the skill directory relocates to TMPDIR with a stderr
note; an explicit --out inside the skill directory is refused. contexts
receipts are JSONL.

Usage:
  context-triage.py probe
  context-triage.py baseline [--corpus PATH] [--delay S] [--reps N] [--out PATH] [--force]
  context-triage.py contexts FILE [--delay S] [--confirm-band F] [--out PATH] [--force]

Env: TYPESAFE_API_KEY (required; presence-checked, never printed),
TYPESAFE_BASE_URL (gateway/compat override), TYPESAFE_MODEL (scored
model alias, default jev-latest).
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from statistics import median

API = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1/systemone")
HERE = os.path.dirname(os.path.realpath(__file__))  # resolve a symlinked invocation
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_CORPUS = os.path.join(SKILL_DIR, "assets", "corpus.jsonl")

MODEL = os.environ.get("TYPESAFE_MODEL", "jev-latest")
AUTO_RESOLVE_THRESHOLD = 0.75
CONFIRM_BAND = 0.05

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
        {"state": state, "model": MODEL, "questions": QUESTIONS}
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


def score_once(context: str, delay: float) -> tuple[str | None, float | None, str | None]:
    r = call_jev(context, delay)
    cls = r.get("answers", {}).get("classification", {})
    return cls.get("choice"), cls.get("confidence"), r.get("model")


def score_majority(context: str, delay: float, reps: int) -> tuple[str | None, float | None, str | None]:
    """Score reps times: majority prediction, median of its confidences,
    most-common resolved model. A prediction tie resolves to (None, None, ..),
    which gates to escalate."""
    samples = [score_once(context, delay) for _ in range(reps)]
    preds = [p for p, _, _ in samples]
    top = max(set(preds), key=preds.count)
    if preds.count(top) * 2 <= len(preds):
        return None, None, None
    confs = sorted(c for p, c, _ in samples if p == top and c is not None)
    models = [m for _, _, m in samples if m]
    resolved = max(set(models), key=models.count) if models else None
    return top, (median(confs) if confs else None), resolved


def run_probe() -> int:
    """One unauthenticated GET to the API root; any HTTP status proves
    egress (404s are normal for bare roots). The key is never sent."""
    root = API.split("/v1/", 1)[0]
    req = urllib.request.Request(root, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            print(f"reachable status={resp.status} url={root}")
        return 0
    except urllib.error.HTTPError as e:
        print(f"reachable status={e.code} url={root}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"blocked url={root} error={e}")
        return 3


def _inside_skill_dir(path: str) -> bool:
    real = os.path.realpath(path)
    return real == SKILL_DIR or real.startswith(SKILL_DIR + os.sep)


def open_out(path: str | None, kind: str, force: bool) -> str:
    """Resolve the output path: --out wins; default is CWD timestamped.
    Receipts never land inside the skill dir: a default path that would
    relocates to TMPDIR with a stderr note, an explicit --out is refused."""
    ext = ".jsonl" if kind == "triage-contexts" else ".json"
    if path is None:
        name = f"{kind}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{ext}"
        path = os.path.abspath(
            os.path.join(os.environ.get("TRIAGE_OUT_DIR", os.getcwd()), name)
        )
        if _inside_skill_dir(path):
            path = os.path.join(os.environ.get("TMPDIR", "/tmp"), name)
            print(f"note: default receipt path is inside the skill directory; "
                  f"writing {path}", file=sys.stderr)
    else:
        path = os.path.abspath(path)
        if _inside_skill_dir(path):
            sys.exit(f"refusing to write inside the skill directory: {path}")
    if os.path.exists(path) and not force:
        sys.exit(f"output exists: {path} (--force to overwrite)")
    return path


def gate(predicted: str | None, confidence: float | None, pipeline_shaped: bool) -> str:
    if pipeline_shaped and predicted != "pipeline-indicator":
        return "escalate"  # a non-pipeline read of a pipeline-shaped context is disqualifying
    if confidence is None or confidence < AUTO_RESOLVE_THRESHOLD:
        return "escalate"
    return "auto-resolve"


def load_jsonl(path: str, required: tuple[str, ...]) -> list[dict]:
    rows = []
    try:
        f = open(path)
    except OSError as e:
        sys.exit(f"{path}: cannot open input: {e.strerror}")
    with f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                sys.exit(f"{path}: invalid JSON on line {n}: {e.msg}")
            if not isinstance(row, dict):
                sys.exit(f"{path}: line {n}: expected a JSON object, got {type(row).__name__}")
            for field in required:
                if field not in row:
                    sys.exit(f"{path}: line {n}: missing required field {field!r}")
            rows.append(row)
    return rows


def warn_unflagged(rows: list[dict], ours: str) -> None:
    unflagged = [r["id"] for r in rows if ours(r)]
    if unflagged:
        names = ", ".join(str(i) for i in unflagged[:5])
        print(f"warning: {len(unflagged)} row(s) lack pipeline_shaped and the gate "
              f"treats them as false: {names}{' ...' if len(unflagged) > 5 else ''}",
              file=sys.stderr)


def run_baseline(corpus_path: str, delay: float, reps: int, out: str | None, force: bool) -> int:
    corpus = load_jsonl(corpus_path, ("id", "label", "context"))
    if not corpus:
        sys.exit(f"{corpus_path}: 0 corpus items; nothing to score")
    # Unflagged pipeline positives are the mislabeled-corpus hazard: the
    # broadened gate cannot see them (2026-11-09: the 7 synthetic positives).
    warn_unflagged(corpus, lambda s: s["label"] == "pipeline-indicator"
                 and "pipeline_shaped" not in s)

    rows = []
    for s in corpus:
        try:
            predicted, confidence, resolved = score_majority(s["context"], delay, reps)
            rows.append({
                "id": s["id"],
                "label": s["label"],
                "predicted": predicted,
                "confidence": confidence,
                "pipeline_shaped": s.get("pipeline_shaped", False),
                "gate": gate(predicted, confidence, s.get("pipeline_shaped", False)),
                "model": resolved,
                "reps": reps,
            })
        except Exception as e:  # noqa: BLE001 — record and continue
            rows.append({"id": s.get("id", "<missing>"), "label": s.get("label", "<missing>"),
                         "error": str(e)})
        time.sleep(delay)

    out_path = open_out(out, "triage-baseline", force)
    with open(out_path, "w") as f:
        json.dump(
            {
                "generated": datetime.now().isoformat(timespec="seconds"),
                "summary": summarize_baseline(rows),
                "rows": rows,
            },
            f,
            indent=2,
        )
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
    pipeline_missed = [
        r for r in labeled
        if r.get("pipeline_shaped") and r.get("predicted") != "pipeline-indicator"
    ]
    return {
        "total": len(rows),
        "scored": n,
        "errors": len(rows) - n,
        "accuracy": round(len(correct) / n, 3) if n else 0.0,
        "mean_confidence_correct": round(sum(conf_ok) / len(conf_ok), 3) if conf_ok else None,
        "mean_confidence_wrong": round(sum(conf_bad) / len(conf_bad), 3) if conf_bad else None,
        "pipeline_false_clears": len(pipeline_benign),
        "pipeline_shaped_missed": len(pipeline_missed),
        "misclassified": [
            {"id": r["id"], "label": r["label"], "predicted": r.get("predicted"),
             "confidence": r.get("confidence")}
            for r in labeled if r.get("predicted") != r["label"]
        ],
    }


def run_contexts(path: str, delay: float, confirm_band: float, out: str | None, force: bool) -> int:
    contexts = load_jsonl(path, ("id", "context"))
    if not contexts:
        sys.exit(f"{path}: 0 contexts in input; nothing to triage")
    warn_unflagged(contexts, lambda c: "pipeline_shaped" not in c)

    out_path = open_out(out, "triage-contexts", force)
    with open(out_path, "w") as f:
        for c in contexts:
            try:
                predicted, confidence, model = score_once(c["context"], delay)
                rerun = False
                class_flip = False
                if (confirm_band > 0 and predicted is not None and confidence is not None
                        and AUTO_RESOLVE_THRESHOLD - confirm_band
                        <= confidence < AUTO_RESOLVE_THRESHOLD + confirm_band):
                    p2, c2, m2 = score_once(c["context"], delay)
                    if p2 != predicted:
                        class_flip = True  # instability in the band is disqualifying
                    if c2 is not None and (confidence is None or c2 < confidence):
                        predicted, confidence, model = p2, c2, m2
                    rerun = True
                ps = c.get("pipeline_shaped", False)
                row = {
                    "id": c["id"],
                    "predicted": predicted,
                    "confidence": confidence,
                    "pipeline_shaped": ps,
                    "gate": "escalate" if class_flip else gate(predicted, confidence, ps),
                    "model": model,
                }
                if rerun:
                    row["confirm_rerun"] = True
                if class_flip:
                    row["confirm_class_flip"] = True
            except Exception as e:  # noqa: BLE001
                row = {"id": c.get("id", "<missing>"), "error": str(e)}
            f.write(json.dumps(row) + "\n")
            print(json.dumps(row))
            time.sleep(delay)
    print(f"receipt: {out_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("probe", help="egress reachability check (one unauthenticated GET)")

    b = sub.add_parser("baseline", help="score assets/corpus.jsonl against labels")
    b.add_argument("--corpus", default=DEFAULT_CORPUS)
    b.add_argument("--delay", type=float, default=0.4)
    b.add_argument("--reps", type=int, default=1)
    b.add_argument("--out", default=None)
    b.add_argument("--force", action="store_true")

    c = sub.add_parser("contexts", help="triage new contexts from a JSONL file")
    c.add_argument("file")
    c.add_argument("--delay", type=float, default=0.4)
    c.add_argument("--confirm-band", type=float, default=CONFIRM_BAND, dest="confirm_band")
    c.add_argument("--out", default=None)
    c.add_argument("--force", action="store_true")

    args = ap.parse_args()

    if args.mode == "probe":
        return run_probe()

    if not os.environ.get("TYPESAFE_API_KEY"):
        print("SKIP_REASON=TYPESAFE_API_KEY not set", file=sys.stderr)
        return 2
    if args.mode == "baseline" and args.reps < 1:
        sys.exit("--reps must be >= 1")

    print(
        f"threshold {AUTO_RESOLVE_THRESHOLD} is model-specific "
        "(measured on jev-latest); re-run baseline before trusting other models",
        file=sys.stderr,
    )
    if args.mode == "baseline":
        return run_baseline(args.corpus, args.delay, args.reps, args.out, args.force)
    return run_contexts(args.file, args.delay, args.confirm_band, args.out, args.force)


if __name__ == "__main__":
    sys.exit(main())
