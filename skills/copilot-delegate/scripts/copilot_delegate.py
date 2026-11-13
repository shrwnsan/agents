#!/usr/bin/env python3
"""Delegate one bounded task to the GitHub Copilot CLI under a fixed contract.

Subcommands:
  check   Preflight: CLI present, version, auth state, ledger writable.
  run     One delegation: prompt -> JSON answer -> optional caller check -> ledger.
  report  Summarize the ledger (calls/day, models, outcomes).

Stdlib only. The script never talks to the network itself; the pinned copilot
binary does. It never passes --share, --share-gist, or --enable-memory, and it
passes --allow-all-tools only when the operator says --need-tools.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

JSON_CONTRACT = (
    "\n\nOutput contract: end your reply with one fenced code block containing "
    "a single JSON object and nothing else in that block: "
    '{"answer": "<the deliverable>", "assumptions": ["<each assumption you '
    'made>"], "confidence": "low"|"medium"|"high"}. No text after the block.'
)
JSON_RETRY_SUFFIX = (
    "\n\nYour previous reply broke the output contract. End the reply with "
    "one fenced JSON object matching the contract—no prose after it."
)

FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_-]*)\s*\n(.*?)```", re.DOTALL)
RATE_HINTS = ("rate limit", "rate_limit", "quota", "429", "premium request",
              "billing", "exceeded")
NEVER_FLAGS = ("--share", "--share-gist", "--enable-memory")


def state_dir() -> Path:
    """Runtime state home: ledger and failed-reply dumps.

    XDG_STATE_HOME if set (default ~/.local/state), overridable wholesale
    with COPILOT_DELEGATE_STATE_DIR for tests and exotic setups.
    """
    override = os.environ.get("COPILOT_DELEGATE_STATE_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "state"
    return base / "copilot-delegate"


def cache_dir() -> Path:
    """Recomputable cache home: the auth-probe timestamp lives here."""
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "copilot-delegate"


def legacy_state_dir() -> Path:
    """Pre-1.1.1 location under ~/.config; migrated once, then ignored."""
    override = os.environ.get("COPILOT_DELEGATE_LEGACY_DIR")
    if override:
        return Path(override)
    return Path.home() / ".config" / "copilot-delegate"


def migrate_legacy_state() -> None:
    """Move ledger, failed replies, and probe cache out of ~/.config."""
    legacy = legacy_state_dir()
    target = state_dir()
    if not legacy.is_dir() or target.exists():
        return
    try:
        target.mkdir(parents=True, exist_ok=True)
        for item in sorted(legacy.iterdir()):
            dest = target / item.name
            if not dest.exists():
                os.replace(item, dest)
        legacy.rmdir()
        print(f"note: migrated state from {legacy} to {target}",
              file=sys.stderr)
    except OSError:
        pass  # fall back to reading the legacy location in place


def ledger_path() -> Path:
    override = os.environ.get("COPILOT_DELEGATE_LEDGER")
    if override:
        return Path(override)
    migrate_legacy_state()
    return state_dir() / "ledger.jsonl"


def ledger_append(entry: dict) -> None:
    path = ledger_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except OSError as exc:
        print(f"warning: ledger write failed ({exc}); burn happened anyway",
              file=sys.stderr)


def failed_output_path(label: str, stage: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-") or "run"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return state_dir() / "failed" / f"{stamp}-{safe}-{stage}.txt"


def save_failure(label: str, stage: str, output: str) -> str:
    """Keep the raw delegate reply from a failed attempt; return the path."""
    path = failed_output_path(label, stage)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        return str(path)
    except OSError as exc:
        print(f"warning: could not write failed reply to {path} ({exc})",
              file=sys.stderr)
        return ""


def guarded_tail(output: str, limit: int = 400) -> str:
    """Quote the end of a failed reply back to the model, minus flag names."""
    tail = output.strip()[-limit:]
    for flag in NEVER_FLAGS:
        tail = tail.replace(flag, "[redacted]")
    if not tail:
        return ""
    return "\n\nFor reference, your previous output ended with:\n" + tail


def auth_cache_path() -> Path:
    return cache_dir() / "auth-probe.json"


def copilot_bin() -> str | None:
    override = os.environ.get("COPILOT_BIN")
    if override:
        return override if Path(override).is_file() else None
    return shutil.which("copilot")


def extract_json(text: str) -> dict | None:
    matches = FENCE_RE.findall(text)
    for block in reversed(matches):
        try:
            obj = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("answer"), str):
            continue
        assumptions = obj.get("assumptions", [])
        if not isinstance(assumptions, list):
            continue
        if obj.get("confidence") not in ("low", "medium", "high"):
            continue
        return {"answer": obj["answer"], "assumptions": assumptions,
                "confidence": obj["confidence"]}
    return None


def run_copilot(base: list[str], prompt: str, timeout: int) -> tuple[int, str]:
    argv = base + ["-p", prompt + JSON_CONTRACT, "-s",
                   "--disable-client-telemetry"]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        return 5, ""
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return proc.returncode, output


def looks_like_quota(output: str) -> bool:
    low = output.lower()
    return any(hint in low for hint in RATE_HINTS)


def run_check(command: str, cwd: str | None, timeout: int,
              answer: str) -> tuple[bool, str]:
    env = dict(os.environ)
    env["COPILOT_DELEGATE_ANSWER"] = answer
    try:
        proc = subprocess.run(shlex.split(command), capture_output=True,
                              text=True, timeout=timeout, cwd=cwd, env=env)
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return False, f"check-command itself failed: {exc}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output[-800:]


def build_base(args) -> list[str]:
    binary = args.copilot or copilot_bin()
    if not binary:
        print("FAIL: copilot CLI not found (set COPILOT_BIN, or install via "
              "npm / 'brew install --cask copilot-cli' / the gh.io install "
              "script — see SKILL.md Preflight)", file=sys.stderr)
        raise SystemExit(2)
    base = [binary]
    if args.cwd:
        base += ["-C", args.cwd]
    if args.model:
        base += ["--model", args.model]
    if args.need_tools:
        base += ["--allow-all-tools"]
    return base


def cmd_run(args) -> int:
    prompt = args.prompt
    if args.context_file:
        try:
            context = Path(args.context_file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL: cannot read --context-file: {exc}", file=sys.stderr)
            return 6
        prompt = ("Context (authoritative for this task; answer only from "
                  f"it):\n\n{context}\n\nTask:\n{args.prompt}")
    for forbidden in NEVER_FLAGS:
        if forbidden in prompt:
            print(f"refusing: prompt text mentions {forbidden}; the wrapper "
                  "never constructs it", file=sys.stderr)
            return 6
    base = build_base(args)
    label = args.task_label
    attempts: list[dict] = []

    def attempt(prompt: str, note: str) -> tuple[int, dict | None, str]:
        start = time.monotonic()
        code, output = run_copilot(base, prompt, args.timeout)
        seconds = round(time.monotonic() - start, 1)
        parsed = extract_json(output) if code == 0 else None
        if code == 5:
            outcome = "timeout"
        elif code != 0:
            outcome = "cli_error"
        elif parsed is None:
            outcome = "contract_fail"
        else:
            outcome = "parsed"
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "label": label, "model": args.model or "cli-default",
                 "seconds": seconds, "exit": code, "check": note,
                 "outcome": outcome}
        attempts.append(entry)
        ledger_append(entry)
        return code, parsed, output

    code, parsed, output = attempt(prompt, "parse")
    if code == 5:
        print("timeout; raise --timeout only if the task is genuinely long",
              file=sys.stderr)
        return 5
    if code != 0:
        if looks_like_quota(output):
            print("quota or rate limiting detected; stop, do not retry",
                  file=sys.stderr)
            return 4
        tail = "\n".join(output.strip().splitlines()[-5:])
        print(f"copilot exited {code}:\n{tail}", file=sys.stderr)
        return 6
    if parsed is None:
        where = save_failure(label, "parse", output)
        hint = f"raw reply saved to {where}\n" if where else ""
        print(f"{hint}output contract failed; retrying under a stricter "
              "instruction", file=sys.stderr)
        code, parsed, output = attempt(
            prompt + JSON_RETRY_SUFFIX + guarded_tail(output), "parse-retry")
        if code == 5:
            return 5
        if code != 0:
            return 4 if looks_like_quota(output) else 6
        if parsed is None:
            where = save_failure(label, "parse-retry", output)
            hint = f"raw reply saved to {where}\n" if where else ""
            print(f"{hint}output contract failed twice; do the task locally",
                  file=sys.stderr)
            return 3

    if not args.check_command:
        print(json.dumps(parsed, indent=2))
        return 0

    ok, tail = run_check(args.check_command, args.cwd, args.timeout,
                         str(parsed.get("answer", "")))
    if ok:
        parsed["check"] = "passed"
        print(json.dumps(parsed, indent=2))
        return 0
    save_failure(label, "check", str(parsed.get("answer", "")))

    followup = (prompt + "\n\nYour answer failed this verification:\n"
                f"{tail}\nFix the deliverable and reply under the same "
                "output contract.")
    code, parsed2, output = attempt(followup, "check-retry")
    if code == 5:
        return 5
    if code != 0:
        return 4 if looks_like_quota(output) else 6
    if parsed2 is None:
        where = save_failure(label, "check-retry", output)
        hint = f" raw reply saved to {where}." if where else ""
        print(f"retry broke the output contract; do the task locally.{hint}",
              file=sys.stderr)
        return 3
    ok, tail = run_check(args.check_command, args.cwd, args.timeout,
                         str(parsed2.get("answer", "")))
    if ok:
        parsed2["check"] = "passed"
        print(json.dumps(parsed2, indent=2))
        return 0
    save_failure(label, "check-retry", str(parsed2.get("answer", "")))
    print("caller check failed twice; do the task locally\n" + tail,
          file=sys.stderr)
    return 3


def cmd_check(args) -> int:
    problems = 0
    binary = copilot_bin()
    if not binary:
        print("FAIL: copilot CLI not found (set COPILOT_BIN, or install via "
              "npm / 'brew install --cask copilot-cli' / the gh.io install "
              "script — see SKILL.md Preflight)")
        return 2
    print(f"OK: CLI at {binary}")
    try:
        proc = subprocess.run([binary, "--version"], capture_output=True,
                              text=True, timeout=30)
        version_text = (proc.stdout or "") + (proc.stderr or "")
        lines = [line for line in version_text.strip().splitlines()
                 if line.strip()]
        print(f"OK: version output: {lines[-1] if lines else '(empty)'}")
        match = re.search(r"(\d+\.\d+\.\d+)", version_text)
        if match:
            print(f"OK: detected version {match.group(1)}")
            if args.expect_version and args.expect_version != match.group(1):
                print(f"FAIL: --expect-version {args.expect_version} does not "
                      f"match detected {match.group(1)}")
                problems = 1
        else:
            print("note: no semantic version found in the version output")
            if args.expect_version:
                print(f"FAIL: no version detected to compare against "
                      f"--expect-version {args.expect_version}")
                problems = 1
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"WARN: could not read version ({exc})")
        problems = 1
    skip_probe = False
    if not args.fresh:
        try:
            cached = json.loads(auth_cache_path().read_text(encoding="utf-8"))
            age = time.time() - float(cached["ts"])
            if 0 <= age < 3600 and cached.get("ok"):
                print(f"OK: authenticated (cached {int(age // 60)} min ago; "
                      "pass --fresh to re-probe)")
                skip_probe = True
        except (OSError, ValueError, KeyError):
            pass
    if not skip_probe:
        auth = subprocess.run([binary, "-p", "Reply with the word OK.", "-s",
                               "--disable-client-telemetry"],
                              capture_output=True, text=True, timeout=90)
        if auth.returncode == 0:
            print("OK: authenticated (a real call was answered—this burned one "
                  "premium request)")
            try:
                cache = auth_cache_path()
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps({"ts": time.time(), "ok": True}),
                                 encoding="utf-8")
            except OSError as exc:
                print(f"note: auth cache write skipped ({exc})")
        else:
            low = ((auth.stdout or "") + (auth.stderr or "")).lower()
            if any(h in low for h in RATE_HINTS):
                print("WARN: authenticated but quota or rate limiting hit")
            else:
                print("WARN: not authenticated or call failed; run `copilot` "
                      "once interactively to complete the device flow")
                problems = 1
    path = ledger_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        print(f"OK: ledger writable at {path}")
    except OSError as exc:
        print(f"WARN: ledger not writable ({exc}); set COPILOT_DELEGATE_LEDGER")
    return 0 if problems == 0 else 1


def cmd_report(args) -> int:
    path = ledger_path()
    if not path.is_file():
        print(f"no ledger at {path}")
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if datetime.fromisoformat(row["ts"]) >= cutoff:
                rows.append(row)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    if not rows:
        print(f"no calls in the last {args.days} days")
        return 0
    per_day: dict[str, int] = {}
    models: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    for row in rows:
        per_day[row["ts"][:10]] = per_day.get(row["ts"][:10], 0) + 1
        models[row["model"]] = models.get(row["model"], 0) + 1
        outcome = row.get("outcome")
        if outcome is None:
            outcome = ("used" if row.get("exit") == 0 else
                       "fallback" if row.get("exit") == 3 else
                       "timeout" if row.get("exit") == 5 else "error")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    total = len(rows)
    print(f"calls: {total} in {args.days} days "
          f"({total / args.days:.1f}/day)")
    for name, count in sorted(models.items(), key=lambda kv: -kv[1]):
        print(f"  model {name}: {count}")
    for name, count in sorted(outcomes.items()):
        print(f"  {name}: {count}")
    for day in sorted(per_day):
        print(f"  {day}: {per_day[day]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    chk = sub.add_parser("check", help="preflight: CLI, version, auth, ledger")
    chk.add_argument("--fresh", action="store_true",
                     help="re-probe auth even if a recent probe passed")
    chk.add_argument("--expect-version",
                     help="fail if the detected CLI version differs")
    chk.set_defaults(func=cmd_check)

    run = sub.add_parser("run", help="run one delegation")
    run.add_argument("prompt")
    run.add_argument("--task-label", required=True,
                     help="short name for the ledger row")
    run.add_argument("--model", help="exact model string from the plan catalog")
    run.add_argument("--timeout", type=int, default=300,
                     help="seconds for the copilot call and the check")
    run.add_argument("--context-file",
                     help="file whose contents are prepended to the prompt "
                          "as authoritative context")
    run.add_argument("--check-command",
                     help="verification to run on the answer (shlex-split, "
                          "no shell)")
    run.add_argument("--cwd", help="working directory (forwarded as -C)")
    run.add_argument("--need-tools", action="store_true",
                     help="forward --allow-all-tools; pair with sandboxed-run")
    run.add_argument("--copilot", help="copilot binary path "
                     "(default: COPILOT_BIN or PATH)")
    run.set_defaults(func=cmd_run)

    rep = sub.add_parser("report", help="summarize the ledger")
    rep.add_argument("--days", type=int, default=7)
    rep.set_defaults(func=cmd_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
