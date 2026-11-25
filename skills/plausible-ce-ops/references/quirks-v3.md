# Plausible CE v3 quirks (schema-pinned)

Verified against Plausible CE v3-era ClickHouse schema (24.12.6) and the
docker-compose CE deployment. Re-verify after major version bumps.

## `events` vs `events_v2`

- Fresh v3 stacks write **`events_v2`**; the legacy `events` table exists but
  stays **empty (0 rows)**. Querying `events` and concluding "no data" is the
  single most common false alarm.
- Check which table is live: row counts on both, plus
  `max(timestamp) FROM events_v2` against wall clock.
- Sessions live in `sessions_v2` (plus `sessions_v2_tmp_versioned`); the same
  empty-legacy-table rule applies (`sessions` vs `sessions_v2`).

## `events_v2` schema essentials

| Need | Column |
|---|---|
| Site | `hostname` (NOT `domain` — `domain` is the v1 name and errors on v2) |
| Event type | `name` (`pageview`, custom events); filter `name='pageview'` for traffic |
| Source | `referrer_source` (normalized, empty string = direct) and `referrer` (raw host) |
| Path | `pathname` |
| Session | `session_id` (UInt64 — countDistinct it for sessions) |
| Time | `timestamp` (DateTime, UTC) |
| Geo | `country_code` FixedString(2); `city_geoname_id` is an ID, not a name |
| Device | `screen_size`, `browser`, `operating_system` |
| UTM | `utm_medium`, `utm_source`, `utm_campaign`, `utm_content`, `utm_term` |

ALIAS columns exist for convenience (`source` -> `referrer_source`,
`country` -> `country_code`, `screen` -> `screen_size`, etc.) — but if an
ALIAS errors, fall back to the underlying column.

## Failure modes

- **Stale ingestion**: `max(timestamp)` frozen while sites get traffic —
  check the `plausible` container logs and the ClickHouse container health;
  buffer flush failures often trace to disk pressure on the CH volume.
- **Dashboard 404 via CDN/proxy, ClickHouse healthy**: origin routing is
  broken (wrong host rule, missing DNS, tunnel down). Distinguish "data is
  missing" from "I can't see the data": run the tail test (SKILL.md) before
  touching analytics config.
- **Docker socket unreachable from the agent's namespace but bridge
  interfaces visible**: query ClickHouse by bridge IP directly
  (`http://172.xx.0.y:8123`) — no container exec needed.
- **`count()` ordered by alias errors**: ClickHouse cannot ORDER BY a
  non-materialized alias in some contexts; order by `count()` itself and
  alias the expression (`... count() AS c ... ORDER BY c DESC` fails on some
  versions — use `ORDER BY 3 DESC` or repeat `count()`).
- **Automation never lands events**: the tracker drops sessions with
  `navigator.webdriver` set, so headless or scripted browsers produce zero
  rows no matter what they click. Verify ingestion with a curl beacon
  instead: `POST https://<public-host>/api/event` with header
  `Content-Type: text/plain` and body
  `{"n":"Test","d":"<domain>","u":"https://<domain>/","v":33}` (a 202 means
  accepted), then look for the row in `events_v2`. The plain-text content
  type is what the loader itself sends, to avoid CORS preflights.

## Goal metadata and custom properties (Postgres + app side)

Goal metadata lives in Postgres, not ClickHouse. On the reference compose
stack the containers are `plausible-plausible-1` (app),
`plausible-plausible_db-1` (Postgres), `plausible-plausible_events_db-1`
(ClickHouse), and the Postgres database and role are both `plausible`
(`docker exec plausible-plausible_db-1 psql -U plausible -d plausible`).
The app container can run Elixir on the live node:
`docker exec plausible-plausible-1 bin/plausible rpc '<code>'`. Use `rpc`,
not `eval`: `eval` starts no services and fails with "could not lookup Ecto
repo". Keep calls read-only; `rpc` executes arbitrary Elixir on the
production node. Useful reads:

```elixir
site = Plausible.Repo.get!(Plausible.Site, ID) |> Plausible.Repo.preload(:team)
IO.inspect(Plausible.Props.allowed_for(site))                    # :all | prop list
IO.inspect(Plausible.Billing.Feature.Props.check_availability(site.team))  # :ok | error
```

Failure modes observed on v3.2.1:

- **`goals.custom_props` values are SQL parameters.** The stats queries bind
  each map value as a ClickHouse parameter. A JSON `null` (from a
  hand-written INSERT meant to "declare" a property) crashes the driver with
  `FunctionClauseError` in `Ecto.Adapters.ClickHouse.Connection.param_type/1`
  and every goal-filtered endpoint of that site returns 500 until the row is
  fixed. `{}` is the correct shape for a goal that matches any prop value.
  The database and role for the fix are both `plausible`.
- **Property breakdown needs a set-up site, not just data.** The goal card's
  Properties tab discovers keys from
  `GET /api/stats/<domain>/suggestions/prop_key` (`SELECT DISTINCT meta.key`
  over `events_v2` for the range) and renders its generic empty state when
  that returns nothing. Two independent gates produce that empty state:
  (1) no prop-bearing events in the queried range, and (2)
  `sites.allowed_event_props` is `nil`. With `nil`, queries stay open
  (`Plausible.Props.allowed_for/1` returns `:all`) but the dashboard shows a
  "Set up props" call to action instead of the breakdown, because the UI
  checks `Plausible.Props.configured?/1`, which requires a non-empty list.
  Fix in Settings -> Custom Properties by allowing the key (or
  `Plausible.Props.allow_existing_props/1` on the node). Allowing keys
  changes query visibility only; ingestion never filtered by the list.
- **`BASE_URL` has two consumers.** It bakes the event endpoint into the
  served tracker script, and it sets the endpoint host that Phoenix
  LiveView's origin check compares against. A tailnet or CGNAT hostname in
  `BASE_URL` (100.64/10 counts as local network to Chromium) makes Brave and
  Chrome raise local-network permission prompts on every tailnet page load,
  while beacons from devices off the tailnet fail DNS resolution silently.
  Changing `BASE_URL` moves the breakage instead of ending it: the public
  script starts working and the dashboard's websocket starts failing origin
  check on the old host. Distinguish with a handshake probe:
  `curl -si -H 'Connection: Upgrade' -H 'Upgrade: websocket'
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ=='
  -H 'Origin: https://<dashboard-host>' https://<dashboard-host>/live/websocket`
  returns `403` from Cowboy when the origin is rejected and `101` when
  transport and origin pass. Plan for both consumers before editing
  `BASE_URL`; the tracker endpoint wants a public hostname, the dashboard
  wants to be browsed on an allowed one.
