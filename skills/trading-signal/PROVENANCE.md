# PROVENANCE — trading-signal

- **Source:** [binance/binance-skills-hub](https://github.com/binance/binance-skills-hub) `skills/binance-web3/trading-signal`
- **Pinned:** `5847361637028decd18e778395281dc2b3777f90` (2026-06-03, "Release skills/binance-web3/trading-signal v1.0.0")
- **License:** none declared upstream (repo carries no LICENSE; treat as all rights reserved by Binance). Vendored for personal/internal use only — do not redistribute.
- **Vendored:** 2026-11-13, byte-true (SKILL.md verified identical to the pin).
- **Tracking:** listed in `.upstream.yml` (`preserve: [PROVENANCE.md]`); refresh by hand-running the sync-upstream workflow, then diff against this pin. Bumping the pin repeats the vetting pass.

## What it does

Smart-money buy/sell signals with trigger prices via Binance's web3 public API, fronted by a bundled CLI that auto-generates the required `requestId` UUID.

## Vendor review notes (2026-11-13)

- Originally vendored under `skills/tokens/` without provenance; the path was flattened in #157 and this file closes the gap. Read-only API usage; no keys required.
- Upstream also ships a `binance-trading-signal` variant (richer knowledge file); this hub vendored the plain `trading-signal` one.
