# Smoke Test

Every command in SKILL.md must be executed at least once before shipping — the `//lib/systemd/system/` double-slash in early versions was the fingerprint of an unrun command.

## Running

```sh
sh scripts/smoke-test.sh
```

Read-only; never prompts for sudo. Commands requiring root run only when passwordless sudo is available (`sudo -n`), otherwise SKIP. Linux-only commands SKIP on macOS and vice versa.

## Passing

- Exit 0 and `0 fail` in the summary.
- Every SKIP must be for a valid reason (`platform` or `needs-sudo`) — a SKIP on the platform the command targets is a bug.
- A FAIL means the command is wrong or the environment changed — fix before shipping.

## When to re-run

- After any edit to SKILL.md that adds or changes a command.
- After major macOS upgrades (commands like `sfltool` change interface between versions).
- Rule: **no command ships in SKILL.md without a smoke-test PASS or a documented SKIP.**

## Adding commands

Append a `run <id> <condition> "<cmd>"` line to `scripts/smoke-test.sh` with the same phase ID scheme (P1-05, P2-03, …).
