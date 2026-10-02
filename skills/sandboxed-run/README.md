# sandboxed-run

One-command containment for running untrusted or vendored code. A fresh venv,
a throwaway clone or copy of the code under test, and a credential-free
environment — built before the run, torn down after it, exit code preserved.

Born from a convention, not a theory: recipe selftests and third-party skill
vetting were being hand-sandboxed per run (venv here, temp repo there), which
is exactly the kind of manual procedure that drifts. This ships the procedure
as tooling — one script, same behavior from every agent.

## Quick start

```bash
scripts/sandboxed-run.sh -C . -- python3 scripts/guard.py --selftest
```

Full options and semantics: [SKILL.md](SKILL.md).

## What it quarantines

| Risk | Mechanism |
|---|---|
| pip installs landing in a shared interpreter | fresh venv per run, deleted with the sandbox |
| git side effects reaching the working repo | code staged into a throwaway clone (own `.git`) or a copy with `.git` dropped |
| tokens, proxy/CA vars, git config, agent sockets | env scrubbed to a small allowlist; HOME and TMPDIR re-pointed into the sandbox |

## What it does not do

It is not a jail. The child process can read world-readable files and reach
the network (proxied credential-injecting egress usually fails, which is the
safe direction). Clone mode is write-isolated, not read-isolated: the staged
clone carries the repo's full reachable history, so committed-then-reverted
secrets are readable inside the sandbox — use `--copy` to leave history
behind. For code that must not be trusted with the filesystem at all, use a
container — this layers fine inside one.

## Design notes

Both `rm -rf` uses in the script are deliberate and containment-guarded: the
teardown deletes only a path `mktemp` created under `$TMPDIR`, and a failed
teardown keeps the sandbox with a loud warning instead of clobbering the exit
code. skill-quality-gate flags both lines as `destructive:rm-recursive-force`
WARN by design — reviewed and accepted here; WARN is advisory, these are the
tool's core mechanics.

## Requirements

POSIX sh, `git` (for `-C` on a work tree), `mktemp`. Python is optional — runs
without it (`--require-venv` hardens a run that needs pip).
