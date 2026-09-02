# Orphaned Application Data

Data left behind by uninstalled or removed applications. These directories consume storage but serve no purpose since the parent application no longer exists.

## Contents

- [Detection Strategy](#detection-strategy)
- [Common Orphan Patterns](#common-orphan-patterns)
- [Cleanup Commands](#cleanup-commands)
- [Safety Checks](#safety-checks)
- [Typical Sizes](#typical-sizes)

## Detection Strategy

### Automatic Detection
Scan `~/Library/Application Support/` and `~/Library/Caches/` for directories where the corresponding application is no longer installed.

```bash
# Find orphaned Application Support directories
for dir in ~/Library/Application\ Support/*/; do
  app_name=$(basename "$dir")
  # Skip known system/non-app directories
  case "$app_name" in
    com.apple.*|com.google.*|com.microsoft.*) continue ;;
  esac
  # Check if any matching app exists
  if ! mdfind "kMDItemFSName == '*.app'" 2>/dev/null | grep -qi "$app_name"; then
    size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    echo "$size  $app_name"
  fi
done | sort -rh

# Find orphaned Cache directories
for dir in ~/Library/Caches/*/; do
  app_name=$(basename "$dir")
  case "$app_name" in
    com.apple.*|Homebrew) continue ;;
  esac
  if ! mdfind "kMDItemFSName == '*.app'" 2>/dev/null | grep -qi "$app_name"; then
    size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    echo "$size  $app_name"
  fi
done | sort -rh
```

### Manual Verification
Before flagging as orphaned, verify:
1. The app is truly gone (`ls /Applications/`, `brew list --cask`)
2. No LaunchAgent or system extension remains
3. The data isn't shared with another installed app

## Common Orphan Patterns

### Uninstalled IDEs and Editors
| Pattern | Locations | Example |
|---------|-----------|---------|
| Electron-based IDE data | `~/Library/Application Support/{name}/` | Kiro, Windsurf, WebStorm |
| IDE config/cache | `~/.{name}/` | `~/.kiro/`, `~/.vscode-server/` |
| Extension data | `~/.{name}/extensions/` | `~/.antigravity/extensions/` |

### Uninstalled VPN Clients
| Pattern | Locations |
|---------|-----------|
| VPN data | `~/Library/Application Support/com.{vendor}.vpn*/` |
| Network config cache | `~/Library/Caches/com.{vendor}.vpn*/` |
| HTTP storage | `~/Library/HTTPStorages/com.{vendor}.vpn*/` |
| Preferences | `~/Library/Preferences/com.{vendor}.vpn*.plist` |

### ML Model Caches from Uninstalled Tools
| Pattern | Locations | Origin |
|---------|-----------|--------|
| HuggingFace models | `~/Library/Caches/datalab/`, `~/.cache/huggingface/` | Surya OCR, marker-pdf, docling |
| Surya OCR models | `~/Library/Caches/datalab/models/` | marker-pdf dependency |
| ONNX models | `~/.cache/onnx/` | Various ML tools |

#### pipx Cleanup Gap
When uninstalling a pipx tool (`pipx uninstall {tool}`), model caches downloaded by its dependencies are **not** automatically removed. Common culprits:
- `marker-pdf` → leaves Surya OCR models in `~/Library/Caches/datalab/` (~3 GB)
- Document AI tools → leave HuggingFace model caches

## Cleanup Commands

```bash
# Remove orphaned data (verify app is gone first)
trash ~/Library/Application\ Support/{orphan_name}/
trash ~/Library/Caches/{orphan_name}/
trash ~/.{orphan_name}/

# Check for remaining fragments
ls ~/Library/Preferences/*{orphan_name}* 2>/dev/null
ls ~/Library/HTTPStorages/*{orphan_name}* 2>/dev/null
ls ~/Library/LaunchAgents/*{orphan_name}* 2>/dev/null
```

## Safety Checks

Before removing orphaned data:
1. **Check for running processes**: `ps aux | grep -i {name}`
2. **Check LaunchAgents**: `ls ~/Library/LaunchAgents/*{name}*`
3. **Check system extensions**: `ls /Library/LaunchDaemons/*{name}*`
4. **Check Homebrew**: `brew list --cask | grep {name}`
5. **Verify app removal**: `mdfind "kMDItemFSName == '{name}*.app'"`
6. **Check backup-file staleness**: `.bak`-style files (e.g. `data.db.bak`) never regenerate — compare mtimes against the primary file and confirm individually before proposing deletion

## Typical Sizes

- Uninstalled IDE data: 500 MB - 5 GB
- Uninstalled VPN data: 100 MB - 500 MB
- Orphaned ML models: 500 MB - 5 GB
- Browser profile data: 100 MB - 1 GB
