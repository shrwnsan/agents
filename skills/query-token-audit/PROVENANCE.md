# PROVENANCE — query-token-audit

- **Source:** [binance/binance-skills-hub](https://github.com/binance/binance-skills-hub) `skills/binance-web3/query-token-audit`
- **Pinned:** `a519ee650ab134af2cf290ef4731412dcf99c6bb` (2026-03-30, "Release skills/binance-web3/query-token-audit v1.0.0")
- **License:** none declared upstream (repo carries no LICENSE; treat as all rights reserved by Binance). Vendored for personal/internal use only — do not redistribute.
- **Vendored:** 2026-11-13, **locally extended, not byte-true**: a usage example (one CLI invocation with a sample request) is inserted after the `## Overview` anchor; the upstream body itself is unmodified. The addition lives verbatim in `local-usage-example.md`, and the sync re-applies it after every refresh.
- **Tracking:** listed in `.upstream.yml` (`preserve: [PROVENANCE.md, local-usage-example.md]` plus an `insert:` rule for SKILL.md); refresh by hand-running the sync-upstream workflow. A missing anchor or snippet fails the sync instead of stripping the example. Bumping the pin repeats the vetting pass.

## What it does

One endpoint: token security scan (honeypot/rug-pull detection, contract audit) via Binance's web3 public API, fronted by a bundled CLI that auto-generates the required `requestId` UUID.

## Vendor review notes (2026-11-13)

- Originally vendored under `skills/tokens/` without provenance; the path was flattened in #157 and this file closes the gap. Read-only API usage; no keys required.
