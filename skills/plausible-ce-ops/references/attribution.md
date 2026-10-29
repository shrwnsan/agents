# Referrer attribution per platform

Observed behavior of social platforms' `Referer` headers on link clicks, and
what it means for Plausible sources. Clicks and in-app browsers only —
impressions never touch your site and need each platform's own insights.

## What Plausible records

- `referrer`: raw host from the `Referer` header (e.g. `t.co`,
  `m.facebook.com`), empty when stripped.
- `referrer_source`: normalized label (`Twitter`, `Facebook`, `GitHub`,
  search-engine names); empty string for direct/no-referrer.
- Link-redirect hosts (`t.co`, `l.threads.com`, `l.instagram.com`) may appear
  as their own `referrer_source` when they are not in Plausible's source map —
  expect a label to split across two source values depending on entry point.

## Platform behavior (clicks)

| Platform | Typical referrer | Reliability |
|---|---|---|
| X/Twitter | `t.co` | High — attribution works with a plain domain |
| Threads | `l.threads.com` / `threads.com` | High — label may split across two sources |
| Facebook | `m.facebook.com`, `facebook.com` | High — label merges in dashboard |
| Instagram | `l.instagram.com` occasionally | Low — usually stripped; those visits land as **Direct/None** |
| Bluesky/LinkedIn | app host | Generally passes through |
| Mastodon | instance host | Passes, but source label is the raw instance |

## Direct/None is not all "lost social traffic"

The direct bucket mixes genuinely direct visits (bookmarks, typing the URL,
channel links) with stripped-referrer clicks. Before buying a fix, compare the
sum of identified social referrers against what each platform's own analytics
reports for outbound clicks; the gap bounds how much is hiding in Direct.

## Vanity paths (`site.com/x` -> 301 `/`)

- Fix attribution **only** for platforms that strip referrers (Instagram is
  the one that matters in practice).
- Implement as a redirect, not a duplicate page, so canonical/SEO stays clean.
- Add nothing where referrers already flow (X, Threads, Facebook) — the
  referrer arrives either way.
- They never measure non-click visibility; that requires platform insights.
