---
name: cleaning-disk-storage
description: Scan for and safely remove temporary files, cache directories, and build artifacts to free disk space. Use when user asks to clean up disk, free storage, remove temp files, mentions running out of space, or needs system maintenance. Includes detection of AI agent temp directories (.gemini-clipboard, antigravity scratch).
---

# Cleaning Disk Storage

## Quick Start

1. Scan for temporary files and report space usage (or run `scripts/scan.sh [root]` — bundled read-only scanner)
2. Confirm with user before deletion
3. Use `trash` command (not `rm -rf`) for safe removal
4. Provide summary with space freed and regeneration instructions

## Purpose

Identify, analyze, and safely remove temporary and cache files to free up storage space. Scans common temp directories, reports space usage, gets confirmation, performs cleanup, and provides comprehensive summary.

## Targets to Scan

Comprehensive reference organized by category. See [reference/TARGETS.md](reference/TARGETS.md) for detailed scanning commands and cleanability information.

### Common Categories

| Category | Typical Size | Reference |
|----------|--------------|-----------|
| Common files (.DS_Store, etc.) | 1-50 MB | [reference/common.md](reference/common.md) |
| Crash logs | 50 MB - 2 GB | [reference/crash-logs.md](reference/crash-logs.md) |
| Python (__pycache__, .venv) | 100 MB - 5 GB | [reference/python.md](reference/python.md) |
| Node.js (node_modules) | 500 MB - 10 GB | [reference/nodejs.md](reference/nodejs.md) |
| Package manager caches | 1-20 GB | [reference/package-managers.md](reference/package-managers.md) |
| AI agent caches | 2-4 GB | [reference/ai-agents.md](reference/ai-agents.md) |
| System caches | 1-30 GB | [reference/cache.md](reference/cache.md) |
| Orphaned application data | 500 MB - 10 GB | [reference/orphaned-data.md](reference/orphaned-data.md) |
| macOS system data | 5-30 GB | [reference/macos-system-data.md](reference/macos-system-data.md) |
| App overlap analysis | 2-15 GB | [reference/app-overlap.md](reference/app-overlap.md) |
| Rust (target/) | 100 MB - 2 GB | [reference/rust.md](reference/rust.md) |
| Build outputs (dist, build) | 50 MB - 2 GB | [reference/build.md](reference/build.md) |
| IDE / Editor | 10-300 MB | [reference/ide.md](reference/ide.md) |

### Quick Scan Commands

```bash
# Common temp files
find ~ -name ".DS_Store" -o -name "Thumbs.db" -o -name "*.swp"

# Python caches
find ~ -type d -name "__pycache__"

# Node dependencies
find ~ -type d -name "node_modules"

# Reliable size calculation (portable — BSD du lacks --files0-from)
find ~ -name ".DS_Store" -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'
```

## Output Format

Structured response with:
1. Scan results with space usage
2. Safety confirmation
3. User confirmation request
4. Cleanup status summary
5. Space freed (before/after/freed)
6. Remaining large directories
7. Regeneration notes
8. Optional follow-up suggestions

## Example Output

```
I found several temporary and cache files that are safe to remove:

• 187 .DS_Store files (macOS metadata) - 2.3MB
• 6,171 __pycache__ directories (Python cache) - ~600MB
• 20 node_modules directories - 5.7GB
• AI agent caches (Windsurf, Gemini, Continue) - ~3GB

These files are safe to delete and can be regenerated when needed.
Would you like me to proceed with deleting these files? (yes/no)

[After user confirms]

Cleanup complete. Freed approximately 9.3GB of space.

For regeneration instructions, see [reference/REGENERATION.md](reference/REGENERATION.md).
```

## Best Practices

- Scan and report space usage before deletion
- Prefer the tool's own cleanup command (`brew cleanup`, `uv cache clean`, `go clean -cache`, `pnpm store prune`) before trashing directories — see [reference/GOTCHAS.md](reference/GOTCHAS.md)
- Clearly indicate which files are safe to delete
- Request explicit user confirmation before performing deletions
- Provide regeneration instructions for important items
- Include comprehensive summary after cleanup
- Suggest additional cleanup opportunities when appropriate
- Keep output informative but concise

## Thresholds

- Report individual items over 100MB
- Group smaller items by category
- Always warn before deleting directories over 1GB

## Regeneration Instructions

See [reference/REGENERATION.md](reference/REGENERATION.md) for comprehensive restore instructions including:
- Python virtual environments
- Node.js dependencies
- Rust/Cargo build artifacts
- AI agent caches and sessions
- Time estimates for restoration

## Evaluation Scenarios

**Scenario 1**: User asks "I'm running out of disk space, help clean up"
- Expected: Scans common directories, reports findings, asks for confirmation

**Scenario 2**: User asks "Clean up .DS_Store files"
- Expected: Targets only .DS_Store files, reports count and space

**Scenario 3**: User confirms cleanup
- Expected: Uses `trash` command, provides before/after summary

**Scenario 4**: User asks to clean specific directory
- Expected: Scans only specified directory, respects scope limitation

## Security Considerations

- Always validate file paths before deletion to prevent accidental removal of important files
- Verify that identified files are indeed temporary/cache files before deletion
- Implement proper error handling for permission issues during file operations
- Log all deletion operations for audit purposes
- Ensure user consent is obtained before any file removal operations

## Implementation Notes

This skill uses progressive disclosure:
- **SKILL.md** (this file): Main instructions and quick reference
- **reference/TARGETS.md**: Comprehensive target reference with scanning commands
- **reference/targets.json**: Machine-readable target catalog (data source of truth for tooling)
- **reference/REGENERATION.md**: Complete restoration instructions
- **reference/GOTCHAS.md**: Operational traps from real runs — read before executing a cleanup
- **reference/PLATFORMS.md**: Linux and Windows mappings
- **reference/**: Detailed references by category (common, python, nodejs, ai-agents, etc.)
- **scripts/scan.sh**: Read-only scanner producing a per-category size report

For detailed scanning of specific categories, refer to the appropriate file in the `reference/` directory.
