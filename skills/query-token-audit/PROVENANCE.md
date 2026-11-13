# PROVENANCE — query-token-audit

- **Source:** [binance/binance-skills-hub](https://github.com/binance/binance-skills-hub) `skills/binance-web3/query-token-audit`
- **Pinned:** `a519ee650ab134af2cf290ef4731412dcf99c6bb` (2026-03-30, "Release skills/binance-web3/query-token-audit v1.0.0")
- **License:** none declared upstream (repo carries no LICENSE; treat as all rights reserved by Binance). Vendored for personal/internal use only — do not redistribute.
- **Vendored:** 2026-11-13, **locally extended, not byte-true**: a usage example (one CLI invocation with a sample request) was appended after the frontmatter body; the upstream body itself is unmodified. Re-syncing must preserve this addition or re-apply it.
- **Tracking:** listed in `.upstream.yml` (`preserve: [PROVENANCE.md]`); refresh by hand-running the sync-upstream workflow, then diff against this pin — and re-apply the local usage example. Bumping the pin repeats the vetting pass.

## What it does

One endpoint: token security scan (honeypot/rug-pull detection, contract audit) via Binance's web3 public API, fronted by a bundled CLI that auto-generates the required `requestId` UUID.

## Vendor review notes (2026-11-13)

- Originally vendored under `skills/tokens/` without provenance; the path was flattened in #157 and this file closes the gap. Read-only API usage; no keys required.
