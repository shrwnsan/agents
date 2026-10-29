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
