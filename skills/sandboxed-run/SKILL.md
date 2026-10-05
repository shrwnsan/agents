---
name: sandboxed-run
license: Apache-2.0
description: >-
  Use when about to run code you don't fully trust with your files, tokens, or
  git history — recipe scripts, third-party skill scripts, vendored samples,
  evals, a stranger's repo — or when repo conventions route untrusted code
  through sandboxed-run.
user-invocable: true
---

# Sandboxed Run

## Overview

One command puts a run behind three quarantines, then tears them down:

1. **Packages** — a fresh venv per run; pip installs die with the run instead of landing in a shared interpreter.
2. **Git and files** — the code under test is staged into a throwaway clone (committed state) or byte copy inside a temp sandbox; the working repo is never touched.
3. **Credentials** — the environment is scrubbed to a small allowlist; HOME and TMPDIR are re-pointed into the sandbox. Tokens, proxy vars, git config, and agent sockets don't reach the code.

Honest scope: this is process hygiene, not a jail. The child can still read world-readable files and reach the network — the scrub drops proxy and CA vars, so credential-injecting proxied egress usually fails, which is the safe direction. Clone mode is write-isolated, not read-isolated: the staged clone carries the repo's full reachable git history, so anything ever committed to a branch — including a secret committed and later reverted — is readable from inside the sandbox. Use `--copy` to leave history behind entirely. When code must not be trusted with the filesystem at all, use a container; this skill layers fine inside one.

## When to use

- Recipe scripts, their selftests, and evals (`guard.py --selftest`, `run_evals.py`)
- Third-party skill scripts — the vetting live-test before adopting a skill
- Vendored or copied samples, a stranger's repo, untrusted eval harnesses
- Any run whose pip installs you don't want in your real interpreter

When NOT to use:

- Code you wrote and trust, in its own repo — a plain run is fine
- A run that genuinely needs real HOME, git identity, or proxied network — pass explicit `--env NAME=VALUE` entries for exactly what it needs, or don't sandbox
- When the requirement is filesystem/network *confinement* — that's a container, not this

## Run it

```bash
scripts/sandboxed-run.sh [options] -- command [args...]
```

| Option | Effect |
|---|---|
| `-C DIR` | Stage DIR as the code under test and use it as cwd. Git work tree → throwaway clone (committed state incl. full history; uncommitted changes trigger a note). Otherwise → byte copy, `.git` dropped. |
| `--copy` | Force the byte copy (includes uncommitted changes). |
| `--no-venv` | Skip the venv (non-python runs). |
| `--require-venv` | Fail instead of continuing when no venv can be built. |
| `--env NAME` | Pass the parent's NAME through the scrub. |
| `--env NAME=VAL` | Set NAME inside the sandbox; applied last, so it can re-point HOME/TMPDIR when a run truly needs that. |
| `--keep` | Keep the sandbox for debugging; path printed to stderr. |
| `-h`, `--help` | Show the option summary. |

The wrapper prints one audit line to stderr (`sandbox=… mode=… venv=… home=sandbox env=allowlist`) and forwards the command's exit code. Sandbox deletion is containment-guarded: it only ever deletes a path `mktemp` created under `$TMPDIR`.

Examples:

```bash
# Recipe selftest — the house vetting bar for recipes/model-bakeoff-gate
scripts/sandboxed-run.sh -C . -- python3 scripts/guard.py --selftest

# Third-party skill script, copied to a scratch dir first; needs one token
scripts/sandboxed-run.sh -C /tmp/vendor-skill --env API_BASE=https://example.com -- node index.js

# Eval run that must be able to pip install
scripts/sandboxed-run.sh -C . --require-venv -- python3 scripts/run_evals.py all
```

## What the run sees

- cwd: the staged clone/copy (`-C`), or an empty scratch dir
- git: in clone mode, the repo's full reachable history — reverted secrets included; in copy mode, no `.git` at all
- PATH: sandbox venv first; `PYTHONNOUSERSITE=1` set either way
- env: `PATH SHELL USER LOGNAME LANG TERM LC_* PYTHONDONTWRITEBYTECODE` plus explicit `--env` entries — nothing else
- HOME/TMPDIR: sandbox-internal dirs, deleted with the sandbox
- exit code: the command's, preserved through teardown — a failed teardown keeps the sandbox and says so loudly instead of clobbering the code

## Common mistakes

| Mistake | Reality |
|---|---|
| Treating the venv as containment | It quarantines packages only — never the filesystem or network |
| Passing real secrets via `--env` "to make it work" | That re-leaks the one thing the scrub exists to withhold; pass the minimum, prefer keyless runs |
| Expecting dirty working-tree state in the default mode | The clone stages committed state; use `--copy` to test uncommitted changes |
| Assuming clone mode hides repo history | It doesn't — the clone copies all reachable history, reverted secrets included; `--copy` is the history-free mode |
| Reading results from the sandbox after a normal exit | It's deleted; write outputs to a path you choose, or use `--keep` |
