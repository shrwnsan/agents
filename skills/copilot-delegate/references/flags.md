# Copilot CLI flag surface (verified against 1.0.105)

Read from `copilot --help` on CLI 1.0.105 (npm `@github/copilot`, 2026-10-31).
The wrapper only constructs the flags below that say "wrapper uses"—forward
anything else only after re-checking `copilot --help` on the installed pin,
because the surface moves between versions.

## Non-interactive core

| Flag | What it does | Wrapper posture |
|---|---|---|
| `-p, --prompt <text>` | Execute one prompt, exit when done | Always |
| `-s, --silent` | Output only the agent response, no stats | Always |
| `--model <model>` | Pick the model; `auto` lets Copilot choose | Only when `--model` passed; prefer an exact plan-catalog string |
| `-C <directory>` | Change working directory first | Only when `--cwd` passed |
| `--disable-client-telemetry` | Disable the CLI's own telemetry | Always |

## Permissions (the sharp end)

| Flag | What it does | Wrapper posture |
|---|---|---|
| `--allow-all-tools` | Auto-run every tool without confirmation; required before the CLI runs tools in prompt mode (also settable via `COPILOT_ALLOW_ALL`) | Only on explicit `--need-tools`; pair with `sandboxed-run` |
| `--allow-all-paths` | Disable file-path verification, allow any path | Never constructed |
| `--add-dir <dir>` | Grant file access to one more directory (repeatable) | Never constructed; forward by hand only with sandboxing |
| `--disallow-temp-dir` | Withhold automatic temp-directory access | Not used; note for hardened runs |
| `--trust-folder` | Trust the working directory's saved config for one session | Never constructed |

Inference-only delegations (the default) pass none of these—the delegate can
answer but cannot touch files or run commands.

## Session, sharing, memory

| Flag | What it does | Wrapper posture |
|---|---|---|
| `--share [<path>]`, `--share-gist` | Write the session transcript to disk or a secret gist | Never constructed—transcripts can carry the prompt |
| `--enable-memory` | Turn on memory in prompt mode (off by default) | Never constructed |
| `-r, --resume [<id>]`, `--continue`, `--session-id <id>`, `--connect` | Resume or attach to sessions | Out of scope; one-shot only |
| `--fleet` | Parallel subagent orchestration | Out of scope |

## Other surfaces worth knowing

- `--output-format json` emits JSONL events—useful for tooling that wants the
  full event stream; the wrapper sticks to the plain-text JSON contract
  instead, which is stable across CLI versions.
- `--attachment <path>` (repeatable) attaches files to the prompt; an egress
  decision a human should make, not the wrapper.
- `--disable-builtin-mcps` / `--disable-mcp-server <name>` / 
  `--enable-all-github-mcp-tools` shape which MCP servers the delegate can
  reach; the wrapper leaves the CLI defaults alone.
- `copilot skill`, `copilot mcp`, `copilot sandbox` are the CLI's own
  management subcommands—`copilot skill` is how this and other SKILL.md
  packages get installed for Copilot-side use.

## Traps observed in third-party material

Some community skills document `--allow-tool <name>`, `--allow-all-urls`, and
`--yolo`. None exist in 1.0.105—copying those flags into scripts produces a
CLI argument error at best and a false sense of granular permissions at
worst. The only tool permission switch in 1.0.105 is the all-or-nothing
`--allow-all-tools`, which is exactly why the default here is inference-only.
