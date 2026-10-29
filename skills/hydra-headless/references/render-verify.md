# Render + verify: the live-engine path

## Page skeleton (what `make-test-page.mjs` emits, and why)

Every headless Hydra page needs four things the engine will not give you:

```html
<script>
  // 1. error surface — engine failures are invisible otherwise
  window.__hydraError = null;
  window.onerror = function (msg, src, line) {
    window.__hydraError = msg + ' @' + line;
    document.title = 'HYDRA-ERROR';
    return false;
  };
</script>
<!-- 2. optional rAF gate — MUST be installed BEFORE the engine script tag -->
<script src="hydra-synth@1.4.0/dist/hydra-synth.js"></script>
<script>
  // 3. explicit canvas + audio off (headless has no audio device)
  var h = new Hydra({
    canvas: document.getElementById('c'),
    width: 800, height: 450,
    autoStart: true, detectAudio: false
  });
  osc(3, 0.02, 1.2).out();   // 4. patch MUST end in .out() — nothing renders otherwise
</script>
```

Engine pin: `https://cdn.jsdelivr.net/npm/hydra-synth@1.4.0/dist/hydra-synth.js`
(UMD, exposes the global `Hydra`). For airgapped work, vendor the file next to
the page — `make-test-page.mjs --engine ./hydra-synth.js` copies it for you.

## The rAF pause gate

Install before the engine loads — `regl` (the engine's WebGL wrapper) resolves
`requestAnimationFrame` at call time, so a gate installed earlier pauses the
synth with no fork and no engine edit:

```js
(function () {
  var q = [], on = true, real = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) { if (on) return real(cb); q.push(cb); return 0; };
  window.__animGate = {
    set: function (v) { on = v; if (v) q.splice(0).forEach(real); },
    isOn: function () { return on; }
  };
})();
```

Wire it to `visibilitychange`, `IntersectionObserver`, `prefers-reduced-motion`,
and any user-facing Pause button. Gate off = no GPU work at all, not a hidden
render. The pure-procedural micro shader doesn't need this (it owns its own rAF
loop — pausing that stops the clock entirely).

## Verification recipe

Never trust: console silence, `document.title`, wall-clock time, or
`readPixels` from outside a frame. Trust pixels from the PNG:

```bash
agent-browser screenshot shot.png
node png-lum.mjs shot.png          # whole page
node png-lum.mjs shot.png 0,200,800,250   # crop: x,y,w,h — e.g. a hero band
```

Reading the stats (8-bit luminance 0–255):

- `mean 0, litPct 0` — silent black. Check `__hydraError`; check warmup; check
  `.out()` is present; check the engine script actually loaded (network panel or
  `typeof Hydra`).
- `mean` slowly rising across screenshots seconds apart — feedback warmup
  working (measured 13 → 16 mean over the first seconds on a restrained patch).
- `litPct` in the 10–90% range with nonzero `min`/`max` spread — alive. A
  restrained accent patch measured mean ≈ 39–44, lit 10–86% depending on crop.
- Absolute numbers vary with GPU/driver (SwiftShader vs real GL). Compare
  relative values (this render vs that render, this crop vs that crop), never
  against absolute thresholds.

## Cost planning (measured, software GL, top-two browser processes summed)

| Variant | CPU while animating |
|---|---|
| Full engine live | ~250% (≈2.5 cores, continuous) |
| Micro-shader port of the same patch | ~150–170% |
| Pre-rendered .webm loop | decode only (~a few % on hardware decode) |

On real GPUs the engine is cheaper than SwiftShader numbers suggest, but the
ranking holds: the engine is the expensive shape, decode-only media is the
cheap one. Sample consistently (same method, back-to-back) when comparing.

## Reduced-motion and hidden-tab rules

- `prefers-reduced-motion: reduce` → static frame (screenshot of the patch) or
  the `--fallback` gradient; never auto-play.
- `document.hidden` → gate off. Off-screen (IntersectionObserver) → gate off.
- Give users a visible Pause when motion is decorative.
