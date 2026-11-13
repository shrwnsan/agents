---
name: macos-vm-probe
description: >-
  Provision and probe clean macOS VMs of a specific version (15, 26, 27, ...)
  with Tart to verify behavior across macOS releases. Use when a check must be
  verified on the macOS 15 floor or another version, when comparing behavior
  across macOS releases, or before tagging a release that gates on an OS
  version. Fires on requests like "verify this on macOS 15/26/older", "test on
  a different macOS version", "clean macOS VM", "does X behave the same on
  older macOS", or "release gating across macOS versions", and on Tart usage.
  Runs on Apple silicon hosts; probes userspace behavior (launchd, CLI tools),
  not hardware-dependent behavior. Not for generic virtualization questions
  (Docker, Linux VMs, OrbStack).
license: Apache-2.0
compatibility: >-
  Requires macOS host with Apple silicon, Tart (Virtualization.framework CLI),
  ~65GB free disk (a pulled base image is 13-33GB and a running clone grows
  to about the same again), and network for the pull.
metadata:
  author: shrwnsan
  version: "1.1.0"
---

# macOS VM Probe

Stand up a clean macOS VM of a chosen version, run a probe against it,
record evidence, and tear everything down. Use it to verify any behavior
on a specific macOS version in a clean environment, without touching the
host. `references/runbook.md` has a complete worked example with real
timings — read it before the first run.

## Evidence rules (read before promising anything)

- A VM is valid evidence for **userspace behavior only**: launchd output
  and state formats, CLI tool behavior, file system semantics,
  plist/config formats.
- A VM is NOT valid evidence for **hardware-dependent behavior** (GPU,
  accelerators, network hardware, performance numbers). Every recorded
  result must say so explicitly: name the host OS, the VM OS, and state
  that the evidence came from a VM.
- The deliverable of a run: `sw_vers -productVersion` from inside the VM
  plus the exact probe outputs, captured verbatim, followed by a
  verified teardown (`df -h /` shows the disk space back).

## Step 1 — Install Tart

Do not use Homebrew: `brew tap cirruslabs/cli` is broken against
Homebrew 7. Install the release tarball instead:

```bash
cd "$(mktemp -d)"
curl -LO https://github.com/cirruslabs/tart/releases/latest/download/tart.tar.gz
tar -xzf tart.tar.gz                     # -> ./tart.app
mv tart.app /Applications/
mkdir -p ~/.local/bin
ln -sf /Applications/tart.app/Contents/MacOS/tart ~/.local/bin/tart
tart --version
```

Cleanup later = delete `/Applications/tart.app` and `~/.local/bin/tart`.

## Step 2 — Pick the image (critical section)

Use **bare base images only** — minimal userspace, 13-33GB on disk
(`macos-sequoia-base` measured 31-33GB in Nov 2026; sizes drift upward):

| Target macOS | Image | Verified in a real run |
|---|---|---|
| 15 (floor era) | `ghcr.io/cirruslabs/macos-sequoia-base:latest` | 15.7.7 |
| 26 | `ghcr.io/cirruslabs/macos-tahoe-base:latest` | 26.6.2 |
| 27 | use the host itself if it already runs 27 | — |
| anything else | try `ghcr.io/cirruslabs/macos-<name>-base:latest` | — |

For unlisted versions, test the `macos-<name>-base:latest` pattern
directly: nonexistent repos return `DENIED` instantly at the manifest
check, so a wrong name costs seconds. Fail fast — never substitute a
bigger image to "get close".

