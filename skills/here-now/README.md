# here-now Skill

Static hosting skill for publishing files and folders to [here.now](https://here.now).
Forked from [heredotnow/skill](https://github.com/heredotnow/skill) with NanoClaw security hardening.

## Files

```
SKILL.md                  Agent-facing instructions
README.md                 This file
scripts/publish.sh        Thin wrapper — execs publish.py (human entrypoint)
scripts/publish.py        Python implementation (zero dependencies)
references/REFERENCE.md   Full API reference
```

## Approach: Why publish.py?

### The problem

The upstream `publish.sh` depends on `curl` and `jq`. Different agent environments have different tooling available:

| Environment                | bash | curl | jq  | python3 |
|----------------------------|------|------|-----|---------|
| Hermes (Docker)            | yes  | no   | no  | yes     |
| Claude Code (macOS host)   | yes  | yes  | yes | yes (pyenv + /usr/bin) |
| Bare: debian bookworm-slim | yes  | no   | no  | no      |
| Bare: ubuntu 24.04         | yes  | no   | no  | no      |
| Bare: alpine 3.20          | no   | no   | no  | no      |
| python:3.12-slim           | yes  | no   | no  | yes     |
| node:22-slim               | yes  | no   | no  | no      |

Container rows measured 2026-09-09 via `docker run` (linux/arm64); Hermes row retained
from upstream docs. Takeaway: no tested environment can run the old bash+curl+jq script
anywhere publish.py cannot — bare images without python3 also lack curl/jq (and alpine
lacks bash outright), so a standalone bash implementation has no remaining niche.

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
2. `scripts/publish.sh <target>` -- thin wrapper that execs publish.py (human-friendly entrypoint)
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

### v2.1.0 — Single implementation

- Replace the bash `publish.sh` with a thin wrapper that execs `publish.py`
- All flags pass through; `--spa` and `--password` now work via the wrapper too
- Closes a latent defect class: the bash script had carried stripped-comment
  corruption since `ecdd4e4` (10 bare lines, fatal under `set -euo pipefail`),
  plus a subshell-scoped upload-error counter and a GNU-only `stat -c` perms check
- Re-measure the environment matrix against real 2026-09 container images —
  no environment where the bash path ran lacks python3

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
