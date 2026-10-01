# Skills

Catalog and lifecycle rules for the skills in this repo. Root README: [← back](../README.md).

Skills are self-contained packages with a `SKILL.md` instruction file and optional scripts/binaries. They are loaded by agents that support the `~/.agents/skills/` convention.

| Skill | Category | Source | Description |
|-------|----------|--------|-------------|
| [crafting-commits](crafting-commits/) | Development | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Conventional commit message drafting with collaborative attribution |
| [review-pr](review-pr/) | Development | native | Comprehensive peer code review with severity-tagged findings |
| [skill-quality-gate](skill-quality-gate/) | Development | native | Pre-flight gate for skill directories: structure + frontmatter spec, script syntax, unsafe-pattern scan, behavioral dry-run with refusal probe — deterministic PASS/WARN/FAIL |
| [systematic-debugging](systematic-debugging/) | Development | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Systematic debugging methodology to prevent thrashing |
| [frontend-design](frontend-design/) | Design & Content | [anthropics](https://github.com/anthropics/claude-plugins-official) | Production-grade frontend interfaces |
| [dataviz](dataviz/) | Design & Content | [claude-code bundled](https://code.claude.com/docs/en/skills) | Chart & dashboard design method with validated palette and CVD validator (proprietary, pinned CLI 2.1.267 — [provenance](dataviz/PROVENANCE.md)) |
| [dataviz-tufte](dataviz-tufte/) | Design & Content | [shrwnsan fork](https://github.com/shrwnsan/dataviz-tufte) of [caylent](https://github.com/caylent/tufte-data-viz) | Tufte chart principles + per-library recipes — scoped to reviewing/auditing existing chart code; dataviz generates, this reviews (MIT, pinned fork @ 91f0dee, renamed from tufte-data-viz — [provenance](dataviz-tufte/PROVENANCE.md)) |
| [motion-craft](motion-craft/) | Design & Content | [emilkowalski](https://github.com/emilkowalski/skills) | Animation & interaction craft — motion decisions, easing/springs, micro-interactions, transition performance; frontend-design directs, this executes (MIT, pinned @ d23d7f8, rebranded from emil-design-eng — [provenance](motion-craft/PROVENANCE.md)) |
| [marp-slide](marp-slide/) | Design & Content | [softaworks](https://github.com/softaworks/agent-toolkit) | Marp presentation slides with 7 themes |
| [extract-design-tokens](extract-design-tokens/) | Design & Content | native | Extract design tokens + taste read (dials, audit) from a live site or local HTML |
| [handoff-context](handoff-context/) | Workflow | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Context engineering for session handoffs across AI tools |
| [meta-search](meta-search/) | Workflow | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins/tree/main/plugins/search-plus) | Error recovery for web search failures (403, 429, 422) with bundled Tavily/Jina scripts |
| [docker-agent-browser](docker-agent-browser/) | Development | native | Agent-browser + Chromium setup in Docker containers (ARM64 workaround) |
| [caveman](caveman/) | Workflow | [JuliusBrussee](https://github.com/JuliusBrussee/caveman) | Ultra-compressed communication mode (~75% token reduction) |
| [here-now](here-now/) | Workflow | native | Security-hardened file publishing via [here.now](https://here.now). Based on [heredotnow/skill](https://github.com/heredotnow/skill) v1.11.0 |
| [vercel-domain-search](vercel-domain-search/) | Workflow | native | Keyless batch domain availability + pricing via Vercel's registrar API — priced read-only shortlists; purchase/transfer out of scope (endpoints pinned, [provenance](vercel-domain-search/PROVENANCE.md)) |
| [live-system-forensics](live-system-forensics/) | Security | native | Live malware/persistence forensics: process, network, and startup audits with per-host allowlist baselines and drift detection |
| [auditing-agent-harnesses](auditing-agent-harnesses/) | Security | native | Privacy/telemetry audits for agent harnesses and AI-coding desktop apps (Electron/asar, Tauri, thin-shell+sidecar), with re-audit triggers on version updates |
| [cleaning-disk-storage](cleaning-disk-storage/) | System | native | Disk cleanup: scan temp/cache/build artifacts, tiered confirmations, trash-only removal, regeneration guidance |
| [tokens/crypto-market-rank](tokens/crypto-market-rank/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Trending tokens, smart-money inflow, meme rank, social hype |
| [tokens/query-token-audit](tokens/query-token-audit/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Honeypot/rug-pull detection, contract security audit |
| [tokens/query-token-info](tokens/query-token-info/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Token metadata, price, klines, social links |
| [tokens/trading-signal](tokens/trading-signal/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Smart-money buy/sell signals with trigger prices |

Skills from vibekit are automatically synced via GitHub Actions. Upstream skills are synced manually via [sync-upstream](../.github/workflows/sync-upstream.yml) — sources in [.upstream.yml](../.upstream.yml).

## Adding a skill

1. **Vet before merging** — read the SKILL.md and every bundled script end to end, then run once in a real consumer container with its output checked against a known-good expectation.
2. **Named gap** — not duplicating a skill already in this repo's table; if it supersedes one, the old skill is removed in the same commit.
3. **Vendor and pin** — third-party skills are copied at a recorded commit (Source column links the ref), never tracked to a moving branch; bumping a pinned ref re-triggers the full vetting pass.

Evaluated-and-rejected candidates go in [rejected-skills.json](../rejected-skills.json), appended in the same turn as the decision — rejections only, since the table above is the acceptance record.
