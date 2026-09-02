# Common Temporary Files

Platform-agnostic temporary files that accumulate during normal system usage.

## Files

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `.DS_Store` | macOS metadata files | Safe |
| `Thumbs.db` | Windows thumbnail cache | Safe |
| `*.swp`, `*.swo` | Vim swap files | Safe |
| `*~` | Backup files | Safe |
| `.bash_history` | Shell history | Inspect first |
| `.zsh_history` | Zsh history | Inspect first |

## Scanning Commands

```bash
# Find .DS_Store files
find ~ -name ".DS_Store" -type f

# Count .DS_Store files
find ~ -name ".DS_Store" -type f | wc -l

# Calculate .DS_Store total size
find ~ -name ".DS_Store" -type f -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'

# Find Vim swap files
find ~ -name "*.swp" -o -name "*.swo"
```

## Notes

- `.DS_Store` files are recreated automatically by macOS
- Vim swap files can be important if recovery is needed (check if vim sessions are active)
- Shell history files may contain sensitive commands or useful history
