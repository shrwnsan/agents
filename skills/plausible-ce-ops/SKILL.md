---
name: plausible-ce-ops
license: Apache-2.0
compatibility: "Requires python3 (urllib only, no dependencies) and network access to the Plausible CE stack's ClickHouse HTTP port (default 8123). Read-only: the skill never inserts, deletes, or mutates analytics data."
metadata:
  author: shrwnsan
  version: "1.0.0"
description: "Operate and debug self-hosted Plausible Community Edition: verify tracking is landing, break down traffic sources and referrers via ClickHouse, check ingestion health, and diagnose dashboard/script reachability. Use when the user mentions Plausible,CE,self-hosted analytics, missing events, referrer attribution, or events_v2 queries."
---

# Plausible CE Ops

Operate self-hosted Plausible Community Edition (battle-tested on the v3 schema)
without the dashboard: verify events land, attribute traffic, and diagnose why
data is missing. Read-only over ClickHouse HTTP; the Stats API is the fallback
path. Version-pinned gotchas live in
[references/quirks-v3.md](references/quirks-v3.md) — read it before writing any
query against `events_v2`.

## Endpoint configuration (per invocation, nothing persisted)

The skill is fleet-agnostic: pass the ClickHouse HTTP endpoint each time or set
`PLAUSIBLE_CH_URL` (default `http://127.0.0.1:8123`). Never hardcode hosts,
tokens, or credentials into any file; if the ClickHouse server enforces auth,
resolve user/password from env at call time (`PLAUSIBLE_CH_USER` /
`PLAUSIBLE_CH_PASSWORD`, sent as `X-ClickHouse-User` / `X-ClickHouse-Key`
headers) and never print or log them.

```bash
python3 scripts/plausible.py health                          # tables + row counts
python3 scripts/plausible.py referrers --hostname SITE       # source breakdown
python3 scripts/plausible.py daily --hostname SITE --days 7  # views/sessions per day
python3 scripts/plausible.py recent --hostname SITE --limit 8  # latest pageviews
python3 scripts/plausible.py verify --hostname SITE          # live-visit landing check
python3 scripts/plausible.py raw "SELECT ..."                # escape hatch (SELECT only)
```

All subcommands accept `--url`, `--db` (default `plausible_events_db`), and
`--format` (`PrettyCompactNoEscapes` default; anything ClickHouse accepts).

## Finding the ClickHouse endpoint

Three common layouts, in discovery order:

1. **Same host, published port** — `curl -s http://127.0.0.1:8123/?query=SELECT%201`
2. **Docker bridge IP** (no published port; you share a network namespace with
   the host): `ip -br addr` for `br-*` bridges, then probe `:8123` on
   `172.xx.0.2..7`. Cross-check `docker ps` when the socket is reachable.
3. **From compose config** — the `CLICKHOUSE_URL` env of the `plausible`
   service names the in-network host:port/db directly.

`health` returning an empty `events` table but a populated `events_v2` is the
v3 signature — not a failure. See quirks.

## Verifying tracking works (the tail test)

The only honest check is a real round trip: load the target site once, then
immediately run `verify --hostname SITE` (it reads pageviews from the last 5
minutes). Browser -> script -> ingest -> ClickHouse in one step. A visit that
shows in neither the dashboard nor ClickHouse means the tracking script is not
loading or firing; a ClickHouse row with an empty dashboard means dashboard
reachability, not ingestion, is broken.

## Diagnosing missing data

Work outward from the write path:

1. **Script present and firing?** Fetch the site HTML, confirm the Plausible
   script tag, and check `window.plausible` after render.
2. **Ingestion alive?** `health`; compare `max(timestamp)` in `events_v2`
   against wall clock. A stale max means ingestion stopped (dead container,
   full disk, buffer errors in `docker logs plausible`).
3. **Reachable at all?** A dashboard 404 through a reverse proxy/CDN with a
   healthy ClickHouse is routing, not analytics: compare the public hostname
   against the app's direct container port. Fix the proxy route; the data
   collection may be fine either way if the script endpoint differs from the
   dashboard hostname.
4. **Wrong table?** v2-era stacks write `events`; v3 stacks write `events_v2`.
   Query the populated one — see quirks.

## Referrer attribution reading

`referrer_source` is Plausible's normalized source (`Twitter`, `GitHub`,
direct = empty string); `referrer` is the raw host. Expect platform quirks:
Instagram strips referrers most of the time (those visits land as direct),
Facebook splits across `m.facebook.com` / `facebook.com`, and Threads appears
both as `Threads` and as the raw `l.threads.com` host depending on entry
point. Vanity paths (`site.com/x` -> 301 `/`) fix attribution only for the
platforms that strip; they add nothing where referrers flow. Details:
[references/attribution.md](references/attribution.md).

## Stats API fallback

When ClickHouse is unreachable but the app is, the read-only Stats API covers
the same ground with worse fidelity (no `session_id`-level checks). API keys
authenticate as `Authorization: Bearer <key>`; resolve keys from env, never
from files. Hard rules: `bounce_rate`/`visit_duration` pair with
`visit:entry_page`, `pageviews`/`time_on_page` pair with `event:page`;
dimensions require a `pagination` object (bare `limit` errors); `is` filters
take no wildcards (use `contains`/`matches`); date ranges are only
`day|today|7d|week|30d|month|year|all`.

## Need more?

```bash
cat references/quirks-v3.md        # events vs events_v2, schema, failure modes
cat references/attribution.md      # referrer behavior per platform
cat references/clickhouse-queries.md  # copy-paste query cookbook
```
