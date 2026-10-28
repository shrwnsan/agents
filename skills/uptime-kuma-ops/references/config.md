# Configuration

Runtime config lives at `~/.agents/uptime-kuma.json` (user-owned, `chmod 600`).
The shipped [`config.example.json`](../config.example.json) is the template —
copy it there and fill in your values. Secrets never go in this file: it names
env files and env-key names; credentials are resolved from those files at runtime.

Without this file the skill still works — pass `--base-url` (and credentials)
per invocation; nothing is persisted.

## Keys

| Key | Purpose |
|---|---|
| `base_url` | Kuma root URL. Or set `base_url_key` to resolve it from the auth env file. |
| `auth_env_file` | Path (prefer `~/`-anchored) to a 600-mode env file holding credentials. |
| `username_key` / `password_key` | Env-key names for socket.io credentials inside `auth_env_file`. |
| `api_key_key` | Env-key name for the metrics API key inside `auth_env_file`. |
| `push_env_file` | Where `PUSH_<NAME>` push tokens are written/read (dead-man's-switch home). |
| `ping_script` | Optional helper invoked after writes (fleet integration hook; unused by core). |

Minimal viable config (reads everything else from defaults):

```json
{ "base_url": "https://kuma.internal", "auth_env_file": "~/.config/kuma.env" }
```
