# Platform Notes

The skill was authored on macOS and treats macOS as the primary target. This file maps the same categories onto Linux and Windows. Deletion policy is identical everywhere: move to Trash, never `rm`/`Remove-Item` for bulk cleanup.

## Contents

- [macOS (primary)](#macos-primary)
- [Linux](#linux)
- [Windows](#windows)

---

## macOS (primary)

- Trash: built-in `/usr/bin/trash` (moves to `~/.Trash`, recoverable).
- Per-category paths: see the category reference files (`reference/*.md`).
- Extra categories unique to macOS: `macos-system-data.md`, `app-overlap.md`.

## Linux

### Trash

No system `trash` binary by default. Use, in order of preference:

1. `gio trash <path>` (GNOME/GLib — present on most desktop distros)
2. `trash-put <path>` (from the `trash-cli` package; follows the FreeDesktop Trash spec)
3. If neither exists, install `trash-cli` — do **not** fall back to `rm -rf` for bulk cleanup

### Category mapping

| Category | macOS | Linux |
|----------|-------|-------|
| User cache | `~/Library/Caches` | `~/.cache` (includes most of it), `~/.local/state` |
| App logs | `~/Library/Logs` | `~/.local/state/*/log`, journal |
| Package caches | Homebrew, `~/Library/Caches/Homebrew` | see below |
| Crash logs | `~/Library/Logs/DiagnosticReports` | `/var/crash`, `journalctl --list-boots` artifacts |
| App data | `~/Library/Application Support` | `~/.local/share`, `~/.config` |

### Native cleanup commands

```bash
# Journal (can reach tens of GB)
sudo journalctl --vacuum-size=200M

# Distro package caches
sudo apt clean                 # Debian/Ubuntu
sudo dnf clean all             # Fedora
sudo pacman -Sc                # Arch (pacman -Scc clears all)

# Universal runtimes (same as macOS)
uv cache clean; pip cache purge; go clean -cache
npm cache clean --force; pnpm store prune
brew cleanup --prune=all       # Linuxbrew
```

### Flatpak / Snap

```bash
flatpak uninstall --unused                 # unused runtimes
sudo snap set system refresh.retain=2      # keep only 2 old revisions
```

## Windows

### Trash

PowerShell can send items to the Recycle Bin via the Visual Basic assembly:

```powershell
Add-Type -AssemblyName Microsoft.VisualBasic
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($path, 'OnlyErrorDialogs', 'SendToRecycleBin')
```

Do not use `Remove-Item -Recurse` for bulk cleanup — it is `rm -rf` and bypasses the Recycle Bin.

### Category mapping

| Category | Windows |
|----------|---------|
| User temp | `%LOCALAPPDATA%\Temp`, `%TEMP%` |
| Package caches | same runtimes: `pip cache purge`, `uv cache clean`, `go clean -cache`, `npm cache clean --force` |
| Browser/dev caches | `%LOCALAPPDATA%\<Vendor>\<App>\Cache` |
| Crash logs | `%LOCALAPPDATA%\CrashDumps`, Event Viewer archives |
| Old installers | `%LOCALAPPDATA%\Package Cache` (inspect first) |

### Do not delete manually

- `C:\Windows\WinSxS` — component store. Only via `Dism.exe /Online /Cleanup-Image /StartComponentCleanup`.
- `C:\Windows\Installer` — removing MSI/MSP files breaks uninstall/repair.
- `pagefile.sys`, `hiberfil.sys` — managed by Windows; change via system settings if needed.
