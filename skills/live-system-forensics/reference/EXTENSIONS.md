# IDE Extension Analysis Reference

## Target IDEs

### Antigravity IDE
```bash
ls -la ~/.antigravity/
ls -la ~/.antigravity/extensions/
cat ~/.antigravity/extensions/extensions.json
```

### Windsurf (Codeium)
```bash
ls -la ~/.codeium/windsurf/
ls -la ~/.codeium/windsurf/extensions/
```

### Continue
```bash
ls -la ~/.continue/
```

### Cursor
```bash
ls -la ~/.cursor/
ls -la ~/.cursor/extensions/
```

### Claude Code
```bash
ls -la ~/.claude/
```

## Analyzing VSIX Extensions

### Extension Structure
```
extension-name/
├── .vsixmanifest
├── package.json
├── out/
├── node_modules/
└── assets/
```

### Key Files to Review

**package.json** - Check:
- author, publisher
- dependencies (suspicious packages?)
- scripts (network calls, file operations?)
- activationEvents (what triggers it)

**main.js / out/main.js** - Look for:
- Network requests
- File system access
- Child process spawns

### Classifying Extensions

Known-good extensions are **host-specific** — see the per-host `ALLOWLIST.md` in this directory. For anything not allowlisted, check `package.json` publisher against the official marketplace listing before trusting (publisher-ID typosquatting is a known attack).

## MCP Server Analysis

MCP (Model Context Protocol) servers are increasingly common in AI IDEs:

```bash
# Find MCP servers (pgrep -f matches full command lines, catching IDE subprocesses)
pgrep -fl mcp
ls -la ~/.antigravity/extensions/*/out/mcp-server*
```

### MCP Server Red Flags
- MCP servers from unknown publishers
- Servers making unexpected network calls
- Servers with excessive file system access

## Quick Audit Script

```bash
echo "=== Antigravity Extensions ==="
ls -la ~/.antigravity/extensions/ 2>/dev/null

echo "=== Extension Details ==="
for ext in ~/.antigravity/extensions/*/; do
    echo "--- $(basename "$ext") ---"
    cat "$ext/package.json" 2>/dev/null | grep -E '"(name|author|publisher|version)"' | head -5
done

echo "=== Running MCP Servers ==="
ps auxww | grep -i mcp | grep -v grep
```
