# here-now Skill

Static hosting skill for publishing files and folders to [here.now](https://here.now).
Forked from [heredotnow/skill](https://github.com/heredotnow/skill) with NanoClaw security hardening.

## Files

```
SKILL.md                  Agent-facing instructions
README.md                 This file
scripts/publish.sh        Bash implementation (requires curl + jq)
scripts/publish.py        Python implementation (zero dependencies)
references/REFERENCE.md   Full API reference
```

## Approach: Why publish.py?

### The problem

The upstream `publish.sh` depends on `curl` and `jq`. Different agent environments have different tooling available:

| Environment    | bash | curl | jq  | python3 |
|---------------|------|------|-----|---------|
| Hermes (Docker) | yes  | no   | no  | yes     |
| Claude Code      | yes  | yes  | yes | yes     |
| Cursor / Codex   | yes  | maybe| maybe| yes    |
| Bare containers  | yes  | maybe| no  | maybe   |

The only constant across all of them is **Python 3 stdlib**.

### The solution

`publish.py` reimplements the full publish.sh logic using only Python stdlib (`urllib`, `hashlib`, `json`, `os`, `re`, `mimetypes`):

- API calls via `urllib.request` (replaces curl)
- JSON handling natively (replaces jq)
- All 5 security layers ported 1:1
- File upload, create, finalize, metadata patch
- State management (`.herenow/state.json`)

### Why not other approaches?

**Per-arch bundled binaries (bin/jq)**
Only solves the jq dependency, not curl. Adds maintenance burden for binary tracking. Doesn't work across architectures without a download/selection layer.

**Auto-download jq on demand**
Creates a circular dependency: if curl is missing (the main scenario), you can't download jq without python3 urllib -- but if python3 is available, publish.py works directly. Adds network dependency at publish time.

**Patch publish.sh to use python3 for curl calls**
Frankenstein script mixing bash and python subprocess calls. Still needs jq for JSON. More fragile, harder to maintain.

**Git LFS for binaries**
Overkill. Adds repo configuration complexity for binaries that are unnecessary if we have a zero-dependency Python path.

### Runtime selection (agent-facing)

The SKILL.md instructs agents to use publish.py as the primary path:

1. `python3 scripts/publish.py <target>` -- works everywhere, zero dependencies
2. `scripts/publish.sh <target>` -- kept for environments with bash+curl+jq (fast path for humans)
3. Manual API calls via python3 urllib -- last resort

For agents specifically, the pre-req check for publish.sh costs extra tool calls and tokens. publish.py is the deterministic choice.

### What publish.py preserves from publish.sh

All NanoClaw security hardening:

| Layer | Description |
|-------|-------------|
| Dangerous extensions | Always blocked (.env, .pem, .key, etc.) |
| Suspicious extensions | Blocked unless `--allow-suspicious` (.bak, .tmp, no extension) |
| Unknown extensions | Blocked unless `--allow-unknown` (published as application/octet-stream) |
| Secret scanning | Pre-upload content scan for leaked credentials |
| Credential permissions | Warns if `~/.herenow/credentials` is world-readable |

Plus all publish.sh features: slug updates, claim tokens, TTL, viewer metadata, state persistence, client attribution.

## Changelog

### v2.0.0 — Python-native publisher

- Add `publish.py` — full reimplementation using Python 3 stdlib (urllib, hashlib, json)
- Drop `curl` and `jq` as dependencies
- Remove bundled `bin/jq` binary
- Deprecate `publish.sh` (kept for environments with bash+curl+jq)
- Update SKILL.md to recommend publish.py as primary path
- Add README.md

### v1.11.0 — NanoClaw hardening

- Block dangerous file types (.env, .pem, .key, etc.)
- Warn on suspicious types (.bak, .tmp, no extension)
- Pre-upload secret scanning for leaked credentials
- Credential file permission warnings
- Bundle `bin/jq` for zero-install environments

## Upstream

Based on [heredotnow/skill](https://github.com/heredotnow/skill/tree/main/here-now) v1.11.0.
