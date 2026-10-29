# ClickHouse query cookbook

All queries assume `events_v2`, filter `name='pageview'`, and take the site as
`hostname = '<SITE>'`. Replace `<SITE>` per invocation; never commit a real
hostname into this file.

Referrers, all time (source, raw host, first/last seen):
```sql
SELECT referrer_source, referrer, count() AS views,
       min(timestamp), max(timestamp)
FROM plausible_events_db.events_v2
WHERE hostname = '<SITE>' AND name = 'pageview'
GROUP BY referrer_source, referrer
ORDER BY views DESC
```

Per-day views and sessions:
```sql
SELECT toDate(timestamp) AS d, count() AS views,
       countDistinct(session_id) AS sessions
FROM plausible_events_db.events_v2
WHERE hostname = '<SITE>' AND name = 'pageview'
  AND timestamp >= now() - INTERVAL 7 DAY
GROUP BY d ORDER BY d DESC
```

Direct vs referred, per day:
```sql
SELECT toDate(timestamp) AS d,
       if(referrer_source = '', 'Direct', referrer_source) AS src,
       count() AS views
FROM plausible_events_db.events_v2
WHERE hostname = '<SITE>' AND name = 'pageview'
GROUP BY d, src ORDER BY d DESC, views DESC
```

Top pages:
```sql
SELECT pathname, count() AS views, countDistinct(session_id) AS sessions
FROM plausible_events_db.events_v2
WHERE hostname = '<SITE>' AND name = 'pageview'
  AND timestamp >= now() - INTERVAL 7 DAY
GROUP BY pathname ORDER BY views DESC LIMIT 20
```

Latest raw pageviews (the tail test — run right after a manual visit):
```sql
SELECT timestamp, pathname, referrer, referrer_source, browser, screen_size
FROM plausible_events_db.events_v2
WHERE hostname = '<SITE>' AND name = 'pageview'
  AND timestamp >= now() - INTERVAL 5 MINUTE
ORDER BY timestamp DESC
```

Ingestion health — table inventory and freshness:
```sql
SELECT name, total_rows
FROM system.tables WHERE database = 'plausible_events_db'

SELECT hostname, min(timestamp), max(timestamp), count()
FROM plausible_events_db.events_v2
GROUP BY hostname ORDER BY count() DESC
```

Multi-site inventory (which sites report at all):
```sql
SELECT hostname, count() AS views, uniqExact(session_id) AS sessions,
       min(timestamp) AS first_seen, max(timestamp) AS last_seen
FROM plausible_events_db.events_v2
GROUP BY hostname ORDER BY views DESC
```

Tips:
- Build the query in the script with `--data-binary` (raw SQL body), not
  `--data-urlencode` — ClickHouse treats the latter's `query=...` body as a
  syntax error at position 1.
- `ORDER BY <alias>` of an aggregate can error on some versions; order by the
  expression or its ordinal instead.
- Everything here is read-only SELECT; the script's `raw` subcommand rejects
  anything else.
