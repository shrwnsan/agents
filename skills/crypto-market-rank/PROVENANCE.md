# PROVENANCE — crypto-market-rank

- **Source:** [binance/binance-skills-hub](https://github.com/binance/binance-skills-hub) `skills/binance-web3/crypto-market-rank`
- **Pinned:** `923c1ead4daab623218202ff298eba4488630835` (2026-06-03, "Release skills/binance-web3/crypto-market-rank v1.0.0")
- **License:** none declared upstream (repo carries no LICENSE; treat as all rights reserved by Binance). Vendored for personal/internal use only — do not redistribute.
- **Vendored:** 2026-11-13, byte-true (SKILL.md verified identical to the pin).
- **Tracking:** listed in `.upstream.yml` (`preserve: [PROVENANCE.md]`); refresh by hand-running the sync-upstream workflow, then diff against this pin. Bumping the pin repeats the vetting pass.

## What it does

Trending tokens, smart-money inflow, meme rank, and social hype rankings via Binance's web3 public API, fronted by a bundled CLI that auto-generates the required `requestId` UUID.

## Vendor review notes (2026-11-13)

- Originally vendored under `skills/tokens/` without provenance; the path was flattened in #157 and this file closes the gap. Read-only API usage; no keys required.
