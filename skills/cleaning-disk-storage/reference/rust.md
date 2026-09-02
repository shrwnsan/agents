# Rust / Cargo

Rust-specific build artifacts and toolchain files.

## Directories

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `target/` | Build artifacts | Safe |
| `Cargo.lock` | Dependency lock file | Inspect first |

## Scanning Commands

```bash
# Find target directories
find ~ -type d -name "target"

# Count target directories
find ~ -type d -name "target" | wc -l

# Calculate target total size
find ~ -type d -name "target" -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'

# Check Cargo registry cache
du -sh ~/.cargo/registry/cache/ 2>/dev/null

# Check Rustup toolchain size
du -sh ~/.rustup/ 2>/dev/null
```

## Notes

- `target/` contains compiled binaries and intermediate build artifacts
- Validate build markers before trashing a `target/` directory (`CACHEDIR.TAG`, `.rustc_info.json`, `debug/`, or `release/` present) — non-Rust projects can have lookalike source directories
- Regenerated with `cargo build` or `cargo build --release`
- `Cargo.lock` should typically be kept (ensures consistent dependencies)
- `~/.cargo/registry/cache/` contains downloaded crate archives
- `~/.rustup/` contains installed toolchains (be careful deleting)

## Typical Sizes

- Debug build target: 100-500 MB
- Release build target: 200 MB-2 GB
- Cargo registry cache: 100-500 MB
