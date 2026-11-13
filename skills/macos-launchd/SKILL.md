---
name: macos-launchd
description: "Manage and debug macOS launchd services and LaunchAgents/LaunchDaemons: query loaded jobs, read the persistent per-user disabled-services store, safely enable/disable/bootout/bootstrap jobs, and diagnose KeepAlive/RunAtLoad persistence behavior. Use when working with launchctl, LaunchAgents (~/Library/LaunchAgents), LaunchDaemons, bootout/bootstrap, or KeepAlive/RunAtLoad questions; when a job keeps restarting, won't start at login, or still runs after logout; when disabling or enabling a launchd service; or when inspecting whether a service survives logout, reboot, or disable."
license: Apache-2.0
compatibility: "Requires macOS (launchd). Behaviors verified on macOS 15.7.7, 26.6.2, and 27.0.1."
metadata:
  author: shrwnsan
  version: "1.0.0"
---

# macOS launchd services

How to inspect and change launchd job state for the current user: read the
persistent disabled-services store correctly, park a job so it stays parked,
resume one safely, and avoid the sudo and rc=5 traps.

## Domain model

- Domains: `gui/$UID` is the per-user GUI session, where user LaunchAgents in
  `~/Library/LaunchAgents` live. `system` is for root LaunchDaemons. This
  skill targets `gui/$UID` throughout.
- The disabled-services store is per-UID, PERSISTENT across logins and
  reboots, and UPSERT-ONLY. `launchctl enable` writes an explicit
  `=> enabled` line; entries are never removed. A label with no store line
  is enabled (the default).
- Two independent facts per job:
  1. Store flag: will launchd load it? Ask `launchctl print-disabled`.
  2. Loaded now: is it resident in this session? Ask `launchctl print`.

## Reading state (always safe)

Store flag:

```bash
launchctl print-disabled gui/"$(id -u)"
```

Real output uses leading tabs on entry lines:

```
    "com.example.agent" => disabled
    "com.example.other" => enabled
```

Detection rule (normative): strip leading whitespace, then require an exact
whole-line match of `"LABEL" => disabled`. Use `grep -Fx`. NEVER presence-grep
the bare label:

- Prefix collisions: label `web` also matches the store line for `web-2`.
- Explicit `=> enabled` lines persist forever, so a label grep also hits
  them and misreports an enabled job as disabled.

A failed `print-disabled` call (non-zero exit) means the flag is UNKNOWN.
Never treat an unknown flag as disabled.

Loaded state:

```bash
launchctl print gui/"$(id -u)"/com.example.agent
```

- Exit 0: the job is loaded in the gui domain.
- Non-zero exit: not loaded.

Loaded plus disabled is the `running-disabled` state: the job runs now but
will NOT survive the next login, because disabled jobs are not loaded at
login. Report the state instead of assuming respawn behavior (see
references/gotchas.md).

## Mutations (order matters)

Every command below names the target in `gui/$UID/<label>` form, except
`bootstrap`, which takes the domain plus a plist path.

### Park (disable, then bootout)

```bash
launchctl disable gui/"$(id -u)"/com.example.agent
launchctl bootout gui/"$(id -u)"/com.example.agent
```

Disable FIRST so the job cannot be reloaded; then bootout to unload it.

- Disable alone leaves a loaded job running.
- Bootout alone is undone at the next login: the store still says enabled,
  so `RunAtLoad` reloads the job.

`bootout` of an already-unloaded job exits 0 harmlessly. `disable` and
`enable` work whether or not the job is loaded.

### Resume (enable, then bootstrap)

```bash
launchctl enable gui/"$(id -u)"/com.example.agent
launchctl bootstrap gui/"$(id -u)" /path/to/Agent.plist
```

Enable FIRST. Bootstrapping a disabled label fails with rc=5 and a generic
"Input/output error"; launchd never says "disabled". The store must say
enabled before bootstrap, or you cannot tell the failure causes apart.

### KeepAlive semantics

- Disable gates LOADING. A booted-out disabled job cannot be reloaded, and
  `RunAtLoad` cannot resurrect it at login. That is what makes
  disable-then-bootout durable.
- For a STILL-LOADED disabled job, respawn behavior is undocumented. Name
  the `running-disabled` state in your report instead of guessing.

## Safety

- Per-UID isolation: you can only affect your own user's gui domain.
- THE SUDO TRAP: under `sudo`, `$UID` is 0, and `gui/0` fails. It is not a
  different user's domain; it is meaningless. Resolve the real user's UID
  first (`id -u <realuser>` or `stat -f %u /dev/console`), then build
  `gui/<that-uid>` targets.
- Mutations affect real services. Query read-only first; mutate only with
  explicit user intent.
- Probe-label technique: to verify store format or behavior without touching
  real services, bootstrap a throwaway plist (ProgramArguments `/bin/true`,
  label like `com.<you>.format-probe`) from `~/Library/LaunchAgents/`,
  disable it, read `print-disabled`, then `enable` and delete the plist.
  The store line remains forever (inert, undeletable); accept that residue.
  `scripts/probe.sh --park-test` does this for you under a random label.
- Unfamiliar macOS version: run the probe FIRST before trusting any output
  matcher. Older releases reportedly printed `=> true` instead of
  `=> disabled`. To provision a clean VM of a specific macOS version for
  this check, use the `macos-vm-probe` skill and run
  `scripts/probe.sh --park-test` inside the VM.

## Version compatibility

The `"label" => disabled` store format was verified live on macOS 15.7.7,
26.6.2, and 27.0.1. On any other release, treat the format as unverified
until `scripts/probe.sh --park-test` confirms it.

## Tools in this skill

- `scripts/probe.sh [label]`: read-only. Prints the resolved
  `gui/$(id -u)` target, the exact store verdict for the label (disabled /
  enabled / absent / unknown), and whether the job is loaded. With no label,
  it prints the whole store listing.
- `scripts/probe.sh --park-test`: the throwaway-label park test. Mutating,
  but confined to its own random label; cleans up through an EXIT trap and
  prints the residue note.
- `references/gotchas.md`: rc=5 ambiguity, prefix collisions, store residue,
  the loaded+disabled state, and legacy store formats.
