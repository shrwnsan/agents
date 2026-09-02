# IDE / Editor

Integrated development environment and editor-specific caches and temporary files.

## Directories

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `.vscode/.cache/` | VS Code cache | Safe |
| `.idea/` | IntelliJ IDEA project files | Inspect first |
| `*.stackdump` | Haxe crash dumps | Safe |

## Scanning Commands

```bash
# Find VS Code cache directories
find ~ -type d -path "*/.vscode/.cache"

# Calculate VS Code cache size
find ~ -type d -path "*/.vscode/.cache" -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'

# Find .idea directories
find ~ -type d -name ".idea"

# Find Haxe crash dumps
find ~ -type f -name "*.stackdump"
```

## Notes

### VS Code (.vscode/.cache/)
- Extension and workspace caches
- Regenerates automatically
- Safe to delete

### IntelliJ IDEA (.idea/)
- Contains project-specific settings and configuration
- May contain run configurations, VCS settings, etc.
- Inspect contents before deleting
- Do not delete if actively using the project

### Haxe (*.stackdump)
- Crash dump files from Haxe compiler
- Safe to delete unless debugging a crash
- Usually small (< 1 MB)

## Typical Sizes

- VS Code cache: 10-100 MB per workspace
- .idea directory: 10-200 MB per project
