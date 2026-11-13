# launchd gotchas

Edge cases for the disabled-services store, bootstrap failures, and the
loaded+disabled state. Read SKILL.md first; this file assumes its terms.

## The store is upsert-only and never forgets

`launchctl enable` and `launchctl disable` write to a per-UID store that
persists across logins and reboots:

- `disable` writes `"label" => disabled`.
- `enable` writes or overwrites `"label" => enabled`.
- Entries are never removed. Deleting the plist, booting out, uninstalling:
  none of it removes the store line.
- A label with no line is enabled by default.

Consequences:

- A leftover `=> enabled` line for a label that no longer exists is inert.
  No plist, no job, no effect. You can flip the line, but you cannot delete
  it, so do not try to clean it up.
- Presence-greps are broken by design:
  - `launchctl print-disabled gui/$UID | grep disabled` matches every
    disabled line, not the one you asked about.
  - `grep web` matches the line for `web-2` when you asked about `web`
    (prefix collision).
  - `grep web` also matches a persistent `"web" => enabled` line left over
    from a past enable, and misreports an enabled job as having a disabled
    flag.
- The only correct test: strip leading whitespace, then exact whole-line
  match with `grep -Fx "\"LABEL\" => disabled"`.

## rc=5 is ambiguous, so capture stderr

`launchctl bootstrap gui/$UID <plist>` failing with rc=5 and a generic
"Input/output error" covers at least three causes:

1. The label is disabled in the store (fix: `enable` first).
2. The job is already bootstrapped (fix: check `launchctl print` first).
3. A genuine I/O error: bad path, unreadable plist.

launchd's message never distinguishes them. Capture stderr, then run the
read-only checks before concluding anything:

```bash
err="$(launchctl bootstrap gui/"$uid" "$plist" 2>&1)"; rc=$?
launchctl print-disabled gui/"$uid" | grep -Fx "\"$label\" => disabled"
launchctl print gui/"$uid"/"$label" >/dev/null 2>&1 && echo loaded
```

The disable-line check and the loaded check together separate cause 1 and
cause 2. If both come back clean, suspect the path or plist contents.

## The loaded+disabled state (running-disabled)

Reachable two ways:

- `disable` while the job is loaded. Disable does not unload anything.
- A `disable` that succeeded followed by a `bootout` that failed.

In this state the job runs now, the store says disabled, and the next login
will not load it. launchd documents load-time gating only. Whether a
still-loaded disabled job respawns under KeepAlive is undocumented, so do
not claim it either way. Report the state (print succeeds AND the exact
disabled line matches) and park properly with disable-then-bootout when the
intent is "not running, and stays not running".

## gui/0 under sudo is meaningless

`sudo launchctl print-disabled gui/$UID` expands `$UID` to 0 in the root
shell, and `gui/0` is not a real user's domain. The fix is to resolve the
real user's UID explicitly:

```bash
real_uid="$(id -u alice)"          # or: stat -f %u /dev/console
sudo launchctl print-disabled gui/"$real_uid"
```

`/dev/console` is owned by the logged-in GUI user. Reads may work under
sudo, but never construct mutation targets from `$UID` inside a root shell.

## Legacy store formats: probe first

The `"label" => disabled` and `"label" => enabled` format is verified on
macOS 15.7.7, 26.6.2, and 27.0.1. Older macOS releases reportedly printed
`=> true` and `=> false` style lines. On any machine you have not verified,
run `scripts/probe.sh --park-test` first and build matchers from the line it
observes. Do not trust a format you have not seen on that release.

## Store residue is permanent

There is no command that deletes a store entry; enable and disable only flip
lines. A probe label's `=> enabled` line stays in every later
`print-disabled` listing, forever, inert. Name throwaway labels under
`com.local.launchd-probe.*` so anyone reading the store later can recognize
the residue.