**NEVER** use `ghcr.io/cirruslabs/macos-runner:*` (or other full CI
images) for a userspace question. They ship complete CI toolchains and
blow past 80GB — a real pull reached 79G downloaded with only 36GiB of
disk free before it was aborted (see the runbook's near-miss).

**HARD DISK GUARD — non-negotiable.** During any pull, poll
`du -sh ~/.tart` (every ~30s). If the cache passes ~45GB, the image is
wrong (a correct sequoia-base pull stops near 33GB): stop the pull (`pkill -f "tart pull"` or stop the background
task), then clean up and re-pick from the table:

```bash
rm -rf ~/.tart && df -h /
```

A disk that fills mid-pull can wedge the host. This guard exists because
it nearly happened.

## Step 3 — Pull, clone, boot, probe (normative order)

1. **Pull** — background it and monitor per the disk guard:
   `tart pull <image>`. Never pipe a pull into `head`; once `head`
   exits, SIGPIPE kills the download mid-flight. Redirect to a log and
   `tail` it. Use `set -o pipefail` in any script that pipes.

2. **Clone** — `tart clone <image> probe-vm`. Pulled images are OCI
   sources and CANNOT be run directly. The clone is an APFS
   copy-on-write copy: near-free at clone time, growing toward the
   image size (27-29GB observed) as the guest writes. Because cloning
   is cheap, keep the pulled image between runs and delete only the
   clone; re-pulling costs the full download. `tart list --quiet`
   lists names (images show up twice, once with an `@sha256:` entry).

3. **Run** — `tart run probe-vm > /tmp/tart-run.log 2>&1 &` (or in a
   background task). Boot console output goes to the virtual display,
   not the log — do not wait for boot lines in the log file.

4. **Get the IP** — `tart ip probe-vm` blocks until DHCP answers
   (typically 60-90s; result looks like 192.168.64.x). The first ssh
   may race the VM's sshd startup — retry a few times before
   concluding anything is broken. **On a macOS 27 host the DHCP server
   (bootpd) may never answer and `tart ip` hangs forever.** Do not wait:
   `tart exec` talks to the guest agent (ready about 10s after boot,
   needs no network), so set a static address through it:

   ```bash
   until tart exec probe-vm true 2>/dev/null; do sleep 3; done
   tart exec probe-vm sudo -n networksetup -setmanual "Ethernet" \
     192.168.64.50 255.255.255.0 192.168.64.1
   IP=192.168.64.50     # the guest has passwordless sudo
   ```

   Run the VM with `tart run --no-graphics probe-vm`: it still creates
   the guest GUI session, and it needs no window on the host.

5. **SSH as admin/admin** (cirruslabs base image default), fully
   non-interactive via an askpass helper:

   ```bash
   printf '#!/bin/sh\necho admin\n' > /tmp/askpass.sh
   chmod +x /tmp/askpass.sh
   SSH_ASKPASS=/tmp/askpass.sh SSH_ASKPASS_REQUIRE=force \
     ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
     admin@$IP 'echo connected'
   ```

6. **Ship the probe as a file, never inline** — avoids quoting hell:

   ```bash
   cat probe.sh | SSH_ASKPASS=/tmp/askpass.sh SSH_ASKPASS_REQUIRE=force \
     ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
     admin@$IP 'cat > ~/probe.sh'
   ```

   Then execute it the same way: `... admin@$IP 'bash ~/probe.sh'`.

7. **Record + clean up.** Capture `sw_vers -productVersion` and the
   exact probe output verbatim, then:

   ```bash
   tart stop probe-vm     # only if still running
   tart delete probe-vm
   rm -rf ~/.tart         # if the image isn't needed again
   df -h /                # verify the space is actually back
   ```

## Step 3b — Guest quirks to expect

- **The guest NAT may have no internet.** Do not plan on `curl`, `brew`
  or `git clone` inside the VM. Serve what the probe needs from the
  host: `python3 -m http.server 8000 --bind 192.168.64.1` in the
  artifact directory, and fetch from `http://192.168.64.1:8000/`. For
  Homebrew, write a local tap (`brew tap-new --no-git local/probe`) with
  a cask or formula whose `url` points at the host server and whose
  `sha256` is computed from the local file; set
  `HOMEBREW_NO_AUTO_UPDATE=1`. Kill the server in a `trap ... EXIT`.
- **Non-login ssh shells lack Homebrew on `PATH`.** Export
  `/opt/homebrew/bin` at the top of the probe.
- **Launching a GUI app from ssh** needs the console user's session:
  `sudo launchctl asuser 501 sudo -u admin /usr/bin/open -a <app>`
  (501 is the base image's `admin`).
- **Quarantined ad-hoc or unnotarized apps block `open -a`** on a
  Gatekeeper "Not Opened" dialog. To see it, run `screencapture` in the
  background through the same `launchctl asuser` wrapper. The dialog's
  default button is Move to Trash, so never dismiss it blind. To run
  such an app anyway: `xattr -dr com.apple.quarantine <app>`.
- **Clean up on every exit path.** A leftover `tart run` keeps the VM
  locked and a leftover HTTP server holds its port. Put
  `tart stop`, `tart delete` and the server kill in one `EXIT` trap.
- **Prefer one orchestrator script per recurring check** (clone, boot,
  static IP, ship files, run, trap cleanup) over replaying this
  runbook by hand. It ends with the VM deleted and exit code 0 as the
  pass signal.

## Step 4 — Evidence discipline

- Name the host OS and the VM OS in every recorded result.
- Always note "verified in a VM" — never present VM output as
  physical-hardware behavior.
- Keep probe scripts self-contained: no repo dependencies, absolute
  paths, safe to re-run. A throwaway launchd label (bootstrap, disable,
  read the disabled store back with `launchctl print-disabled`, bootout)
  is a good template for userspace probes — the runbook has one. For
  launchd disabled-store semantics (exact-match rules, upsert-only
  store), see the `macos-launchd` skill, whose `scripts/probe.sh
  --park-test` is designed to run inside these VMs.

## Worked example

`references/runbook.md` is a complete runbook from a real session:
sequoia-base pull (~3 min at ~40MB/s), clone, boot-to-IP (~60-90s), the
askpass ssh session with its sshd race, a generic launchd userspace
probe, teardown with `df -h /` verifying 108GiB reclaimed — plus the
runner-image near-miss (79G pulled, 36GiB free, aborted) and the
SIGPIPE / pipefail lessons.
