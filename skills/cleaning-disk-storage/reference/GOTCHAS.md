# Gotchas

Operational traps collected from real cleanup runs. Read before executing any cleanup.

## Contents

- [Trash does not free space until emptied](#trash-does-not-free-space-until-emptied)
- [Sandboxed agents cannot write to user directories](#sandboxed-agents-cannot-write-to-user-directories)
- [BSD vs GNU du flag drift](#bsd-vs-gnu-du-flag-drift)
- [Sparse files and ls-vs-du mismatches](#sparse-files-and-ls-vs-du-mismatches)
- [Live apps rebuild caches instantly](#live-apps-rebuild-caches-instantly)
- [Git worktrees duplicate build directories](#git-worktrees-duplicate-build-directories)
- [Prefer the tool's own cleanup command](#prefer-the-tools-own-cleanup-command)
- [System assets that must never be deleted](#system-assets-that-must-never-be-deleted)
- [Process listing may be unavailable](#process-listing-may-be-unavailable)

---

## Trash does not free space until emptied

On macOS, the Trash lives on the same volume as the files it holds. Moving items to Trash **renames** them — `df` does not change until the user empties Trash.

- Observed: ~39 GB moved to Trash, `df` moved only the ~2.5 GB of tool-native deletes.
- Never report "space freed" from a `df` delta alone when using trash. Track the manifest total instead.
- Tell the user explicitly: "X GB is recoverable in Trash until emptied."

## Sandboxed agents cannot write to user directories

Agent harnesses (Claude Code, Codex, etc.) often run commands in a sandbox that denies writes outside an allowlist — typically blocking `~/.cache`, `~/Library/Caches`, `~/Developer` — and may also block process listing (`pgrep`, `ps`).

- Probe before planning: `touch <target>/.cleanup-probe && rm <target>/.cleanup-probe`.
- If writes are denied, do not retry blindly. Either hand the user a ready-to-run cleanup script (e.g. `! bash /tmp/cleanup.sh` so output lands in the session) or ask them to adjust sandbox settings.
- Per-user instruction policy may also require `trash` over `rm -rf`; both fail identically under sandbox denies since the move target (`~/.Trash`) is also blocked.

## BSD vs GNU du flag drift

`du --files0-from=-` is GNU coreutils only; macOS BSD du fails silently in pipelines.

- Portable size sums: `find ... -print0 | xargs -0 du -sk 2>/dev/null | awk '{s+=$1} END {printf "%.1f GB\n", s/1048576}'`
- `xargs -0` handles paths with spaces; avoid newline-delimited lists for any real volume of files.

## Sparse files and ls-vs-du mismatches

`ls -l` reports apparent size; `du` reports actual blocks. Sparse disk images and APFS-cloned files can show 60G in Finder but 5G in `du`.

- Always quote `du` numbers in reports.
- If a user expects ls-sized savings, flag the gap before deleting — deleting a sparse image frees blocks, not apparent size.

## Live apps rebuild caches instantly

Deleting an app's cache while the app is running makes the directory reappear immediately (observed: browser cache rebuilt to 17 MB within a minute of deletion).

- Ask the user to quit the target apps before cleanup if accurate before/after numbers matter.
- Either way the cache regrows during use — set expectations.

## Git worktrees duplicate build directories

Each `git worktree` checkout gets its own `node_modules`, `.venv`, and build outputs. Cleaning the main checkout does not touch `.worktrees/` or `.claude/worktrees/` (observed: 463 MB of `node_modules` in a single feature worktree).

- Scan worktree roots explicitly: `find ~/Developer -maxdepth 4 -type d -name node_modules -path "*.worktrees*"`
- Worktree build dirs are as regenerable as main-checkout ones — include them.

## Prefer the tool's own cleanup command

Package managers know what is stale; blunt directory trashing does not.

| Manager | Command |
|---------|---------|
| Homebrew | `brew cleanup --prune=all` |
| uv | `uv cache clean` |
| pip | `pip cache purge` |
| go | `go clean -cache` |
| pnpm | `pnpm store prune` |
| Docker | `docker system prune` |

Use directory trashing as the fallback when no native command exists.

## System assets that must never be deleted

- `/Library/Application Support/com.apple.idleassetsd/` — system-level aerial wallpaper assets. The user-level `~/Library/Application Support/com.apple.wallpaper/aerials/` is safe; the system path is not.
- `~/Library/Application Support/com.apple.ProtectedCloudStorage/` — iCloud protected data. Never touch.

## Process listing may be unavailable

`pgrep`/`ps` can be denied in sandboxed shells (macOS sysmon) and behave differently across platforms (`pgrep -x` is exact-match on macOS).

- Treat "is the app running?" as unknown when listing fails; phrase app-cache warnings accordingly ("if X is running, quit and relaunch it after cleanup").
