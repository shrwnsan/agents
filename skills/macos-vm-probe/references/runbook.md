# Worked runbook — macOS 15 floor verification

A real session end to end with real timings and the mistakes made:
verify userspace behavior on the macOS 15 floor from a newer host.
Paste the blocks in order; change only the image for another version
(table in SKILL.md). Preflight: host `sw_vers -productVersion` for the
evidence record, `df -h /` (100GB+ free), `tart --version`.

## 1. Pull (background + disk guard)

```bash
set -o pipefail
tart pull ghcr.io/cirruslabs/macos-sequoia-base:latest > /tmp/tart-pull.log 2>&1 &
```

While it runs, check the guard every ~30 seconds:

```bash
du -sh ~/.tart
tail -2 /tmp/tart-pull.log
```

Real timing: ~3 minutes at ~40MB/s (~13GB). If `du -sh ~/.tart` passes
~45GB the image is wrong — stop the pull (`pkill -f "tart pull"` or
stop the background task), `rm -rf ~/.tart`, confirm with `df -h /`,
and re-pick from the table. Pipe lessons from this session:
`tart pull ... | head -3` kills the pull (once `head` exits, SIGPIPE
takes the download down mid-flight) — redirect to a file and `tail` it;
and a bare pipe masks exit codes, so always `set -o pipefail`.

## 2. Clone and boot

```bash
tart clone ghcr.io/cirruslabs/macos-sequoia-base:latest probe-vm  # mandatory: OCI sources can't run directly
tart run probe-vm > /tmp/tart-run.log 2>&1 &  # console goes to the virtual display, not this log
IP=$(tart ip probe-vm)    # blocks until DHCP; 60-90s in this run
echo "$IP"                # e.g. 192.168.64.15
```

On a macOS 27 host the DHCP step never completed and `tart ip` hung.
Use the guest agent instead, which needs no network:

```bash
until tart exec probe-vm true 2>/dev/null; do sleep 3; done
tart exec probe-vm sudo -n networksetup -setmanual "Ethernet" 192.168.64.50 255.255.255.0 192.168.64.1
IP=192.168.64.50
```

The 108GiB and ~13GB figures in this runbook come from the first,
older image. A later pull of the same tag was 31-33GB and its clone
grew to 27-29GB, so allow about 65GB free. SKILL.md step 3b lists the
guest quirks (no internet, `PATH`, GUI launch, Gatekeeper dialog).

## 3. SSH (askpass, non-interactive)

```bash
printf '#!/bin/sh\necho admin\n' > /tmp/askpass.sh
chmod +x /tmp/askpass.sh
vmssh() {
  SSH_ASKPASS=/tmp/askpass.sh SSH_ASKPASS_REQUIRE=force \
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    admin@"$IP" "$@"
}
for i in 1 2 3 4 5; do vmssh 'echo connected' && break; sleep 5; done  # retries absorb the sshd startup race
```

## 4. Ship the probe as a file, then run it

Never inline the probe in the ssh command — quoting collapses first.
Write it locally as `probe.sh`, pipe it over, execute it. This one is
generic userspace: OS identity plus a launchd disabled-store format
check, using a throwaway label:

```bash
#!/bin/bash
# Runs entirely inside the VM. Self-contained, safe to re-run.
set -euo pipefail
echo "== sw_vers =="
sw_vers
echo "productVersion: $(sw_vers -productVersion)"
echo "== launchd disabled-store format =="
LABEL="com.example.vmprobe.throwaway"; DOMAIN="gui/$(id -u)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.example.vmprobe.throwaway</string>
  <key>ProgramArguments</key><array><string>/bin/true</string></array>
  <key>RunAtLoad</key><false/>
</dict></plist>
EOF
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl disable "$DOMAIN/$LABEL"
launchctl print-disabled "$DOMAIN"
launchctl enable "$DOMAIN/$LABEL"
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
rm -f "$PLIST"
echo "== probe complete =="
```

Ship and run (the `tee` keeps a local verbatim copy):

```bash
cat probe.sh | vmssh 'cat > ~/probe.sh'
vmssh 'bash ~/probe.sh' | tee /tmp/probe-results.txt
```

## 5. Record the evidence

This run: VM `sw_vers -productVersion` → 15.7.7 (macos-sequoia-base
image); host macOS 27; caveat stated alongside — VM evidence is valid
for userspace behavior only, not hardware-dependent behavior. Keep
exact outputs verbatim; paraphrased evidence is not evidence.

## 6. Teardown (verify, don't assume)

```bash
tart stop probe-vm            # skip if it already exited
tart delete probe-vm
rm -rf ~/.tart
df -h /
```

This run reclaimed 108GiB; if `df -h /` does not show it back,
`du -sh ~/.tart` should be tiny or nonexistent — investigate first.

## Near-miss: the runner image

The session's first image choice was a `ghcr.io/cirruslabs/macos-runner:*`
CI image — the pull reached 79G downloaded with only 36GiB of disk free
before the guard caught it and it was aborted. Bare `macos-*-base`
images (~13-26GB) answer the same userspace questions: same `sw_vers`,
same launchd, same CLI tools. Golden rule: `*-base` only, cache under
~45GB during any pull, `df -h /` verified before calling it done.
