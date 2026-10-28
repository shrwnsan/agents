---
name: uptime-kuma-ops
license: Apache-2.0
compatibility: Requires python3, python-socketio==5.13.0 and websocket-client>=0.58 (writes only), plus network access to the configured Kuma host; reads work with urllib alone.
metadata:
  author: shrwnsan
  version: "0.1.0"
description: "Automate Uptime Kuma 2.x: monitor CRUD, push dead-man's-switch monitors, heartbeats, status/SSL reads. Use when the user mentions Uptime Kuma, wants monitors automated, or debugs Kuma errors (SQLITE columns, pushToken missing)."
---

# Uptime Kuma Ops

Automate Uptime Kuma 2.x (battle-tested on 2.5.3) without the web UI. Two surfaces:
the **metrics endpoint** (reads, API key) and **socket.io** (writes, username/password).
Version-pinned gotchas live in [references/quirks-2.5.md](references/quirks-2.5.md) —
read it before any `add`/`editMonitor` operation.

## Configuration (opt-in)

Fleet-agnostic: with no config, run against any Kuma with per-invocation flags —
nothing is persisted. For standing use, create `~/.agents/uptime-kuma-config.json` from
the shipped [uptime-kuma-config.example.json](uptime-kuma-config.example.json) (template also printed by
`python3 scripts/kuma.py init`). It names secret sources (env-file paths + key
names) without containing them; values resolve at runtime and are never printed,
logged, or written anywhere except the configured push-env file's `PUSH_<NAME>`
lines. Full key reference: [references/config.md](references/config.md).

```bash
python3 scripts/kuma.py init            # writes template to stdout; save as:
# ~/.agents/uptime-kuma-config.json   (user-owned, no secrets inside)
```

Config schema (all keys optional except `base_url` in fleet mode):



## Reads — metrics (no socket needed)

API keys authenticate via **HTTP Basic with an empty username**:

```bash
curl -sf -u ":$KUMA_API_KEY" "$BASE_URL/metrics" | grep '^monitor_status{'   # 1=Up 0=Down
```

`monitor_response_time` (ms), `monitor_cert_days_remaining`, `monitor_cert_is_valid`
per monitor. Or `python3 scripts/kuma.py metrics`.

## Writes — socket.io

```bash
python3 scripts/kuma.py monitors                     # list (waits for monitorList push)
python3 scripts/kuma.py add-push NAME --interval 360 # create push monitor, token minted client-side
python3 scripts/kuma.py set-token NAME --token HEX32 # attach/replace a push token
python3 scripts/kuma.py push NAME                    # send one heartbeat (status=up)
```

Dependency: `python-socketio==5.13.0` + `websocket-client>=0.58` (websocket transport) — install into a
venv or `pip install --user`; the script names the exact command in its error if absent).

## Critical conventions (full list in references/quirks-2.5.md)

- `add` needs **`accepted_statuscodes`** (snake_case). camelCase → server crash
  `Cannot read properties of undefined (reading 'every')`.
- Do NOT send `group` / `path` / `pathName` / `tags` / `retries` on 2.5.x — not columns.
- **`pushToken` is client-generated** (32-char hex). Creating a push monitor without
  one yields a push-less monitor; fix with `set-token` (editMonitor).
- A `monitor_notification` FK error *after* creation is post-store and harmless.
- Login emit must carry an ack callback; on success the login ack may or may not
  arrive — treat the `monitorList` push event as the auth proof.
