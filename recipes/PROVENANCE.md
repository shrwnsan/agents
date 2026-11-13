# Recipe provenance

Recipes synced from upstream are read-only mirrors: the [sync-upstream
workflow](../.github/workflows/sync-upstream.yml) copies them from the source
repo and local edits would be overwritten on the next run. This file records
where each copy came from; per-run pins live in
[.upstream-manifest.json](../.upstream-manifest.json) (`commit` is upstream
repo HEAD at clone time, `source_commit` is the last commit that touched the
synced source).

| Recipe | Upstream | First vendored | Status |
|---|---|---|---|
| [agent-voice.md](agent-voice.md) | [garrytan/gbrain](https://github.com/garrytan/gbrain) `recipes/agent-voice.md` | 2026-11-13 | Active upstream |
| [listening-post.md](listening-post.md) | maintained in this repo | — | Not synced |
| [model-bakeoff-gate/](model-bakeoff-gate/) | maintained in this repo | — | Not synced |
| [ngrok-tunnel.md](ngrok-tunnel.md) | [garrytan/gbrain](https://github.com/garrytan/gbrain) `recipes/ngrok-tunnel.md` | 2026-11-13 | Active upstream |
| [twilio-voice-brain.md](twilio-voice-brain.md) | [garrytan/gbrain](https://github.com/garrytan/gbrain) `recipes/twilio-voice-brain.md` | 2026-04-13 | **Deprecated upstream** (frozen 2026-05-23 in v0.40.0.0; successor is `agent-voice`; upstream plans removal) |

## twilio-voice-brain removal policy

Upstream has announced the file will be deleted in a future release. When a
sync run reports it missing:

1. Remove its entry from [.upstream.yml](../.upstream.yml) (the workflow fails
   the run otherwise).
2. Keep the local copy as an archived redirect, updating its status row above
   to "archived (upstream removed)".
3. Point the README entry at `agent-voice` only.
