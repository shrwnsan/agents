# Cache Directories

System and application cache directories that can accumulate significant storage over time.

## Directories

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.cache/` | User cache (XDG standard) | Inspect first |
| `~/.cargo/registry/cache/` | Cargo registry cache | Safe |
| `~/.rustup/` | Rust toolchain | Inspect first |
| `~/.npm/` | NPM cache | Safe |
| `~/.yarn/cache/` | Yarn cache | Safe |
| `~/Library/Caches/` | macOS application caches | Inspect first |
| `~/.thumbnails/` | Image thumbnails | Safe |

## Scanning Commands

```bash
# Check main cache directory
du -sh ~/.cache/ 2>/dev/null

# Check Cargo registry cache
du -sh ~/.cargo/registry/cache/ 2>/dev/null

# Check Rustup toolchain
du -sh ~/.rustup/ 2>/dev/null

# Check NPM cache
du -sh ~/.npm/ 2>/dev/null

# Check Yarn cache
du -sh ~/.yarn/cache/ 2>/dev/null

# Check macOS Library Caches
du -sh ~/Library/Caches/ 2>/dev/null

# Check thumbnails cache
du -sh ~/.thumbnails/ 2>/dev/null

# Find large cache subdirectories
du -sh ~/.cache/* 2>/dev/null | sort -hr | head -20
```

## Related

Package manager caches (Homebrew, pip, go, Playwright, pnpm) are covered in [package-managers.md](package-managers.md).

## Notes

### ~/.cache/
- Contains cached data for many Linux/Unix applications
- May contain important offline data
- Inspect contents before deleting

### ~/.cargo/registry/cache/
- Downloaded Rust crates
- Regenerated on demand when building
- Safe to delete but may slow down subsequent builds

### ~/.rustup/
- Installed Rust toolchains
- Only delete if you don't need those specific Rust versions
- Reinstalling toolchains can be slow

### ~/Library/Caches/
- macOS application caches
- Can be very large (several GB)
- Many apps regenerate automatically
- Some apps may store important data here

### ~/.thumbnails/
- Generated image thumbnails
- Regenerated automatically by file managers

## Typical Sizes

- ~/.cache/: 500 MB - 5 GB
- ~/.cargo/registry/cache/: 100-500 MB
- ~/Library/Caches/: 5-30 GB
- ~/.npm/: 200 MB - 2 GB
