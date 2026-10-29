# Micro shader: collapsing a Hydra patch to ~3 KB

A pure-procedural patch (no feedback, no frame-to-frame state) is a pure
function of pixel coordinates and time — which means it collapses to **one
WebGL1 fragment shader**. Measured outcome on a real accent patch: ~3 KB inline
(vs 208 KB engine), identical band luminance (39.5 vs 38.7), and ~60% of the
engine's CPU. The full engine stays the pick for anything interactive or
feedback-based; this is the port for one hero patch on a tight budget.

## When a patch qualifies

- Only `osc`, `color`, `add`, `mult`, `modulate`, `modulateScale`, `scale`,
  `kaleid`, `shape`, etc. with constant arguments — no `.diff`, no `src()`
  feeding a previous frame, no `prev` buffer.
- The patched output looks static-structure + time-drift. If it smears or trails
  (feedback), it does not collapse.

## `osc` is three sines

Extracted from `hydra-synth.js` 1.4.0 (~line 1752) — `st` is UV coordinates,
`time` seconds, and `freq`/`speed`/`offset` the osc arguments:

```glsl
float r = sin((st.x - offset * 2.0 / freq + time * sync) * freq) * 0.5 + 0.5;
float g = sin((st.x + time * sync) * freq) * 0.5 + 0.5;
float b = sin((st.x + offset / freq + time * sync) * freq) * 0.5 + 0.5;
```

(Only `st.x` — Hydra's osc is horizontal by default; rotate by transforming
`st` before the sines.)

## Operator semantics (as the engine composes them)

| Hydra | GLSL equivalent |
|---|---|
| `.color(r, g, b)` | channel multiply: `vec3(r,g,b) * vec3(oscR, oscG, oscB)` |
| `.add(c2, amt)` | `c0 + c2 * amt` |
| `.mult(c2)` | `c0 * c2` |
| `.modulate(c2, amt)` | coordinate warp: `st += (c2.xy - 0.5) * amt`, with `c2` sampled at the **unwarped** `st` |

`.modulate` is the one that trips ports: the modulator is evaluated at the
original coordinate, then warps it.

## Page skeleton

Fullscreen triangle (no vertex buffer needed), DPR capped (1.5 is plenty for
soft gradients), one uniform (`u_time`) advanced by your own rAF loop:

```js
const gl = canvas.getContext('webgl');
// attribute-less draw:
gl.drawArrays(gl.TRIANGLES, 0, 3);   // verts generated in the vertex shader: [-1,-1, 3,-1, -1,3]
```

Owning the rAF loop means pausing = stop advancing `u_time` — no gate needed,
the clock itself stops. Same `prefers-reduced-motion` / `document.hidden`
rules apply.

## Verify the port, don't assume it

1. Screenshot the engine rendering the original patch and the shader rendering
   the port — same viewport, same crop of the visual band.
2. `node png-lum.mjs` both crops. Luminance means should land close (verified
   example: 38.7 engine vs 39.5 port — an ambient patch won't match per-pixel;
   match the *distribution*: mean within a few points, similar spread).
3. Sample CPU back-to-back with the identical method for both pages if you
   claim efficiency numbers anywhere.

## License — do not skip

The formulas above are transcribed from `hydra-synth` (AGPL-3.0). A port that
embeds them **inherits AGPL-3.0** for that code. Ship it with a visible credit
line (e.g. "shader math transcribed from hydra-synth, AGPL-3.0") and treat the
file as AGPL, not as your project's license. Writing the sines "from scratch"
does not dodge this — they are the engine's osc, recognized as such.
