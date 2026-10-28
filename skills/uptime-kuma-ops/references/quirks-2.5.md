# Uptime Kuma 2.5.x automation quirks

Source-verified against `server/server.js` + `server/model/monitor.js` @ 2.5.3.

## Metrics / API keys
- API keys authenticate via **HTTP Basic with an EMPTY username**: `curl -u ":$KEY" .../metrics`.
  `X-API-Key`, `Bearer`, and query-param forms all 401 — a 401 there is *not* a stale key.
- `/metrics` is the only REST surface; every other `/api/*` path is SPA fallback (HTML).

## socket.io `add` / `editMonitor` (2.5.3 field contract)
- Requires **`accepted_statuscodes`** (snake_case). Sending camelCase `acceptedStatuscodes`
  → server crash `Cannot read properties of undefined (reading 'every')` — the server calls
  `.every()` on the snake_case key directly.
- These keys are **not** 2.5.3 columns and must NOT be sent: `group`, `path`, `pathName`,
  `tags`, `retries` → `SQLITE_ERROR: table monitor has no column named ...`.
- **`pushToken` is client-generated** (32-char hex, e.g. `secrets.token_hex(16)`). The server
  stores whatever the payload carries; a push monitor created without a token is push-less.
  Fix: `editMonitor` with `id` + `pushToken`.
- `notificationIDList` must be `{"notificationIDs": []}` — the handler iterates its keys as
  notification IDs; any other key → FOREIGN KEY constraint error.
- A `monitor_notification` FOREIGN KEY error **after** creation is post-store: the monitor row
  and token were already saved. Harmless.

## socket.io login
- The login emit MUST carry an ack callback (server bails silently otherwise:
  `typeof callback !== "function"` → return).
- The login ack may or may not arrive even on success — use the `monitorList` push
  event as the auth proof.
- WebSocket transport is more reliable than polling; do reads promptly after login.

## Push monitors
- Push URL: `{base}/api/push/{token}?status=up&msg=&ping=`.
- Token home convention: `PUSH_<NAME_UPPER_SNAKE>` lines in a 600-mode env file.
- Heartbeat dead-man pattern: monitor interval ≈ 2× the job cadence; DOWN alert = job
  stopped pinging (crashes *and* silent failures both trip it).
