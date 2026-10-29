---
name: hydra-headless
description: Render Hydra (hydra-synth) generative-visual patches in a headless browser without the silent failures, verify output with pixel statistics, record loops to WebM, and collapse pure-procedural patches into a ~3 KB fragment shader. Use when the user wants Hydra visuals generated, tested, screenshotted, recorded, embedded in a page, or made lighter — or when a headless WebGL canvas renders black and nobody knows why.
allowed-tools:
  - Bash(node *)
  - Bash(agent-browser *)
metadata:
  version: "1.0.0"
---

# Hydra Headless

Drive [Hydra](https://hydra.ojack.xyz) patches (the `hydra-synth` engine) in a
headless browser: render, verify, record, and — when a patch qualifies — port it
to a tiny standalone shader. Everything here was learned the hard way: Hydra
fails **silently** in headless contexts, so this skill is mostly about the
verification loop that catches it.

## Requirements

- Node 18+ and the `agent-browser` CLI on PATH (the [docker-agent-browser](../docker-agent-browser/) skill sets that up in containers).
- No API keys. The engine loads from a local file or the pinned jsdelivr URL.

## Pick the shape first

| Shape | Use for | Cost | See |
|---|---|---|---|
| **Full engine, live** | Interactive playgrounds, live-coded demos | ~1.4 MB engine; heavy on CPU/GPU | [render-verify.md](references/render-verify.md) |
| **Pre-rendered loop** (production pick for accents) | Hero bands, ambient backgrounds | One .webm, decode-only on visitors | [capture.md](references/capture.md) |
| **Micro shader** (port) | One pure-procedural patch on a tight budget | ~3 KB inline GLSL | [micro-shader.md](references/micro-shader.md) |

Prefer the pre-rendered loop for anything a visitor will see: live engines cost
visitors battery and CPU (measured ~2.5 cores under software GL vs ~1.5–1.7 for
the micro port of the same patch).

## Quick start

```bash
# 1. generate a test page with the traps pre-handled
node "${CLAUDE_SKILL_DIR}/scripts/make-test-page.mjs" \
  --patch "osc(3,0.02,1.2).color(0.05,0.13,0.13).add(osc(4,0.015,1.0).color(0.34,0.29,0.17),0.55).modulate(osc(2,0.01),0.15).out()" \
  --out page.html --width 800 --height 450 --gate --fallback "#0e3a3a,#cbb87f"

# 2. render headless — wait for the page title to flip to HYDRA-LIVE
agent-browser set viewport 800 450
agent-browser open file://"$PWD"/page.html   # or serve the dir and open the URL
sleep 5                                       # feedback patches need warmup

# 3. verify pixels — do NOT trust the console or readPixels
agent-browser screenshot shot.png
node "${CLAUDE_SKILL_DIR}/scripts/png-lum.mjs" shot.png
#   → {"mean":43.8,"min":9,"max":66,"litPct":85.5}  = alive and lit
#   → {"mean":0,"litPct":0}                          = silent black, debug below

# 4. verify the pause gate actually holds frames
agent-browser eval "window.__animGate.set(false); window.__animGate.isOn()"
```

Offline checks after any edit to the generator: `node make-test-page.mjs --selftest`.

## The five silent failures (all verified first-hand)

1. **Nonexistent transforms render black.** Calling something like
   `modulateScroll` that the engine does not have throws internally and the
   canvas stays black with no visible error. Add the `window.onerror` hook (the
   generator does) and check `window.__hydraError`.
2. **Feedback patches need warmup.** Patches whose output feeds back into
   themselves start black and accumulate — a screenshot seconds too early is
   indistinguishable from a failure. Wait for `HYDRA-LIVE` (the generator polls
   for real non-black pixels, in-frame) plus a settle pause.
3. **`readPixels` / `drawImage` outside a rAF callback reads zeros.** The WebGL
   drawing buffer is cleared after compositing (`preserveDrawingBuffer` is off).
   Read in-frame or verify from a screenshot instead.
4. **`MediaRecorder` produces 0-byte files headless** (compositor-dependent).
   Record via WebCodecs instead — [capture.md](references/capture.md).
5. **Agent-side screenshot tools may hand back a URL, not pixels.** Verify
   dimensions and luminance from the PNG file itself (`png-lum.mjs`), not from
   what a tool claims it captured.

## Integration rules for shipped pages

- Respect `prefers-reduced-motion` (show a static frame or gradient fallback).
- Pause when `document.hidden` and when off-screen — the `--gate` flag installs
  `window.__animGate` which stops the engine's frames without forking it; wire
  it to visibility handlers and any Pause control.
- License: `hydra-synth` is AGPL-3.0. A live embed ships the library; the
  transcribed math in the micro-shader port **inherits AGPL-3.0** — credit the
  project and note the license on the page.
