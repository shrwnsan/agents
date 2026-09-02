# Node.js / JavaScript

Node.js-specific dependencies, caches, and build outputs.

## Directories

| Pattern | Description | Cleanability |
|---------|-------------|--------------|
| `node_modules/` | NPM dependencies | Inspect first |
| `.npm/` | NPM cache | Safe |
| `.yarn/` | Yarn cache | Safe |
| `*.log` | NPM logs | Safe |
| `.next/` | Next.js build output | Safe |
| `.nuxt/` | Nuxt.js build output | Safe |
| `.turbo/` | Turbopack cache | Safe |

## Scanning Commands

```bash
# Find node_modules directories
find ~ -type d -name "node_modules"

# Count node_modules directories
find ~ -type d -name "node_modules" | wc -l

# Calculate node_modules total size
find ~ -type d -name "node_modules" -print0 2>/dev/null | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f MB\n", s/1024}'

# Find .next build directories
find ~ -type d -name ".next"

# Check npm cache size
du -sh ~/.npm/ 2>/dev/null

# Check yarn cache size
du -sh ~/.yarn/ 2>/dev/null
```

## Notes

- `node_modules` can be restored with `npm install` or `yarn install`
- Very large sizes are common (500MB-2GB per project)
- Active projects need their node_modules
- Archived/inactive projects are good candidates for cleanup
- `.next/` and `.nuxt/` regenerate when running `npm run build` or `npm run dev`

## Typical Sizes

- Small project node_modules: 50-200 MB
- Medium project node_modules: 200-500 MB
- Large project node_modules: 500MB-2 GB
- .next build output: 50-500 MB
