# agents

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
![Skills: 23](https://img.shields.io/badge/skills-23-green.svg)
[![skills.sh](https://skills.sh/b/shrwnsan/agents)](https://skills.sh/shrwnsan/agents)

Personal hub for AI agent skills, prompts, and configurations.

## Skills

Skills are self-contained packages with a `SKILL.md` instruction file and optional scripts/binaries. They are loaded by agents that support the `~/.agents/skills/` convention.

| Skill | Category | Source | Description |
|-------|----------|--------|-------------|
| [crafting-commits](skills/crafting-commits/) | Development | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Conventional commit message drafting with collaborative attribution |
| [review-pr](skills/review-pr/) | Development | native | Comprehensive peer code review with severity-tagged findings |
| [skill-quality-gate](skills/skill-quality-gate/) | Development | native | Pre-flight gate for skill directories: structure + frontmatter spec, script syntax, unsafe-pattern scan, behavioral dry-run with refusal probe — deterministic PASS/WARN/FAIL |
| [systematic-debugging](skills/systematic-debugging/) | Development | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Systematic debugging methodology to prevent thrashing |
| [frontend-design](skills/frontend-design/) | Design & Content | [anthropics](https://github.com/anthropics/claude-plugins-official) | Production-grade frontend interfaces |
| [dataviz](skills/dataviz/) | Design & Content | [claude-code bundled](https://code.claude.com/docs/en/skills) | Chart & dashboard design method with validated palette and CVD validator (proprietary, pinned CLI 2.1.267 — [provenance](skills/dataviz/PROVENANCE.md)) |
| [dataviz-tufte](skills/dataviz-tufte/) | Design & Content | [shrwnsan fork](https://github.com/shrwnsan/dataviz-tufte) of [caylent](https://github.com/caylent/tufte-data-viz) | Tufte chart principles + per-library recipes — scoped to reviewing/auditing existing chart code; dataviz generates, this reviews (MIT, pinned fork @ 91f0dee, renamed from tufte-data-viz — [provenance](skills/dataviz-tufte/PROVENANCE.md)) |
| [motion-craft](skills/motion-craft/) | Design & Content | [emilkowalski](https://github.com/emilkowalski/skills) | Animation & interaction craft — motion decisions, easing/springs, micro-interactions, transition performance; frontend-design directs, this executes (MIT, pinned @ d23d7f8, rebranded from emil-design-eng — [provenance](skills/motion-craft/PROVENANCE.md)) |
| [marp-slide](skills/marp-slide/) | Design & Content | [softaworks](https://github.com/softaworks/agent-toolkit) | Marp presentation slides with 7 themes |
| [extract-design-tokens](skills/extract-design-tokens/) | Design & Content | native | Extract design tokens + taste read (dials, audit) from a live site or local HTML |
| [handoff-context](skills/handoff-context/) | Workflow | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins) | Context engineering for session handoffs across AI tools |
| [meta-search](skills/meta-search/) | Workflow | [vibekit](https://github.com/shrwnsan/vibekit-claude-plugins/tree/main/plugins/search-plus) | Error recovery for web search failures (403, 429, 422) with bundled Tavily/Jina scripts |
| [docker-agent-browser](skills/docker-agent-browser/) | Development | native | Agent-browser + Chromium setup in Docker containers (ARM64 workaround) |
| [caveman](skills/caveman/) | Workflow | [JuliusBrussee](https://github.com/JuliusBrussee/caveman) | Ultra-compressed communication mode (~75% token reduction) |
| [here-now](skills/here-now/) | Workflow | native | Security-hardened file publishing via [here.now](https://here.now). Based on [heredotnow/skill](https://github.com/heredotnow/skill) v1.11.0 |
| [vercel-domain-search](skills/vercel-domain-search/) | Workflow | native | Keyless batch domain availability + pricing via Vercel's registrar API — priced read-only shortlists; purchase/transfer out of scope (endpoints pinned, [provenance](skills/vercel-domain-search/PROVENANCE.md)) |
| [live-system-forensics](skills/live-system-forensics/) | Security | native | Live malware/persistence forensics: process, network, and startup audits with per-host allowlist baselines and drift detection |
| [auditing-agent-harnesses](skills/auditing-agent-harnesses/) | Security | native | Privacy/telemetry audits for agent harnesses and AI-coding desktop apps (Electron/asar, Tauri, thin-shell+sidecar), with re-audit triggers on version updates |
| [cleaning-disk-storage](skills/cleaning-disk-storage/) | System | native | Disk cleanup: scan temp/cache/build artifacts, tiered confirmations, trash-only removal, regeneration guidance |
| [tokens/crypto-market-rank](skills/tokens/crypto-market-rank/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Trending tokens, smart-money inflow, meme rank, social hype |
| [tokens/query-token-audit](skills/tokens/query-token-audit/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Honeypot/rug-pull detection, contract security audit |
| [tokens/query-token-info](skills/tokens/query-token-info/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Token metadata, price, klines, social links |
| [tokens/trading-signal](skills/tokens/trading-signal/) | Crypto | [binance-skills-hub](https://github.com/binance/binance-skills-hub) | Smart-money buy/sell signals with trigger prices |

Skills from vibekit are automatically synced via GitHub Actions. Upstream skills are synced manually via [sync-upstream](.github/workflows/sync-upstream.yml) — sources in [.upstream.yml](.upstream.yml).

## Usage

Copy skills into your agent's skills directory:

```bash
git clone https://github.com/shrwnsan/agents.git /tmp/agents
cp -r /tmp/agents/skills/* ~/.agents/skills/
```

Skills follow the `~/.agents/skills/` convention. Claude Code users should symlink or copy to `~/.claude/skills/` instead:

```bash
ln -s ~/.agents/skills ~/.claude/skills
# or
cp -r ~/.agents/skills/* ~/.claude/skills/
```

For platform-specific setup guides, see [docs/](docs/).

## Adding a skill

1. **Vet before merging** — read the SKILL.md and every bundled script end to end, then run once in a real consumer container with its output checked against a known-good expectation.
2. **Named gap** — not duplicating a skill already in this repo's table; if it supersedes one, the old skill is removed in the same commit.
3. **Vendor and pin** — third-party skills are copied at a recorded commit (Source column links the ref), never tracked to a moving branch; bumping a pinned ref re-triggers the full vetting pass.

Evaluated-and-rejected candidates go in [rejected-skills.json](rejected-skills.json), appended in the same turn as the decision — rejections only, since the table above is the acceptance record.

## Global rules

[global/AGENTS.md](global/AGENTS.md) holds the rules every agent follows in every repo: workspace layout, file safety, Git and GitHub conventions, and quality checks. A repo's own AGENTS.md or CLAUDE.md wins on conflict. The rules are personal, so adapt the Workspace section before reusing them.

Copy it to `~/.agents/AGENTS.md`, then point each harness's global path at that copy:

| Harness | Global instructions |
|---------|---------------------|
| Droid | `~/.agents/AGENTS.md` (read directly) |
| Claude Code | `~/.claude/CLAUDE.md` containing `@~/.agents/AGENTS.md` (an import, not a link) |
| Codex | `~/.codex/AGENTS.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |
| Pi | `~/.pi/agent/AGENTS.md` |
| Amp | `~/.config/AGENTS.md` |

```bash
mkdir -p ~/.agents
cp /tmp/agents/global/AGENTS.md ~/.agents/AGENTS.md   # clone from Usage above
ln -s ~/.agents/AGENTS.md ~/.codex/AGENTS.md          # same for the OpenCode, Pi, and Amp paths
```

`global/AGENTS.md` is the published copy. The live one is `~/.agents/AGENTS.md`: edit that, then copy it here to publish.

Don't link Gemini CLI or Qwen Code. Their memory tools append to their global files, which would write into the shared rules.

## Recipes

Recipes are upstream integration playbooks from the *Claw ecosystem (OpenClaw, Hermes). Unlike skills, they are **not** agent-executable capabilities — they are reference material documenting production-hardened integration architectures and patterns.

Tracked read-only from upstream repos. See [docs/research-001-claw-recipes-vs-skills.md](docs/research-001-claw-recipes-vs-skills.md) for context on the recipe vs skill distinction.

### Synced from upstream repos

- **twilio-voice-brain** — Phone-to-knowledge pipeline via Twilio + voice AI. From [garrytan/gbrain](https://github.com/garrytan/gbrain).

## License

Apache 2.0
