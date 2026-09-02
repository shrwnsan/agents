# AI Agent Temporary Directories

Temporary files, caches, and session data from AI development tools and IDEs.

## Contents

- [Claude Code](#claude-code)
- [Gemini CLI](#gemini-cli)
- [Windsurf IDE (Codeium)](#windsurf-ide-codeium)
- [Antigravity IDE](#antigravity-ide)
- [Continue (VS Code Extension)](#continue-vs-code-extension)
- [Cursor IDE](#cursor-ide)
- [Factory AI / Droid](#factory-ai--droid)
- [Qwen Code](#qwen-code)
- [Codex (OpenAI)](#codex-openai)
- [Common Patterns](#common-patterns)
- [Total Cleanup Potential](#total-cleanup-potential)

## Claude Code

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.claude/debug/` | Debug logs | Old only |
| `~/.claude/shell-snapshots/` | Shell snapshots | Old only |
| `~/.claude/session-env/` | Session environments | Old only |

### Scanning
```bash
du -sh ~/.claude/debug/ 2>/dev/null
du -sh ~/.claude/shell-snapshots/ 2>/dev/null
du -sh ~/.claude/session-env/ 2>/dev/null
```

---

## Gemini CLI

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.gemini/tmp/` | Temporary session files | Safe |
| `~/.gemini/history/` | Chat history | Inspect first |
| `.gemini-clipboard/` | Clipboard temp files | Safe |

### Scanning
```bash
du -sh ~/.gemini/tmp/ 2>/dev/null
du -sh ~/.gemini/history/ 2>/dev/null
find ~ -name ".gemini-clipboard" -type d -exec du -sh {} + 2>/dev/null
```

### Notes
- `history/` contains conversation history - backup before deleting

---

## Windsurf IDE (Codeium)

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Application Support/Windsurf/GPUCache/` | GPU cache | Safe |
| `~/Library/Application Support/Windsurf/Code Cache/` | JS/WASM cache | Safe |
| `~/Library/Application Support/Windsurf/logs/` | App logs | Inspect first |
| `~/Library/Caches/com.exafunction.windsurf/` | Cache | Safe |
| `~/.codeium/windsurf/cascade/` | AI cascade cache | Safe |

### Scanning
```bash
du -sh ~/Library/Application\ Support/Windsurf/GPUCache/ 2>/dev/null
du -sh ~/Library/Application\ Support/Windsurf/Code\ Cache/ 2>/dev/null
du -sh ~/Library/Caches/com.exafunction.windsurf/ 2>/dev/null
du -sh ~/.codeium/windsurf/cascade/ 2>/dev/null
```

### Notes
- Cascade cache rebuilds on next use (may slow down initially)
- GPU/Code caches regenerate on next launch

---

## Antigravity IDE

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Application Support/Antigravity/GPUCache/` | GPU cache | Safe |
| `~/Library/Application Support/Antigravity/Code Cache/` | JS/WASM cache | Safe |
| `~/Library/Application Support/Antigravity/logs/` | App logs | Inspect first |
| `~/Library/Caches/com.google.antigravity/` | Cache | Safe |

### Scanning
```bash
du -sh ~/Library/Application\ Support/Antigravity/GPUCache/ 2>/dev/null
du -sh ~/Library/Application\ Support/Antigravity/Code\ Cache/ 2>/dev/null
du -sh ~/Library/Caches/com.google.antigravity/ 2>/dev/null
```

---

## Continue (VS Code Extension)

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.continue/sessions/` | Session history | Inspect first |
| `~/.continue/index/` | Code index | Inspect first |

### Scanning
```bash
du -sh ~/.continue/sessions/ 2>/dev/null
du -sh ~/.continue/index/ 2>/dev/null
```

### Notes
- Index rebuilds on next workspace open (may slow down initially)
- Sessions contain conversation history

---

## Cursor IDE

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Application Support/Cursor/GPUCache/` | GPU cache | Safe |
| `~/Library/Application Support/Cursor/Code Cache/` | JS/WASM cache | Safe |

### Scanning
```bash
du -sh ~/Library/Application\ Support/Cursor/GPUCache/ 2>/dev/null
du -sh ~/Library/Application\ Support/Cursor/Code\ Cache/ 2>/dev/null
```

---

## Factory AI / Droid

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.factory/logs/` | Application logs | Safe |
| `~/.factory/sessions/` | Session history | Inspect first |
| `~/.factory/temp/` | Temporary files | Safe |

### Scanning
```bash
du -sh ~/.factory/logs/ 2>/dev/null
du -sh ~/.factory/sessions/ 2>/dev/null
du -sh ~/.factory/temp/ 2>/dev/null
```

---

## Qwen Code

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.qwen/tmp/` | Temporary files | Safe |
| `~/.qwen/todos/` | Task history | Inspect first |

### Scanning
```bash
du -sh ~/.qwen/tmp/ 2>/dev/null
du -sh ~/.qwen/todos/ 2>/dev/null
```

---

## Codex (OpenAI)

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/.codex/log/` | Application logs | Inspect first |
| `~/.codex/sessions/` | Session data | Inspect first |

### Scanning
```bash
du -sh ~/.codex/log/ 2>/dev/null
du -sh ~/.codex/sessions/ 2>/dev/null
```

---

## Common Patterns

### GPU Caches
- Universal across Electron-based IDEs (Windsurf, Antigravity, Cursor)
- Regenerate automatically on next launch
- Typically 50-500 MB per IDE

### Code Caches
- JavaScript and WASM compilation caches
- Safe to delete, regenerate on next launch

### Cascade/Codeium
- AI context indexing cache
- Rebuilds on next use but causes initial slowdown

### Session Directories
- Contain conversation history and context
- Backup before deleting if important

### Logs
- Generally safe to delete
- Inspect first if debugging issues

## Total Cleanup Potential

Typical AI tool cleanup: **2-4 GB**

Largest consumers:
- Windsurf: 2-3 GB
- Gemini CLI: 300-500 MB
- Continue: 100-200 MB
- Antigravity: 300-500 MB
