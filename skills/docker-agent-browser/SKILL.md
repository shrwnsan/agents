---
name: docker-agent-browser
description: Ensures agent-browser is installed and functional in Docker container environments. Use when agent_browser tool fails with "agent-browser is required but was not found on PATH", or when setting up browser automation in a new container session.
allowed-tools: Bash(npm:*), Bash(sudo:apt:*), Bash(sudo:dnf:*), Bash(which:*), Bash(uname:*), Bash(ls:*), Bash(find:*)
---

# Docker Agent-Browser Setup

Ensures the `agent-browser` binary and a Chromium-based browser are available inside Docker containers so that the `agent_browser` native tool works.

## When to Use

- The `agent_browser` tool fails with `"agent-browser is required but was not found on PATH"`
- Starting a fresh Docker container that needs browser automation
- After a container rebuild where global npm packages are lost

## What This Fixes

Pi's `pi-agent-browser-native` extension wraps the upstream `agent-browser` CLI binary. The extension is bundled with Pi, but the **upstream binary is a separate install** that does not persist across container rebuilds. This skill automates that setup.

## Detection

```bash
which agent-browser 2>/dev/null && echo "FOUND" || echo "MISSING"
```

If the binary is intercepted by the Pi wrapper, use the direct path check:

```bash
ls -la "$(npm root -g)/agent-browser/bin/agent-browser-linux-arm64" 2>/dev/null && echo "FOUND" || echo "MISSING"
```

## Setup Steps

### 1. Install agent-browser via npm

```bash
npm install -g agent-browser
```

Verify (direct binary call to avoid wrapper interception):

```bash
"$(npm root -g)/agent-browser/bin/agent-browser-linux-arm64" --version
```

Expected output: `agent-browser <version>`

### 2. Install a Chromium-based browser

**Chrome for Testing does not provide Linux ARM64 builds.** Use system Chromium instead.

Detect architecture:

```bash
ARCH=$(uname -m)
echo $ARCH
```

#### Debian/Ubuntu (x86_64 or ARM64)

```bash
sudo apt update && sudo apt install -y chromium
```

Verify:

```bash
which chromium
```

#### Fedora/RHEL

```bash
sudo dnf install -y chromium
```

#### If system package manager has no chromium

Try these alternatives in order:

```bash
# Snap-based systems
sudo snap install chromium

# Or install google-chrome-stable
wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i /tmp/google-chrome.deb || sudo apt -f install -y
```

### 3. Verify end-to-end

Attempt a basic browser action:

```
Use agent_browser to open https://example.com
```

If successful, agent-browser is fully operational.

## Architecture Reference

| Architecture | Binary Suffix | Install Path |
|---|---|---|
| Linux ARM64 (aarch64) | `agent-browser-linux-arm64` | `$(npm root -g)/agent-browser/bin/` |
| Linux x86_64 | `agent-browser-linux-x64` | `$(npm root -g)/agent-browser/bin/` |
| macOS ARM64 | `agent-browser-darwin-arm64` | `$(npm root -g)/agent-browser/bin/` |
| macOS x86_64 | `agent-browser-darwin-x64` | `$(npm root -g)/agent-browser/bin/` |

## Common Issues

### "Chrome for Testing does not provide Linux ARM64 builds"

Expected on ARM64 Docker containers (e.g., Apple Silicon VMs). Solution: install system Chromium via `apt` and the binary auto-detects it.

### Binary installs but `agent_browser` tool still fails

Ensure the symlink exists:

```bash
ls -la "$(npm root -g)/../bin/agent-browser"
```

It should point to the correct architecture binary. If missing or broken:

```bash
ln -sf "$(npm root -g)/agent-browser/bin/agent-browser-linux-$(uname -m | sed 's/aarch64/arm64/' | sed 's/x86_64/x64/')" "$(npm root -g)/../bin/agent-browser"
```

### Permission denied on binary

```bash
chmod +x "$(npm root -g)/agent-browser/bin/agent-browser-linux-"*
```

### Stale Chrome processes blocking new sessions

```bash
pkill -f chromium || true
pkill -f chrome || true
```

## Persistence Note

Global npm installs (`npm install -g`) do **not** persist across Docker container rebuilds. To make this permanent, add to your Dockerfile:

```dockerfile
RUN npm install -g agent-browser && \
    agent-browser install || true && \
    apt-get update && apt-get install -y chromium
```

Or mount `~/.agents/skills/docker-agent-browser` as a volume and re-run setup on each new session.
