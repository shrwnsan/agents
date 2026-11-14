# Gotchas

Operational traps collected from real cleanup runs. Read before executing any cleanup.

## Contents

- [Trash does not free space until emptied](#trash-does-not-free-space-until-emptied)
- [The trash CLI destroys or mis-handles bare dotfiles](#the-trash-cli-destroys-or-mis-handles-bare-dotfiles)
- [Sandboxed agents cannot write to user directories](#sandboxed-agents-cannot-write-to-user-directories)
- [Root-owned files masquerade as TCC denials](#root-owned-files-masquerade-as-tcc-denials)
- [Docker volumes: inspect before prune](#docker-volumes-inspect-before-prune)
- [TCC-protected directories are silently unscanned](#tcc-protected-directories-are-silently-unscanned)
- [BSD vs GNU du flag drift](#bsd-vs-gnu-du-flag-drift)
- [Sparse files and ls-vs-du mismatches](#sparse-files-and-ls-vs-du-mismatches)
- [Live apps rebuild caches instantly](#live-apps-rebuild-caches-instantly)
- [Git worktrees duplicate build directories](#git-worktrees-duplicate-build-directories)
- [Prefer the tool's own cleanup command](#prefer-the-tools-own-cleanup-command)
- [Content-addressed stores need two-signal orphan sweeps](#content-addressed-stores-need-two-signal-orphan-sweeps)
- [Tool stdout totals are not freed space](#tool-stdout-totals-are-not-freed-space)
- [System assets that must never be deleted](#system-assets-that-must-never-be-deleted)
- [The manifest is the audit trail](#the-manifest-is-the-audit-trail)
- [Process listing may be unavailable](#process-listing-may-be-unavailable)

---

## Trash does not free space until emptied

On macOS, the Trash lives on the same volume as the files it holds. Moving items to Trash **renames** them — `df` does not change until the user empties Trash.

- Observed: ~39 GB moved to Trash, `df` moved only the ~2.5 GB of tool-native deletes.
- Never report "space freed" from a `df` delta alone when using trash. Track the manifest total instead.
- Tell the user explicitly: "X GB is recoverable in Trash until emptied."

## The trash CLI destroys or mis-handles bare dotfiles

`/usr/bin/trash` on Darwin 27 does not reliably move dot-named files to the Trash. The failure mode is destruction, not a skip.

- Observed (differential repro, twice, with readable `~/.Trash`): trashing a `.DS_Store` printed `fnfErr "The file .DS_Store doesn't exist"` + exit 5; the source file was gone AND the item was absent from Trash, with Trash metadata untouched. Non-dotfile items in the same run landed in Trash normally.
- Other runs saw exit 0 with the dotfile gone, landing unverifiable. Either way, **the recovery guarantee is void for bare dotfiles**; treat the CLI result as "may have been permanently deleted".
- Root cause is the CLI's handling of dot-named arguments, not agent error. A skill-following agent using only documented commands still hits it; this falsified an eval (beh-003) before it was understood.
- **Workarounds (both verified):**
  - Stage into a non-dot-named directory, then trash the directory: directory trashing demonstrably lands in Trash, and the dotfile rides inside it. `trash -v <dir>` prints the destination path, which is supplementary self-report evidence.
  - `osascript -e 'tell application "Finder" to delete POSIX file "<path>"'`. Finder prints the `.Trash` destination URL, so recoverability is self-verifying even from shells that cannot read `~/.Trash`.
- **Ordering matters: the sibling sweep.** Trashing *any* sibling (directory or plain file, no dotfile argument involved) silently deletes the parent directory's `.DS_Store`: exit 0, no error, unrecoverable. Verified in isolation twice; `.hidden` survives, so the sweep is strictly `.DS_Store`-specific (likely Finder-owned metadata pruning). Stage or Finder-delete `.DS_Store` **before** any other trash call in that parent, or accept the loss and disclose it (`.DS_Store` is Finder view-state, regenerated on next visit).
- **Trash name collisions rename, not destroy.** In a quiet environment, trashing a second item with the same basename as an existing Trash entry appends a timestamp (`name HH-MM-SS-mmm`), and both remain recoverable. An eval run under six concurrent agents sharing `~/.Trash` did observe a same-name destroy, but it did not reproduce in isolation. Treat concurrent Trash traffic as a hazard, and use unique names for anything whose recoverability you will later assert.
- **Verifying Trash landings when `~/.Trash` is TCC-denied.** Bare `ls ~/.Trash` fails with EPERM, but direct-path access works: `stat`/`ls` a specific expected path (e.g. `~/.Trash/<staging-name>/...`), and/or use the osascript/Finder routes above whose output self-verifies.
- Applies to the `.DS_Store` sweeps this skill recommends. Do not pipe scanner output for dotfiles straight into `trash`; stage or use Finder delete, and stage first.

## Sandboxed agents cannot write to user directories

Agent harnesses (Claude Code, Codex, etc.) often run commands in a sandbox that denies writes outside an allowlist — typically blocking `~/.cache`, `~/Library/Caches`, `~/Developer` — and may also block process listing (`pgrep`, `ps`).

- Probe before planning: `touch <target>/.cleanup-probe && rm <target>/.cleanup-probe`. But the probe is itself a mutation. In plan-only / dry-run phases (where the user asked for no changes), use the read-only `[ -w <dir> ]` test instead and save the probe for when deletion is authorized and imminent.
- If writes are denied, do not retry blindly. Hand the user a ready-to-run cleanup script — but note that in-session execution (e.g. the `!` prefix in Claude Code) **inherits the session sandbox and fails identically**. The reliable routes: the user runs the script in a real terminal, or disables the sandbox for the session so the agent can execute it directly with output landing in the conversation.
- Per-user instruction policy may also require `trash` over `rm -rf`; both fail identically under sandbox denies since the move target (`~/.Trash`) is also blocked.

## Root-owned files masquerade as TCC denials

`afpAccessDenied` on `trash`/`mv` is not always TCC or App Management. It is often plain POSIX ownership. Privileged helpers (NordVPN's daemon, for one) write `root:staff 600` files *inside user Library dirs*, and nothing running as the user can move them, GUI quit or not.

- Observed: NordVPN `ng/web_protection/data.db.bak{,.copy}` (~2 GB each) owned `root:staff`; `trash` and `mv` both denied before and after the app quit.
- Check `ls -l` **before** blaming TCC or retrying, because ownership is the diagnosis.
- Routes: `sudo rm` in a real terminal, or Finder delete with the admin-password prompt.
- Claude Code's `!` prefix does not allocate a TTY, so `sudo` there dies with "a terminal is required to read the password". Never collect the password in-chat; hand the user the command for their own terminal.

## Docker volumes: inspect before prune

Docker volumes are the one prune target where "reclaimable" can mean "user database". Inspect, then delete individually.

- **Order matters**: run volume inspection *before* `docker image prune -a`, because pruning can delete the only image you would have used to look inside a volume (observed: alpine gone post-prune, postgres survived by luck).
- `docker system df -v` gives per-volume sizes; `LINKS > 0` means a container references the volume, so never prune those.
- Compose-created volumes carry labels; empty labels = anonymous: `docker volume inspect <v> --format '{{index .Labels "com.docker.compose.project"}}'`
- Peek inside read-only with a surviving image: `docker run --rm -v <vol>:/v:ro postgres:17-alpine ls /v`
- `docker volume prune` only removes *anonymous* volumes; named orphans need explicit `docker volume rm`.
- Deleting hash-named volumes in one bulk `rm` is data-loss-prone and gets denied by auto-mode permission classifiers. Guard each deletion with an inline content check and delete only on match:
  `docker run --rm -v <vol>:/v:ro <img> sh -c 'test -d /v/@babel'` → `docker volume rm <vol>`; print SKIP when the guard fails.

## TCC-protected directories are silently unscanned

Full-home `find`/`du` skip macOS TCC-gated dirs (`~/Downloads`, `~/Documents`, `~/Desktop`) without error when stderr is suppressed, which the size-summing pipelines in this skill do by design.

- Observed: `du -sh ~/Downloads` printed nothing, and the follow-up find reported "no old installers". That conclusion came from a directory that was never readable.
- Never present a TCC dir as scanned-clean. List it as **unscanned** and let the user check it themselves (or grant the harness access deliberately; do not prompt them to blanket-grant).

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

## Content-addressed stores need two-signal orphan sweeps

Content-addressed caches (Hugging Face hub blobs, git objects, pnpm's store) keep payload bytes in a global store; visible folders hold symlinks into it, and each payload carries bookkeeping sidecars (`.refs`, `.lock`) plus store dotfiles.

- A naive "unreferenced means orphan" diff flags the sidecars and marker files of live payloads as junk. Deleting those corrupts bookkeeping for models still in use. Orphan candidates are payload files only: exclude dotfiles and sidecars, and require a second signal (stale `.refs` entries) before classifying anything.
- Compute the referenced set by resolving every symlink under the cache root. This protects by resolution: anything any project, tool, or concurrent process points at is safe, including entries added after the scan started. Hardcoded protected-name lists go stale.
- Re-scan immediately before deletion. Caches churn while you work; a plan computed minutes ago can already be wrong. Abort if any candidate became referenced between scan and execute, or if the plan differs from an independent recomputation.
- Structural gates beat magnitude gates. "Only reclaim if the orphan set exceeds N GB" fails when the number goes stale between scan and execute; require the plan and an independently coded recomputation to match exactly instead.
- `huggingface-cli delete-cache` cannot see store orphans (it operates per visible repo, and the command itself is deprecated). No vendor cleaner covers this yet.

The full layout, algorithm, and verification steps live in [content-addressed-stores.md](content-addressed-stores.md).

## Tool stdout totals are not freed space

Native tools report what *they* processed, not what the disk gained, and concurrent batches blur attribution further. `docker builder prune` printed `Total: 20.21GB` (scanned, not reclaimed) while the same batch's `df` delta was 24.5 GB once brew/npm/uv contributions mixed in.

- Take a `df -k` baseline immediately before and after each native batch; report `df` as truth and tool stdout as detail.
- Never sum tool-reported "freed" numbers and present the sum as space freed.

## System assets that must never be deleted

- `/Library/Application Support/com.apple.idleassetsd/` — system-level aerial wallpaper assets. The user-level `~/Library/Application Support/com.apple.wallpaper/aerials/` is safe; the system path is not.
- `~/Library/Application Support/com.apple.ProtectedCloudStorage/` — iCloud protected data. Never touch.

## The manifest is the audit trail

Real cleanups rarely end at the first confirmation. The user quits an app and asks for its cache next, picks extra Docker work, or deletes one blocked item manually. Record every one of these in the **same** manifest file created at the start (pre-delete `du -sk` per path), as dated addendum lines, not in a fresh file and not only in chat.

- The manifest is what makes "what exactly did we delete?" answerable weeks later, including items the agent did not delete itself.
- Mark manually-resolved items (user ran sudo, Finder) as such in the addendum.

## Process listing may be unavailable

`pgrep`/`ps` can be denied in sandboxed shells (macOS sysmon) and behave differently across platforms (`pgrep -x` is exact-match on macOS).

- Treat "is the app running?" as unknown when listing fails; phrase app-cache warnings accordingly ("if X is running, quit and relaunch it after cleanup").
