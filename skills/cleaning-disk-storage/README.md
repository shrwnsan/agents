# cleaning-disk-storage

Agent skill for safe disk cleanup: scan temporary files, caches, and build artifacts; report; confirm; remove **to Trash only** — with regeneration guidance for everything it touches.

## Why

Most disk cleaners are dumb size scanners. This skill encodes judgment: what is safe to delete, what needs inspection (sessions, history, virtualenvs), what must never be touched, and exactly how to regenerate what was removed.

## Install

```bash
npx skills add shrwnsan/agents
```

Installs into `~/.claude/skills/`, `~/.codex/skills/`, `~/.cursor/skills/`, and 70+ other agents via the [skills CLI](https://skills.sh).

## Usage

Ask your agent naturally:

- "I'm running out of disk space, help clean up"
- "Clean up .DS_Store files"
- "How much space would the Rust target dirs free?"

Or run the bundled read-only scanner directly:

```bash
bash skills/cleaning-disk-storage/scripts/scan.sh          # full home (slow)
bash skills/cleaning-disk-storage/scripts/scan.sh ~/Developer   # scoped (fast)
```

## Safety model

| Rule | Detail |
|------|--------|
| Trash, never `rm` | Deletions go to the platform trash (recoverable until emptied) |
| Scan → report → confirm | No deletion before an explicit user yes |
| Thresholds | Items > 100 MB reported individually; > 1 GB warned explicitly |
| Tiered cleanability | `safe` / `inspect` / `old-only` / `never` per target |
| Native cleanup first | `brew cleanup`, `uv cache clean`, `go clean -cache` before blunt directory trashing |
| regeneration notes | Every cleanup summary includes how to restore what was removed |

## Structure

| Path | Contents |
|------|----------|
| `SKILL.md` | Workflow, thresholds, output format, evaluation scenarios |
| `reference/TARGETS.md` | Category index with scanning strategy |
| `reference/targets.json` | Machine-readable target catalog (data source of truth) |
| `reference/GOTCHAS.md` | Operational traps from real runs (Trash-vs-df, sandboxing, BSD/GNU drift) |
| `reference/PLATFORMS.md` | Linux + Windows mappings |
| `reference/REGENERATION.md` | Restore instructions + time estimates |
| `reference/*.md` | Per-category deep-dives (python, nodejs, rust, ai-agents, macOS system data, …) |
| `scripts/scan.sh` | Read-only scanner |

## Platforms

macOS is the primary, fully-covered target. Linux and Windows mappings live in `reference/PLATFORMS.md`.

## Related

- [skills.sh entry](https://skills.sh/shrwnsan/agents) — install telemetry leaderboard
- Companion project pondering a desktop app over the same `targets.json` rules DB (see shrwnsan/napkin `docs/labs/`)
