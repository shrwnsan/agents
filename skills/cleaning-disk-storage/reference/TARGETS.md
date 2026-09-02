# Targets to Scan

Comprehensive reference of temporary files, caches, and build artifacts to scan for cleanup.

## Contents

- [Quick Reference](#quick-reference)
- [Category Summaries](#category-summaries)
- [Scanning Strategy](#scanning-strategy)
- [Common Scan Commands](#common-scan-commands)
- [Cleanability Guide](#cleanability-guide)

## Quick Reference

| Category | Reference | Typical Size |
|----------|-----------|--------------|
| Common files | [./common.md](./common.md) | 1-50 MB |
| Python | [./python.md](./python.md) | 100 MB - 5 GB |
| Node.js | [./nodejs.md](./nodejs.md) | 500 MB - 10 GB |
| Rust | [./rust.md](./rust.md) | 100 MB - 2 GB |
| Build outputs | [./build.md](./build.md) | 50 MB - 2 GB |
| Package manager caches | [./package-managers.md](./package-managers.md) | 1-20 GB |
| Caches | [./cache.md](./cache.md) | 1-30 GB |
| AI agents | [./ai-agents.md](./ai-agents.md) | 2-4 GB |
| IDE/Editor | [./ide.md](./ide.md) | 10-300 MB |
| Orphaned app data | [./orphaned-data.md](./orphaned-data.md) | 500 MB - 10 GB |
| macOS system data | [./macos-system-data.md](./macos-system-data.md) | 5-30 GB |
| App overlap | [./app-overlap.md](./app-overlap.md) | 2-15 GB |
| Crash logs | [./crash-logs.md](./crash-logs.md) | 50 MB - 2 GB |

## Category Summaries

### Common Files
Platform-agnostic temporary files: `.DS_Store`, `Thumbs.db`, Vim swap files, shell history.

→ [./common.md](./common.md)

### Python
Bytecode caches (`__pycache__`), virtual environments (`.venv`), pytest caches, mypy caches.

→ [./python.md](./python.md)

### Node.js / JavaScript
Dependencies (`node_modules`), package manager caches (`.npm`, `.yarn`), framework builds (`.next`, `.nuxt`).

→ [./nodejs.md](./nodejs.md)

### Rust / Cargo
Build artifacts (`target/`), Cargo registry cache, Rustup toolchain.

→ [./rust.md](./rust.md)

### Build Outputs
Distribution directories (`dist/`, `build/`, `out/`), object files (`.o`, `.a`, `.so`), Go test binaries.

→ [./build.md](./build.md)

### Cache Directories
User cache (`~/.cache/`), macOS caches (`~/Library/Caches/`), language-specific caches.

→ [./cache.md](./cache.md)

### Package Manager Caches
Homebrew bottles, pip wheels, go build cache, Playwright browsers, pnpm store.

→ [./package-managers.md](./package-managers.md)

### AI Agent Directories
Claude Code, Gemini CLI, Windsurf IDE, Antigravity IDE, Continue, Cursor, Factory AI/Droid, Qwen Code, Codex.

→ [./ai-agents.md](./ai-agents.md)

### IDE / Editor
VS Code caches, IntelliJ IDEA project files, Haxe crash dumps.

→ [./ide.md](./ide.md)

### Orphaned Application Data
Data left behind by uninstalled apps: IDE profiles, VPN configs, ML model caches. Detect by matching Library directories against installed applications.

→ [./orphaned-data.md](./orphaned-data.md)

### macOS System Data
macOS-managed data not tied to a single app: aerial wallpaper videos (can be 30 GB), desktop asset downloads, ML caches.

→ [./macos-system-data.md](./macos-system-data.md)

### App Overlap Analysis
Detection of redundant apps in the same category (VPNs, browsers, IDEs). Reports full footprint per app and recommends consolidation.

→ [./app-overlap.md](./app-overlap.md)

### Crash Logs
macOS diagnostic reports and app-specific crash dumps. Inspect before deletion; app-specific crash dumps are safe.

→ [./crash-logs.md](./crash-logs.md)

## Scanning Strategy

1. **Start with user-specified directory or `~` (home)**
2. **Use `find` or `fd` to locate targets**
3. **Calculate sizes with `du -sh`**
4. **Group by category for reporting**
5. **Ask user for confirmation before deleting**

## Common Scan Commands

```bash
# Quick scan of common temp files
find ~ -name ".DS_Store" -o -name "Thumbs.db" -o -name "*.swp"

# Scan all categories (comprehensive)
find ~ -type d \( -name "__pycache__" -o -name "node_modules" -o -name "target" \)
find ~ -type d \( -name ".venv" -o -name "venv" -o -name "env" \)

# Calculate sizes reliably
find ~ -name ".DS_Store" -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'
```

## Cleanability Guide

Vocabulary matches [targets.json](targets.json) (the data source of truth).

| Level | Description | Examples |
|-------|-------------|----------|
| **safe** | Regenerates automatically, no data loss | `.DS_Store`, `__pycache__`, GPUCache |
| **inspect** | May contain useful data; confirm scope with user before deleting | Session history, `.venv`, conversation logs |
| **old-only** | Safe for files older than ~7 days; keep recent | `.claude/debug/`, shell snapshots |
| **never** | Contains critical data or configuration | `.git/`, auth files, main config dirs |
