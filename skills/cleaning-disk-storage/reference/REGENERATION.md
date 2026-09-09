# Regeneration Instructions

How to restore deleted items after cleanup. Include these in the cleanup summary when applicable.

## Contents

- [Python](#python)
- [Node.js / JavaScript](#nodejs--javascript)
- [Rust / Cargo](#rust--cargo)
- [Build Outputs](#build-outputs)
- [Package Manager Caches](#package-manager-caches)
- [Cache Directories](#cache-directories)
- [AI Agent Directories](#ai-agent-directories)
- [Orphaned Application Data](#orphaned-application-data)
- [macOS System Data](#macos-system-data)
- [App Overlap (Removed Redundant Apps)](#app-overlap-removed-redundant-apps)
- [Time Estimates](#time-estimates)
- [Backup Recommendations](#backup-recommendations)
- [Restoration Priority](#restoration-priority)
- [Crash Logs](#crash-logs)

## Python

### Virtual Environments
```bash
# Create new virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Bytecode Cache
- `__pycache__` and `.pyc` files regenerate automatically when running Python scripts
- No action required

## Node.js / JavaScript

### Dependencies
```bash
# NPM
npm install

# Yarn
yarn install

# PNPM
pnpm install
```

### Build Artifacts
```bash
# Next.js
npm run build

# Nuxt.js
npm run build

# Vite
npm run build

# General
npm run build
```

## Rust / Cargo

### Build Artifacts
```bash
# Debug build
cargo build

# Release build
cargo build --release
```

### Toolchain
- Rustup toolchains: Reinstall with `rustup install <version>`
- Cargo packages: Re-download on next `cargo build`

## Build Outputs

### General Build Commands
```bash
# NPM-based
npm run build

# Cargo
cargo build --release

# Make
make

# Autotools
./configure && make

# CMake
mkdir build && cd build
cmake ..
make
```

## Package Manager Caches

### Homebrew
- Re-downloads on next `brew install` or `brew upgrade`
- No action required
- Initial installs may be slower

### pip
- Re-downloads wheels on next `pip install`
- No action required

### go
- Re-compiles on next `go build`
- No action required
- First build may be noticeably slower

### Playwright
```bash
npx playwright install
```
- Re-downloads all browser engines (~1 GB)

### pnpm
```bash
pnpm install
```
- Store rebuilds from package registry

## Cache Directories

### Most caches regenerate automatically
- No action required
- Tools will recreate as they work
- Initial runs may be slightly slower

## AI Agent Directories

### IDE Caches (Windsurf, Antigravity, Cursor)

**GPU caches, Code Cache**: Regenerated on next launch
- No action required
- May cause slight slowdown on first use after deletion

**Cascade/Codeium cache**: Rebuilds on next use
- Will rebuild automatically
- Initial AI features may be slower until cache rebuilds

**Logs**: Safe to delete
- Regenerate as tools run
- Backup first if debugging issues

### Gemini CLI

**tmp/**: Cleared automatically after sessions
- No action needed

**history/**: Contains conversation history
- Backup before deleting if important
- Cannot be restored once deleted

### Continue (VS Code)

**index/**: Code indexing data
- Rebuilds on next workspace open
- May slow down initially (1-5 minutes)

**sessions/**: Conversation history
- Cannot be restored
- Backup before deleting

### Factory AI / Qwen / Codex

**Logs, tmp**: Generally safe to delete
- Regenerate as tools run

**Sessions**: Conversation context
- Cannot be restored
- Will reset conversation history

### Claude Code

**debug/, shell-snapshots/, session-env/**: Old sessions/logs
- Safe to delete (old/inactive only)
- No restoration needed

## Orphaned Application Data

### General
- Cannot be restored — the parent application was already removed
- Data consists of cached profiles, logs, and settings with no active app to use them

### If reinstalling the app
- Download and install the application
- Sign in and reconfigure settings
- Some apps sync settings from cloud (Arc, Slack, Spotify)
- Others require full local reconfiguration (VPN clients, IDEs)

### ML Model Caches
- Re-download automatically when the ML tool is reinstalled and run
- Example: `pipx install marker-pdf` will re-download Surya OCR models (~3 GB)
- Use `pip cache purge` before reinstalling to ensure clean state

## macOS System Data

### Aerial Wallpaper Videos
- macOS re-downloads aerial videos automatically when an aerial wallpaper is active
- To prevent re-download: switch to a static wallpaper before deleting
- Change via: System Settings > Wallpaper > select a static/color option
- After deletion with static wallpaper set, macOS may recreate manifest/thumbnails (~12 MB) but not the full videos
- System-level assets at `/Library/Application Support/com.apple.idleassetsd/` should not be touched

## App Overlap (Removed Redundant Apps)

### Reinstalling a removed app
- Download from vendor website or `brew install --cask {name}`
- Most modern apps sync settings from cloud (browsers, Slack, Spotify, VPN accounts)
- IDEs may need extension reinstallation and settings reconfiguration
- VPN clients need login and preferred server configuration

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| Python venv + pip install | 1-5 minutes |
| Node_modules install | 1-10 minutes |
| Rust cargo build (debug) | 1-5 minutes |
| Rust cargo build (release) | 5-30 minutes |
| Continue index rebuild | 1-5 minutes |
| Cascade/Codeium cache rebuild | 5-15 minutes |
| Homebrew cache repopulate | 5-30 minutes (next upgrade cycle) |
| go cache rebuild | 1-5 minutes (next build) |
| Playwright browser install | 2-5 minutes |
| ML model re-download | 5-15 minutes (depending on model size) |
| Aerial wallpaper re-download | 30-60 minutes (30 GB, automatic) |
| App reinstall (brew cask) | 2-5 minutes |
| App reinstall + reconfigure | 5-15 minutes |

## Backup Recommendations

Before deleting, consider backing up:

### Always Backup
- Conversation history (Gemini history, Continue sessions)
- Active project virtual environments
- Important session data

### Optional Backup
- Log files (if debugging issues)
- Cache directories (if offline functionality needed)
- Index files (if immediate performance is critical)

## Restoration Priority

| Priority | Items | Reason |
|----------|-------|--------|
| **Critical** | `.git/`, auth files, configs | Data loss, re-authentication required |
| **High** | `node_modules`, `.venv`, `target/` | Time-consuming to restore |
| **Medium** | Caches, indexes | Performance impact until rebuilt |
| **Low** | `.DS_Store`, `__pycache__` | Automatic, minimal impact |

## Crash Logs

No regeneration needed. Crash logs and diagnostic reports are generated automatically when applications crash — they cannot and should not be recreated manually.
