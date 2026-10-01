#!/usr/bin/env python3
"""lab.py — shared model-access layer for the model-bakeoff-gate harness.

One uniform contract behind up to three configured providers, resolved by
which keys are present in the environment (first match wins):

  TYPESAFE_API_KEY   -> TypeSafe direct (Jev System One, model "jev-latest")
  AI_GATEWAY_API_KEY -> Vercel AI Gateway, OpenAI-compatible endpoint
  OPENROUTER_API_KEY -> OpenRouter, OpenAI-compatible endpoint

Design rules (these are the point of the file):
  * Fail closed, never fail silent: with no keys at all, make_jev_client()
    raises SystemExit — callers catch it and degrade to deterministic-only
    behavior. A caller that forgets to catch SystemExit still fails loudly.
  * Every provider speaks the same /v1/systemone contract, so ask() works
    identically on all legs and results are directly comparable.
  * No third-party deps for the OpenAI-compatible legs — stdlib urllib only.
  * Env hygiene: values read from the environment are stripped of ANSI
    escapes (copy-pasted slugs often carry invisible escape codes that
    surface as "Unknown Model" 400s).

Usage:
    from lab import ask, make_jev_client, make_byok_legs, ...
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

# ================================================================ env utils ==

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


def _clean(value: str) -> str:
    """Strip ANSI escape sequences an OS shell may have baked into env values."""
    return _ANSI_RE.sub("", value).strip()


def _env(name: str) -> str | None:
    """Read a non-empty, escape-stripped env value, or None."""
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        return None
    return _clean(raw)


# =========================================================== systemone core ==

_SYSTEMONE_TIMEOUT_S = 60.0


def _post_systemone(key: str, base_url: str, provider: str, payload: dict) -> dict:
    """POST one /v1/systemone request. Raises RuntimeError with the response
    body on non-200 (so callers see the provider's actual error message)."""
    url = f"{base_url.rstrip('/')}/v1/systemone"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_SYSTEMONE_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = "<no body>"
        raise RuntimeError(f"systemone HTTP {e.code} from {provider}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"systemone connection error ({provider}): {e.reason}") from e


def _jev_payload(model: str, state: str, questions: dict) -> dict:
    """Build the wire payload. SDK objects use .to_payload() (or plain dicts
    pass through), which keeps this stdlib-only."""
    q_payload = {}
    for name, q in questions.items():
        if hasattr(q, "to_payload"):
            q_payload[name] = q.to_payload()
        elif isinstance(q, dict):
            q_payload[name] = q
        else:
            raise TypeError(f"question {name!r}: expected SDK question or dict, got {type(q).__name__}")
    return {"model": model, "state": state, "questions": q_payload}


def _parse_answers(data: dict) -> dict:
    """Normalize provider answers into the shape the harness reads:
    answers.<name> = {choice, confidence, probabilities} for Choice,
    {score} for Score, {noul} for Noul. Pass through unknown shapes."""
    out = {}
    for name, a in (data.get("answers") or {}).items():
        if not isinstance(a, dict):
            out[name] = a
            continue
        entry: dict = {}
        if "choice" in a:
            entry["choice"] = a["choice"]
        if "confidence" in a:
            entry["confidence"] = a["confidence"]
        if "probabilities" in a:
            entry["probabilities"] = a["probabilities"]
        if "score" in a:
            entry["score"] = a["score"]
        if "noul" in a:
            entry["noul"] = a["noul"]
        out[name] = entry or a
    return out


def _parse_usage(data: dict) -> dict | None:
    u = data.get("usage")
    return u if isinstance(u, dict) else None


class _JevResult:
    """What ask() returns. Attributes mirror the typesafe-sdk result object
    (leg, latency_ms, usage, answers) so the harness code is unchanged."""

    def __init__(self, answers: dict, usage: dict | None, latency_ms: float, leg: str):
        self.answers = answers
        self.usage = usage
        self.latency_ms = latency_ms
        self.leg = leg


def ask(client: dict, questions: dict, state: str, adapter_model: str | None = None) -> _JevResult:
    """Ask one configured leg. `client` is the dict returned by the
    make_*_client() factories: {"key", "base_url", "provider", "model"}.
    adapter_model overrides the client's model (used by eval baselines).
    Raises RuntimeError on provider error — callers in the harness catch
    per-leg and print [skip]; guard.py catches and exits EXIT_FAILSAFE."""
    model = adapter_model or client["model"]
    payload = _jev_payload(model, state, questions)
    t0 = time.monotonic()
    data = _post_systemone(client["key"], client["base_url"], client["provider"], payload)
    latency_ms = (time.monotonic() - t0) * 1000.0
    return _JevResult(
        answers=_parse_answers(data),
        usage=_parse_usage(data),
        latency_ms=latency_ms,
        leg=client["provider"],
    )


# ================================================================ factories ==

_JEV_MODEL = "jev-latest"  # rolling stable alias per GET /v1/models (jev-1.13 is not a direct-API slug)


def make_jev_client() -> dict:
    """Resolve the first available provider in key-precedence order and return
    its client dict. Raises SystemExit when no key is configured — the harness
    contract: catch it, degrade the leg, keep the deterministic layer running.
    Order: TYPESAFE_API_KEY -> AI_GATEWAY_API_KEY -> OPENROUTER_API_KEY."""
    order = (
        ("TYPESAFE_API_KEY", "https://api.typesafe.ai", "typesafe", _JEV_MODEL),
        ("AI_GATEWAY_API_KEY", "https://api.vercel.com", "gateway", _JEV_MODEL),
        ("OPENROUTER_API_KEY", "https://openrouter.ai/api", "openrouter", _JEV_MODEL),
    )
    for key_name, base_url, provider, model in order:
        key = _env(key_name)
        if key:
            return {"key": key, "base_url": base_url, "provider": provider, "model": model}
    raise SystemExit(
        "no model-access key found; expected one of "
        "TYPESAFE_API_KEY, AI_GATEWAY_API_KEY, OPENROUTER_API_KEY"
    )


def make_gateway_llm_client(model: str) -> tuple[dict, str]:
    """Gateway LLM baseline leg (e.g. 'openai/gpt-4o-mini'). Raises SystemExit
    when AI_GATEWAY_API_KEY is absent — same contract as make_jev_client."""
    key = _env("AI_GATEWAY_API_KEY")
    if not key:
        raise SystemExit("AI_GATEWAY_API_KEY not set — gateway LLM baseline unavailable")
    return ({"key": key, "base_url": "https://api.vercel.com", "provider": "gateway", "model": model}, model)


def _byok(base_url_env: str, model_env: str, key_env: str, label: str):
    """One BYOK leg (OpenAI-compatible direct provider), or None if any of the
    three env vars is unset. Values are ANSI-escape-stripped (see known gotcha)."""
    base_url, model, key = _env(base_url_env), _env(model_env), _env(key_env)
    if not (base_url and model and key):
        return None
    return (label, {"key": key, "base_url": base_url, "provider": label, "model": model}, model)


def make_byok_legs() -> list:
    """Optional BYOK direct-provider legs (LOCAL MACHINES ONLY — not CI).
    Returns [] when no BYOK triple is configured."""
    legs = []
    leg = _byok("ZAI_BASE_URL_OPENAI", "ZAI_MODEL", "ZAI_API_KEY", "byok:zai")
    if leg:
        legs.append(leg)
    return legs


# ============================================================= eval helpers ==

_JEV_CHOICE = {
    "type": "choice",
    "instructions": (
        "You are the decision gate. Read the state and return the single "
        "best choice with your calibrated confidence."
    ),
    "criteria": {
        "auto_merge": "Change is safe to proceed without human review",
        "human_review": "Anything ambiguous, risky, or outside stated policy",
    },
}


def pr_gate_questions() -> dict:
    """Questions for the pr-gate eval (see run_evals.py). Return the same
    dict-shape the SDK questions serialize to, so all legs are comparable."""
    return {"gate": dict(_JEV_CHOICE)}


def worktree_guard_questions() -> dict:
    """Questions for the worktree-guard eval (see run_evals.py)."""
    return {
        "gate": {
            "type": "choice",
            "instructions": (
                "A git branch is a candidate for deletion. The state reports "
                "merge topology (ahead/behind, patch-equivalent vs unique "
                "commits) and worktree cleanliness. Decide whether deletion is safe."
            ),
            "criteria": {
                "safe_delete": "No unique unmerged work and nothing ambiguous remains",
                "keep_review": "Unique unmerged work exists, or signals are ambiguous",
            },
        },
        "has_unique_work": {"type": "noul", "instructions": "Author work exists that exists nowhere else"},
        "data_loss_risk": {
            "type": "score",
            "instructions": "How much unrecoverable work would deletion lose?",
            "criteria": ["None", "Minor", "Real"],
        },
    }
