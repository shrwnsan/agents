# Build Outputs

General build artifacts and compiled outputs across various languages and build systems.

## Directories

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `dist/` | Distribution build output | Safe |
| `build/` | General build output | Safe |
| `out/` | Output directory | Safe |
| `.build/` | SwiftPM build output (macOS) | Safe |

## Object Files

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `*.o` | Object files | Safe |
| `*.a` | Static libraries | Safe |
| `*.so` | Shared libraries (Unix) | Safe |
| `*.dll` | Dynamic libraries (Windows) | Safe |
| `*.exe` | Executables (Windows) | Safe |

## Go

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `*.test` | Test binaries | Safe |
| `*.prof` | Profiling files | Inspect first |

## Scanning Commands

```bash
# Find build output directories
find ~ -type d \( -name "dist" -o -name "build" -o -name "out" \)

# Calculate build directory total size
find ~ -type d \( -name "dist" -o -name "build" -o -name "out" \) -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'

# Find object files
find ~ -type f \( -name "*.o" -o -name "*.a" -o -name "*.so" \)

# Find Go test binaries
find ~ -type f -name "*.test"

# Find Go profiling files
find ~ -type f -name "*.prof"
```

## Notes

- Build outputs regenerate when running build commands
- Common build commands: `npm run build`, `cargo build --release`, `make`, `./configure && make`
- Go test binaries regenerate with `go test`
- Profiling files (`*.prof`) may be needed for performance analysis

## Typical Sizes

- JavaScript build output: 10-100 MB
- Rust release build: 200 MB-2 GB
- C/C++ build output: 50-500 MB
