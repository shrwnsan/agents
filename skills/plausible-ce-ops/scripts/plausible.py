#!/usr/bin/env python3
"""Read-only Plausible CE operations over ClickHouse HTTP.

No dependencies beyond python3 stdlib. Endpoint comes from --url or
PLAUSIBLE_CH_URL (default http://127.0.0.1:8123); credentials, if the server
requires them, come from PLAUSIBLE_CH_USER / PLAUSIBLE_CH_PASSWORD env vars
and are sent as headers only — never printed, logged, or persisted.

Subcommands:
  health                            table inventory + freshness
  referrers --hostname SITE         source breakdown (all time)
  daily --hostname SITE [--days N]  views/sessions per day
  recent --hostname SITE [--limit N]  latest pageviews
  verify --hostname SITE            exit 0 if a pageview landed in the last 5 min
  raw "SELECT ..."                  read-only escape hatch
"""

import argparse
import os
import sys
import urllib.error
import urllib.request

WRITE_TOKENS = ("INSERT", "ALTER", "DROP", "TRUNCATE", "DELETE", "CREATE",
                "GRANT", "REVOKE", "OPTIMIZE", "SYSTEM", "KILL", "SET",
                "RENAME", "ATTACH", "DETACH", "UNDROP")

DB = "plausible_events_db"
FMT = "PrettyCompactNoEscapes"
URL = "http://127.0.0.1:8123"
TIMEOUT = 30


def ch_query(sql: str) -> str:
    req = urllib.request.Request(URL, data=sql.encode("utf-8"), method="POST")
    user = os.environ.get("PLAUSIBLE_CH_USER")
    password = os.environ.get("PLAUSIBLE_CH_PASSWORD")
    if user:
        req.add_header("X-ClickHouse-User", user)
    if password:
        req.add_header("X-ClickHouse-Key", password)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        sys.exit(f"ClickHouse error {exc.code}: {body.strip()[:500]}")
    except urllib.error.URLError as exc:
        sys.exit(f"Cannot reach ClickHouse at {URL}: {exc.reason}\n"
                 "Discovery order: published 8123 on the app host, docker "
                 "bridge IPs (ip -br addr, probe :8123), or CLICKHOUSE_URL "
                 "from the compose config.")


def show(sql: str) -> None:
    out = ch_query(sql + f" FORMAT {FMT}")
    print(out.rstrip() or "(empty result)")


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def cmd_health(_):
    show("SELECT name, total_rows FROM system.tables "
         f"WHERE database = '{DB}' ORDER BY name")
    print("\n-- freshness (events_v2 per hostname) --")
    show(f"SELECT hostname, count() AS views, max(timestamp) AS last_seen "
         f"FROM {DB}.events_v2 GROUP BY hostname ORDER BY views DESC")
    print("\nNote: an empty legacy `events` table is the expected v3 "
          "signature; events_v2 is the live one.")


def cmd_referrers(a):
    show(f"SELECT referrer_source, referrer, count() AS views, "
         f"min(timestamp), max(timestamp) FROM {DB}.events_v2 "
         f"WHERE hostname = '{esc(a.hostname)}' AND name = 'pageview' "
         f"GROUP BY referrer_source, referrer ORDER BY views DESC")


def cmd_daily(a):
    show(f"SELECT toDate(timestamp) AS d, count() AS views, "
         f"countDistinct(session_id) AS sessions FROM {DB}.events_v2 "
         f"WHERE hostname = '{esc(a.hostname)}' AND name = 'pageview' "
         f"AND timestamp >= now() - INTERVAL {int(a.days)} DAY "
         f"GROUP BY d ORDER BY d DESC")


def cmd_recent(a):
    show(f"SELECT timestamp, pathname, referrer, referrer_source, browser, "
         f"screen_size FROM {DB}.events_v2 "
         f"WHERE hostname = '{esc(a.hostname)}' AND name = 'pageview' "
         f"ORDER BY timestamp DESC LIMIT {int(a.limit)}")


def cmd_verify(a):
    sql = (f"SELECT count() AS hits FROM {DB}.events_v2 "
           f"WHERE hostname = '{esc(a.hostname)}' AND name = 'pageview' "
           f"AND timestamp >= now() - INTERVAL 5 MINUTE FORMAT TSV")
    out = ch_query(sql).strip()
    hits = int(out) if out else 0
    if hits:
        print(f"OK: {hits} pageview(s) landed for {a.hostname} in the "
              f"last 5 minutes.")
    else:
        sys.exit(f"FAIL: no pageviews for {a.hostname} in the last 5 "
                 "minutes. Load the site once and retry; if still empty, "
                 "check the tracking script tag and the plausible "
                 "container logs.")


def cmd_raw(a):
    sql = a.sql.strip()
    head = sql.split(None, 1)[0].upper().rstrip(";") if sql else ""
    if head in WRITE_TOKENS or head != "SELECT" and not sql.upper().startswith("WITH"):
        sys.exit(f"Refusing statement: {head or '(empty)'}. Read-only tool.")
    show(sql)


def main():
    global URL, TIMEOUT, FMT
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=os.environ.get("PLAUSIBLE_CH_URL", URL),
                   help="ClickHouse HTTP endpoint (env PLAUSIBLE_CH_URL)")
    p.add_argument("--db", default=os.environ.get("PLAUSIBLE_CH_DB", DB))
    p.add_argument("--format", default=FMT)
    p.add_argument("--timeout", type=int, default=TIMEOUT)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health").set_defaults(fn=cmd_health)

    for name, fn in (("referrers", cmd_referrers), ("daily", cmd_daily),
                     ("recent", cmd_recent), ("verify", cmd_verify)):
        s = sub.add_parser(name)
        s.add_argument("--hostname", required=True,
                       help="site hostname, e.g. example.com")
        s.set_defaults(fn=fn)
    sub.choices["daily"].add_argument("--days", type=int, default=7)
    sub.choices["recent"].add_argument("--limit", type=int, default=8)

    s = sub.add_parser("raw", help="read-only SELECT/WITH passthrough")
    s.add_argument("sql")
    s.set_defaults(fn=cmd_raw)

    args = p.parse_args()
    URL = args.url.rstrip("/")
    TIMEOUT = args.timeout
    FMT = args.format
    globals()["DB"] = args.db
    args.fn(args)


if __name__ == "__main__":
    main()
