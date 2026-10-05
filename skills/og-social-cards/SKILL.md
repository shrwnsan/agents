---
name: og-social-cards
license: Apache-2.0
description: >
  QA and debug Open Graph / social-card (link-preview) tags and images. Extract
  and validate OG/Twitter meta tags, test the rendered card across platform
  debuggers, and cache-bust stale previews on Slack/X/iMessage/LinkedIn/Telegram.
---

# OG / Social-Card QA

Work through these when checking/fixing how a URL previews when shared.

## 1. Extract the tags

First check the response: `curl -sL -o /dev/null -w '%{http_code} %{content_type}' <url>` — a non-200 or non-text/html response means there are no OG tags to validate; report that and stop.

```
curl -sL <url> | grep -ioE '<meta property="og:[^"]*"[^>]*>|<meta name="twitter:[^"]*"[^>]*>|<link rel="canonical"[^"]*>'
```
A complete card has: `og:title`, `og:description`, `og:type`, `og:url`, `og:image` (+ `og:image:width`/`height`), `og:site_name`, `twitter:card` (`summary_large_image`), `twitter:image`, `canonical`. One `<title>` and one `<h1>` per page for traditional SEO.

## 2. Validate
- `og:url` + `canonical`: **absolute** (`https://…`), on the canonical domain, and matching each other.
- `og:image` + `twitter:image`: **absolute** URLs returning HTTP **200**, **PNG or JPG** (SVG OG images are NOT reliably supported by X/Twitter). Ideal size **1200×630** (1.91:1).
- `og:title` ≤ ~60 chars; `og:description` ≤ ~155 chars.

## 3. Test the rendered card (the tools)
- **opengraph.xyz** (`https://opengraph.xyz/`) — paste the URL; renders the card across platforms + shows parsed tags. Best single check.
- **Facebook Sharing Debugger** (`https://developers.facebook.com/tools/debug/`) — FB's scrape; **"Scrape Again"** force-refreshes FB's cache.
- **Twitter/X Card Validator** — X's validator (force-refresh X's cache).
- **LinkedIn Post Inspector** (`https://www.linkedin.com/post-inspector/`) — force-refresh LinkedIn.

## 4. Cache-busting (the gotcha)
Platforms **cache link previews by URL**. Updating OG tags/image on the *same* URL does NOT reliably refresh — especially **Telegram**, which has no refresh button. To force a refresh:
- **Bump the image URL**: change `og:image`/`twitter:image` to `og-image.png?v=2` (new URL → platforms re-fetch).
- Use each platform debugger's **"re-scrape"/"refresh"** button (FB / LinkedIn / X).
- For Telegram: re-paste the URL, or change a query string on the URL.
- For generated images (HTML/CSS → headless-browser screenshot): after editing the card source, re-render, commit the new image, **and** bump the `?v=` — all three, or platforms keep the old card.
