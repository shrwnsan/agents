# PROVENANCE — hydra-headless

Status: **native** (built in this repo from first-hand verified work).
Derived knowledge from one third-party library, recorded below.

## Source pin

- **hydra-synth 1.4.0** (AGPL-3.0) — <https://github.com/ojack/hydra-synth>.
  Default engine URL pinned: `https://cdn.jsdelivr.net/npm/hydra-synth@1.4.0/dist/hydra-synth.js` (UMD, global `Hydra`).
- Supporting pins (capture path): `webm-muxer` **5.1.4** (global `WebMMuxer`),
  `mp4-muxer` **5.2.1** (IIFE `/build/mp4-muxer.js`, global `Mp4Muxer`),
  `agent-browser` **0.27.1** (the CLI this was validated with).

## License exclusion

`references/micro-shader.md` transcribes the `osc` sine formulas and operator
semantics from hydra-synth 1.4.0. That file **inherits AGPL-3.0** and is
excluded from this repo's Apache-2.0 default (same vendor-and-pin policy as the
proprietary vendored skills). Anyone porting per that reference must credit
hydra-synth and ship the derived shader under AGPL-3.0. Everything else in this
skill (page skeletons, gate, verification method, capture pipeline, scripts) is
original and Apache-2.0.

## Live validation (2026-10-29, this container)

- Full loop exercised end-to-end with the shipped scripts: generator →
  headless render (agent-browser + Chromium/SwiftShader) → in-frame ready flag
  flipped to `HYDRA-LIVE` → screenshot → `png-lum.mjs` luminance verification
  (mean 43.8, litPct 85.5%) → rAF gate hold/release verified in-page.
- Generator `--selftest`: deterministic PASS (9/9 checks).
- Capture pipeline previously validated the same day: 10 s 800×450 VP9 loop
  (~378 KB) encoded via WebCodecs + webm-muxer and shipped; MediaRecorder on
  the same canvas produced a 0-byte file (the reason capture.md exists).
- Micro-shader port of an accent patch measured against the engine: band
  luminance 39.5 (port) vs 38.7 (engine); CPU ~150–170% vs ~250% (top-two
  browser processes summed, identical sampling, back-to-back).
- The five silent failures in SKILL.md are each reproduced first-hand, not
  folklore (nonexistent transform → black; warmup; out-of-frame readback zeros —
  including inside this skill's own generator, caught and fixed during
  validation; MediaRecorder 0-byte; tool-returned screenshot URL instead of
  pixels).

## Known fragilities

- Absolute luminance values are GPU/driver-dependent (SwiftShader vs real GL) —
  comparisons are relative by design; the skill never ships absolute thresholds.
- jsdelivr availability: for reproducible/airgapped runs, vendor the engine
  file (`--engine ./hydra-synth.js`) instead of the CDN default.
- MediaRecorder behavior varies by Chromium build/platform; where it works it
  is still the wrong tool here because headless reliability cannot be assumed.

## Refresh runbook

1. Bump the engine pin (SKILL.md, references/render-verify.md, and the
   `DEFAULT_ENGINE` constant in `scripts/make-test-page.mjs`) deliberately.
2. Re-run: `--selftest`, one full render+verify pass, and one gate check.
3. If hydra-synth's API surface changed, re-verify the osc transcription in
   `references/micro-shader.md` against the new source line before shipping the
   reference forward.
