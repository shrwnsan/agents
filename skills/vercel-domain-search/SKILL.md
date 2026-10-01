---
name: vercel-domain-search
license: Apache-2.0
description: >
  Batch-check domain availability and registration pricing via Vercel's
  authless registrar API. Feed it a candidate list (file or args) and get a
  priced shortlist sorted by price. Keyless and read-only — availability and
  price only; buying, transferring, and renewing stay out of scope. Use when
  picking a domain for a new site or property, checking "is X.com available",
  or pricing a domain shortlist.
user-invocable: true
---

# Vercel Domain Search

## Overview

Vercel's domains-registrar API exposes search, availability, and pricing with
no authentication (`security: []` in their OpenAPI spec). This skill wraps the
batch endpoints into one read-only check: give it candidate names, get back
what's free and what it costs. Purchasing requires a Vercel account and is
deliberately not implemented here.

## Usage

```bash
# From a names file (one domain per line, up to 200)
node scripts/check-domains.mjs candidates.txt

# Inline names
node scripts/check-domains.mjs example.com example.org

# Options
node scripts/check-domains.mjs candidates.txt --years 1 --limit 25 --json
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--years N` | `1` | Registration years to price |
| `--limit USD` | none | Per-year price cap: flag rows above it as premium instead of dropping them |
| `--json` | off | Raw merged results instead of the markdown shortlist |

Names are normalized (lowercased, scheme/path stripped, `www.` prefix
removed) and validated; entries without a dot are skipped with a warning.

## Endpoint pins (keyless, as of 2026-09-29)

Base `https://api.vercel.com` — pinned against Vercel's OpenAPI spec (see
[PROVENANCE.md](PROVENANCE.md)):

| Endpoint | Batch cap | Purpose |
|----------|-----------|---------|
| `POST /v1/registrar/domains/search` | 200 names | Availability pass (returns `{domain, available}`) |
| `POST /v1/registrar/domains/price` | 50 names | Pricing pass (`purchasePrice`, `renewalPrice`, `transferPrice`) |

`POST /v1/registrar/domains/availability` (cap 50) is the same availability
check with a smaller batch cap; the skill uses `search` for the larger cap.
`buy`, `transfer`, `renew`, and `auth-code` endpoints are auth-gated — this
skill never calls them.

## Output

Markdown shortlist: available domains first, sorted by per-year price, with
purchase and renewal shown as *total / per-year* (the API prices a period as
a total — see PROVENANCE.md), and a premium flag above `--limit`. Summary
line reports N available of M checked, K under the per-year cap.
`--json` prints the merged raw rows plus a `pricesArePeriodTotals` marker.

## Gotchas

- **Prices are period totals, not per-year.** Verified 2026-10-01:
  `$13/yr` name → years:2 = $26, years:3 = $39. The script shows both total
  and per-year; `--limit` compares per-year.
- **Search seems to exclude premium/registry-reserved inventory.** Probed
  2026-10-01: 8/8 generic-word names (book.dev, casino.io, crypto.chat, …)
  returned `available: false`, not `available: true` at high prices. So
  "available" from this API is a floor, not a guarantee — registry-level
  premium/pricing rules can still apply at checkout.
- **Availability ≠ affordable.** Registry-premium names can come back
  `available: true` at four-to-six-figure prices. Always run the pricing pass
  and filter on price, not availability alone.
- **Taken domains still return prices.** `price` answers for any name;
  `purchasePrice` is `null` for taken domains. Price only the available
  subset (the script does this). For *available* names with a null
  `purchasePrice` the script substitutes renewal and flags it
  `purchase est. = renewal`.
- **Keyless is search-only.** The moment you need to buy, that's a Vercel
  account decision — hand the shortlist to a human.
- **Be gentle.** Authless means no published rate limit; the script sleeps
  1s between chunks. A few hundred names is fine, don't loop thousands.
