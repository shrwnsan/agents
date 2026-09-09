# tokens

On-chain token research and security skills from [Binance Skills Hub](https://github.com/binance/binance-skills-hub). No API key required — all endpoints are public.

## Why these four

The Binance Skills Hub ships 18 skills. Most require API keys or serve narrow use cases. These four were selected because they cover the highest-utility slice of token research without any paid dependencies:

| Skill | What it does | Why included |
|-------|-------------|--------------|
| [crypto-market-rank](crypto-market-rank/) | Trending tokens, smart-money inflow, meme rank, social hype, trader PnL leaderboards | Market context — the "what's moving" layer. Useful for Daily Sip curation enrichment and general awareness. |
| [query-token-audit](query-token-audit/) | Honeypot/rug-pull detection, contract risk, buy/sell tax check | Safety gate — run before any deeper research on a token. One call, comprehensive result. |
| [query-token-info](query-token-info/) | Per-token metadata, social links, creator info, real-time price, kline/OHLCV data | Deep-dive complement to audit. Get the fundamentals and charts once you've confirmed the token isn't a scam. |
| [trading-signal](trading-signal/) | Smart-money buy/sell signals with trigger price, max gain, exit rate | Actionable layer — discrete signals, not just data. BSC and Solana only. |

Typical flow: **rank** (what's hot) → **audit** (is it safe) → **info** (tell me more) → **signal** (what are smart wallets doing).

## What was skipped and why

The remaining 14 skills from Binance Skills Hub were evaluated and excluded:

**Requires API key (6):**
- `trade` — swap/limit orders, needs wallet connection
- `wallet-portfolio` — personal portfolio, needs auth
- `wallet-pnl` — personal PnL tracking, needs auth
- `wallet-transfer` — on-chain transfers, needs wallet
- `dapp-interaction` — DeFi protocol calls, needs wallet
- `copy-trade` — follow smart-money trades, needs wallet

**Too narrow (4):**
- `binance-sports-ai-analyzer` — World Cup only, very narrow timing
- `binance-tokenized-securities-info` — Ondo tokenized stocks, tiny market
- `meme-rush` — Pulse launchpad feed, low signal-to-noise
- `fiat` — only useful if buying crypto via fiat onramp

**Too shallow without paid features (2):**
- `query-address-info` — single wallet snapshot, limited without wallet tracker (paid)
- `binance-leaderboard` — free features are just rankings lookup

**Niche use case (1):**
- `p2p` (Phase 1) — P2P price comparison

**Redundant with included skills (1):**
- `binance-trading-signal` — appeared under both `skills/binance/` and `skills/binance-web3/`; the web3 version is the canonical one (included here as `trading-signal`)

## Source

Cloned from [`binance/binance-skills-hub`](https://github.com/binance/binance-skills-hub) (`skills/binance-web3/`). The upstream repo has no LICENSE file. Skills are used as reference material and CLI tooling.

## Supported chains

| Chain | chainId |
|-------|---------|
| Ethereum | `1` |
| BSC | `56` |
| Base | `8453` |
| Solana | `CT_501` |

Coverage varies by skill — see individual SKILL.md files. Trading signals are BSC + Solana only. Meme rank is BSC only.
