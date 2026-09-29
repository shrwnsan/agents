# Provenance — vercel-domain-search

Created 2026-09-29 by Claude Code (shrwnsan/agents). Native skill — authored
here, no upstream source.

## Endpoint pin

| Fact | Value | Source | Date |
|------|-------|--------|------|
| Base URL | `https://api.vercel.com` | Vercel OpenAPI spec (`openapi.vercel.sh`) | 2026-09-29 |
| Availability batch | `POST /v1/registrar/domains/search`, body `{domains: string[]}`, maxItems 200, `security: []` | OpenAPI spec + live probe | 2026-09-29 |
| Pricing batch | `POST /v1/registrar/domains/price`, body `{domains: string[] (maxItems 50), years: number}`, `security: []` | OpenAPI spec + live probe | 2026-09-29 |
| Alternate availability | `POST /v1/registrar/domains/availability`, maxItems 50, `security: []` (unused; `search` has the bigger cap) | OpenAPI spec | 2026-09-29 |
| Keyword search (authless) | announced in vercel.com/changelog/search-domains-without-authentication (2026-09-28) | changelog | 2026-09-29 |

## Live response shapes (probed 2026-09-29)

- `search` → `{"results":[{"domain":"example.com","available":false}]}`
- `price` → `{"results":[{"domain":"example.com","years":1,"purchasePrice":null,"renewalPrice":11.25,"transferPrice":11.25}]}`

`purchasePrice` is `null` for taken domains; renewal/transfer prices answer
regardless of availability — hence pricing only the available subset.

## Re-pin procedure

If the API drifts (shape change, auth added), re-fetch `openapi.vercel.sh`,
compare the `/v1/registrar/domains/*` paths against the table above, run one
probe per endpoint to confirm response shapes, update this file with the new
date, and only then change `scripts/check-domains.mjs`.
