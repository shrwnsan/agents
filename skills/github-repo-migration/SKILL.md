---
name: github-repo-migration
license: Apache-2.0
description: >
  Migrate GitHub forks between accounts safely: re-fork upstream repos on a
  target account and carry over local commits on dev branches without
  touching the originals. Covers quiet mirrors (byte-identical forks),
  forks with own commits, and branch triage. Use when relocating forks to
  another account (e.g. a machine/bot account), cleaning up a fork
  inventory, or when asked to "move/mirror my forks". Includes
  credential-injecting proxy pitfalls, per-call identity verification,
  throttling, and reversible batch checkpoints.
compatibility: Requires git, curl, jq, Node.js 18+, and network access to api.github.com. Behaviors for credential-injecting API proxies are conditional; see references/PLATFORMS.md for per-OS config and state locations.
metadata:
  author: shrwnsan
  version: "0.2.0"
---

# GitHub Repo Migration

Move forks from a source GitHub account to a target account by **re-forking
upstream** on the target and pushing any of your own work as new branches.
Never transfer repos and never delete originals. Everything is reversible:
a bad fork on the target is deleted; the source is never modified.

## Core rules (never skip)

1. **Bypass credential-injecting proxies for cross-account calls.** If your
   environment routes HTTP through a proxy that injects `Authorization`
   headers (e.g. a credential gateway), that injection OVERRIDES your
   explicit token and every call lands on the WRONG account. Use a direct
   connection (`curl --noproxy '*'` / fetch with proxy disabled) with an
   explicit `Authorization: Bearer <target-account PAT>` header for every
   fork, push, and verification call.
   **Node ≥24 gotcha (verified 2026-11-15):** deleting proxy env vars
   *inside* the script is not enough—undici's `EnvHttpProxyAgent` binds from
   the environment at process startup, so `fetch` keeps routing through the
   proxy and the gateway still overrides the header. Launch with the vars
   already unset: `env -u HTTPS_PROXY -u https_proxy -u HTTP_PROXY -u
   http_proxy node migrate-batch.mjs …`. The `/user` identity gate below is
   the enforcement point that catches this.
2. **Verify response identity, not status codes.** A `202` from the fork
   API proves nothing. Check the response body: `full_name` must start with
   `<target-account>/`. A call that lands on the wrong account is a failed
   call even if it returned 2xx. GitHub's fork API is idempotent per
   account—if the wrong account already has the fork, the misdirected call
   silently "succeeds" by returning the existing fork. Count nothing as
   migrated until its identity check passes.
3. **Verify before acting on failure.** Before any cleanup or deletion,
   confirm the problem actually exists (list the target account's repos,
   compare against the plan). Announce results only after verification.
   GitHub idempotency may mean a suspected batch of duplicates never
   existed.
4. **Throttle and checkpoint.** Max ~1 fork request/second; stay under
   ~1,500 core API requests/hour per account. Run in batches (30 is a good
   size), verify each batch landed on the target before starting the next,
   and pause for a human checkpoint between batches.
5. **Secrets by reference.** The PAT comes from the configured secret
   source (env var or secrets manager—see config below), fetched at run
   time, never printed, never written to any file this skill creates.

## Configuration and state (role-based, resolved per platform)

The skill uses three external locations. Resolve by ROLE, not hardcoded
path—the executing platform knows its own conventions:

- **Config** (`config.yaml`): source account, target account, batch size,
  throttle seconds, secret source reference. Location: the platform's
  user-config directory (e.g. `~/.config/github-repo-migration/` on
  Linux/macOS, `%APPDATA%\github-repo-migration\` on Windows). Absent config →
  sensible defaults; ask the operator for the two account names if unset.
- **State** (`progress.json`): tranches done, per-batch results, counters.
  Location: the platform's user-state directory (e.g.
  `~/.local/state/github-repo-migration/`, `%LOCALAPPDATA%\github-repo-migration\state\`).
  Absent state → start fresh; write after every batch, not at the end.
- **Secrets**: never in either file. Referenced by name (see `config.yaml`
  `secret_source`); retrieved per platform at run time.

## Procedure

1. **Inventory the source.** Paginate `GET /users/<source>/repos` (or the
   authenticated equivalent); keep forks only. Snapshot metadata: name,
   parent full name, pushed_at, default branch.
2. **Classify.**
   - **Quiet mirror**: default branch identical to parent's, no extra
     branches, no own commits → target gets a plain re-fork; nothing to
     carry.
   - **Own commits**: commits authored by the account on the default
     branch or extra branches → carry each to a `dev/*` branch on the
     target fork; the target's default branch stays an upstream mirror.
     Compare via `git` (local clone + `git log --author`) over the API
     where cheaper; batch branch scans into single calls.
   - **Branch triage**: for each extra branch, check for an open/closed
     PR; merged branches are dropped, unmerged ones are pushed to the
     target fork. Branches that mirror upstream's own branches (gh-pages,
     dev, wip) need no triage.
3. **Migrate in batches** (respecting Core rules 1, 2, 4):
   `POST /repos/<parent-owner>/<parent-repo>/forks` on a direct
   connection → identity-check the response → upload carried branches.
4. **Verify each batch.** `GET /repos/<target>/<name>` returns 200 and
   `parent.full_name` matches the upstream parent. Spot-check the default
   branch matches upstream where the class demands it.
5. **Record and report.** Update `progress.json`; report counts and any
   skipped repos with reasons. Originals stay untouched—say so.

## Bundled script

`scripts/migrate-batch.mjs`—Node 18+, no dependencies: takes a batch of
`parent-owner/repo` entries, forks each onto the target with per-call
identity verification, throttling, and state writing. Reads config/state
by role per `references/PLATFORMS.md`. Run it directly; if proxy env vars
are set and `--allow-proxy` is absent, it strips them in-process so calls
go direct. It then refuses to fork unless `/user` confirms the target
account (rule 2)—the identity gate is the enforcement point, not the
proxy check.

## Failure playbook

- **Fork landed on the wrong account** (identity check fails): stop the
  batch. Do NOT attempt cleanup until you have listed the wrong account's
  repos and confirmed what actually changed—idempotency often means
  nothing new was created. Report; get the operator's decision.
- **403 on deletion**: the token lacks `delete_repo`. Deletion is an
  operator action or a scoped token minted for the cleanup only.
- **401 on the PAT**: the stored secret may be wrapped/encoded (e.g. a
  JSON envelope)—unwrap per its documented format before assuming the
  token is dead.
- **Identity gate fires as the wrong account (rule 1 gotcha)**: the token
  is fine—the runtime is still proxying. Re-run with the proxy vars unset
  before node starts (see rule 1); do not attempt cleanup, idempotent fork
  semantics mean the misdirected run created nothing (verified 2026-11-15).
- **Upstream drifted mid-migration**: re-check the parent's default branch
  at batch start; a "quiet mirror" classification from an old snapshot can
  be stale.

## References

- [references/PLATFORMS.md](references/PLATFORMS.md)—per-OS locations,
  tool notes (including Windows-native without WSL), proxy detection.
