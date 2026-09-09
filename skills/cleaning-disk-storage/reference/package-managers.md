# Package Manager Caches

Downloaded packages, build caches, and test runner binaries managed by language-specific package managers.

## Contents

- [Homebrew](#homebrew)
- [pip (Python)](#pip-python)
- [go](#go)
- [Playwright](#playwright)
- [pnpm](#pnpm)
- [Notes](#notes)

## Homebrew

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Caches/Homebrew/` | Downloaded bottles, source tarballs, cask DMGs | Safe |

### Scanning
```bash
du -sh ~/Library/Caches/Homebrew/
du -sh ~/Library/Caches/Homebrew/* | sort -rh | head -20
```

### Cleanup
```bash
brew cleanup --prune=all
```

### Typical Sizes
- 5-20 GB depending on install history and update frequency

---

## pip (Python)

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Caches/pip/` | Downloaded wheels and source distributions | Safe |

### Scanning
```bash
du -sh ~/Library/Caches/pip/
pip cache info
```

### Cleanup
```bash
pip cache purge
```

### Typical Sizes
- 200 MB - 2 GB

---

## go

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Caches/go-build/` | Compiled package cache | Safe |

### Scanning
```bash
du -sh ~/Library/Caches/go-build/
go env GOCACHE
```

### Cleanup
```bash
go clean -cache
```

### Typical Sizes
- 200 MB - 2 GB

---

## Playwright

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Caches/ms-playwright/` | Browser binaries (Node.js) | Safe |
| `~/Library/Caches/ms-playwright-go/` | Browser binaries (Go) | Safe |

### Scanning
```bash
du -sh ~/Library/Caches/ms-playwright/
du -sh ~/Library/Caches/ms-playwright-go/
```

### Cleanup
```bash
# Node.js
npx playwright uninstall --all

# Or directly
trash ~/Library/Caches/ms-playwright/
trash ~/Library/Caches/ms-playwright-go/
```

### Regeneration
```bash
npx playwright install
```

### Typical Sizes
- 500 MB - 2 GB (includes Chromium, Firefox, WebKit)

---

## pnpm

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/pnpm/` | Content-addressable store | Inspect first |
| `~/Library/Caches/pnpm/` | Package cache | Safe |

### Scanning
```bash
du -sh ~/Library/pnpm/
du -sh ~/Library/Caches/pnpm/
```

### Cleanup
```bash
pnpm store prune
```

### Typical Sizes
- 200 MB - 1 GB

---

## Notes

- All caches are safe to delete and regenerate on demand
- Initial runs after cleanup may be slower as packages re-download
- Homebrew cache is often the single largest cache on macOS development machines
- Playwright re-downloads all browser engines (~1 GB) on `npx playwright install`
- pnpm store prune only removes unreferenced packages, not active dependencies
