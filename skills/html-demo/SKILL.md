---
name: html-demo
description: Show an app working on a web page by drawing it live in HTML instead of recording it. A Mac-style window plays the app step by step, and every frame is a pure function of one clock, render(t), drawn on a fixed 1200 × 750 stage that one CSS scale fits to any width. The pointer is scripted and aims at elements measured from the DOM, labels and pictures come from the real app, a steps bar sits under the window, it plays only while on screen, and reduced motion gets designed end frames. Vanilla HTML/JS/CSS, no framework and no build step. Use when someone wants a product demo, an animated app window or hero, a feature walkthrough, "the UI animated and simulated in HTML", "like a screen recording but HTML", an interactive product tour on a landing or download page, or wants to replace screen recordings, GIFs or MP4s of their UI with crisp live HTML.
---

# HTML Demo

**Vanilla JavaScript · DOM/CSS.** One engine file, no dependencies and no build step: `scripts/demo-window.js` with `scripts/demo-window.css`. A complete working example lives in `example/index.html`. No video, canvas, WebGL or screen recording.

It looks recorded, but it's HTML. Each frame is computed, so it stays sharp at any size and pixel density, its words are real text, and it can loop, jump to a step, scrub, freeze for a screenshot and stand still for reduced motion, all from the same code.

**Boundary.** Use a browser-recording workflow when you need a real recording of a real browser as an MP4. Use a motion-design workflow when a page becomes a fixed-length film. Use this skill when the deliverable is a live window on a web page that shows an app working. (In this repo, `html-reel` covers the voice-cut vertical video.)

**Provenance.** Ported from Meng To's `html-demo` skill (extracted from fil.design/download, October 2026), pinned and transformed React → vanilla; see [PROVENANCE.md](PROVENANCE.md).

## The mechanism

**Every frame of the app is a pure function of one number.** A step's `draw(t, $, point)` sets everything inside the window at a fixed 1200 × 750 design size from `t` alone, where `t` is seconds into the step. One CSS scale (`--k = width / 1200`) then fits that stage to the window.

If you take that away, the demo breaks. When state lives in `setTimeout` chains, animation callbacks or effects, you can't jump to a step. It drifts after a hidden tab, screenshots differ between runs, and reduced motion catches it half-done. Designing responsively inside the window breaks it differently: text reflows at every width, the pointer misses its targets, and phones show a different app.

```html
<div id="demo"></div>
<script src="scripts/demo-window.js"></script>
<script>
  const { mount, ease, typed, glide, held } = HTMLDemo;

  // Times live at the top as names, so a step reads like a script.
  const SEND_AT = 4.3, DONE_AT = 6.9;

  // The app at 1200 × 750: markup built once per step, draw sets the rest.
  function agentStep(t, $, point) {
    const done = t >= DONE_AT;
    $('.progress').style.width = 100 * ease(t, SEND_AT + 0.1, DONE_AT) + '%';
    $('.status').textContent = done ? 'Done' : 'Working…';
    const c = glide(t, [
      [0, 2.8, 950, 640],                                   // rest
      [2.8, 3.5, point('send').x, point('send').y],         // glide to the real button
    ], [SEND_AT]);                                          // press
    return { cursor: { ...c, hide: t > SEND_AT + 0.6 } };
  }

  mount(document.getElementById('demo'), {
    steps: [
      { id: 'agent', name: 'Run the agent', dur: 7, html: appHTML(), draw: agentStep },
      // 3–5 steps, 4–8 s each
    ],
    tabs: ['Your app'],
    label: 'Your app, step by step',
  });
</script>
```

A step is `{ id, name, dur, html, draw }`. `html` is the app inside the window at 1200 × 750, built once when the step starts; `draw(t, $, point)` then sets every moving part from `t` alone, where `$(sel)` finds an element on the stage and `point(name)` reads the measured position of `[data-aim="name"]`. `draw` may return `{ cursor: { x, y, press, hide } }` to place the pointer, last, over everything. `mount` provides the window chrome, the clock, the scaling, the steps bar and the pointer; `ease`, `typed`, `cue`, `held` and `glide` are exported alongside it.

## Workflow

1. **Pick one example and use it everywhere.** Choose one believable subject you own, such as a product, a project or a document, and run every window on it. Never show a client's, partner's or real person's data. A window full of names you can't show is unusable, and different subjects in every window read as scraps.
2. **Gather references of the real UI before drawing anything.** Use screenshots, the docs' recordings (pull frames with `ffmpeg -ss 2 -i in.mp4 -frames:v 1 out.png`) and the app's source code. List the references for each step. Copy every label, menu item, toast and cost from the source with grep, never from memory. If a viewer who knows the app spots one invented word ("Processing…"), they stop believing the rest. When the app is fictional (a demo of a product that doesn't exist), write its copy once, in its own voice, and reuse it exactly across steps.
3. **Script the steps on paper.** A window gets 3–5 steps of 4–8 s, 18–30 s in all. Each step gets a beat to see the start (0.3–1 s), the action, the result appearing the way the app shows it (a working state, then the result), and at least 1 s holding on the result. Name the steps as the bar shows them, in 1–3 words ("Paste a link", "Inpaint").
4. **Write each step as named times, then derive state from `t`.** Use constants like `TYPE_FROM = 1.9, SEND_AT = 4.3, DONE_AT = 6.9`, then comparisons (`t >= SEND_AT`), `ease(t, a, b)` for anything that moves, `typed()` for typing and `cue()` for lists of changes. Keep times as constants at the top so the choreography reads like a script and can be retimed in one place.
5. **Draw the app at 1200 × 750 from those states.** Reuse the real app's markup and CSS where you can. Otherwise copy sizes from its stylesheet: rail width, top bar height, radii, type sizes. Prefix every class and `@keyframes` with the window's own prefix (`ximp-`, `xpic-`) and grep to confirm nobody else uses it.
6. **Choreograph the pointer like a person.** It arrives 0.3–0.6 s before a click, presses for 0.15–0.2 s, and glides 0.5–0.9 s between targets. Between actions it rests out of the way, and it fades (`hide`) when the viewer should look at the result. It must aim at real elements: give them `data-aim` and read `point(name)` inside `draw` — the engine measures each target against the stage after the step builds and once fonts load, so a font swap never moves the target out from under the pointer.
7. **Shoot, compare, fix: at least three rounds.** Take frames every 0.5–1 s through each step (a headless screenshot at `seek(t)` per frame, or `example/index.html` as the reference for how a finished window behaves) and put them side by side with the references. Ask: would someone who uses this app believe it's a recording? Fix structure (layout, sizes, wording) before polish (motion).
8. **Check the edges.** Look at the reduced-motion end frames, phone widths (390 px and 340 px), a hidden tab coming back, and the console.

## Rules, each with the failure it prevents

- **Draw from `t` alone; let CSS transitions only smooth between states.** A transition depends on the frame before it. So anything that must be exact when scrubbing, frozen or shot (progress, typed text, reveals, counters) comes from `t`. Transitions are fine for hovers, panel slides and the pointer's glide. The trade-off: after a scrub, those transitions settle late, by up to their own duration. Use `glide()` when the pointer must be exact too.
- **Fixed stage, one scale.** Design at 1200 × 750 (16:10, the window's view `aspect-ratio`) and scale the whole stage with `transform: scale(var(--k))` from a `ResizeObserver`, with `transform-origin: 0 0`. A responsive layout inside the window moves the pointer's targets, and the app looks different on every device.
- **Results appear the way the app shows them.** Show a working state (spinner, "Sending…", shimmer, marching threads), then the result, then a settle. A result that just pops in reads as a slideshow.
- **Use real results and real words.** Show output the app actually made, saved next to the page. Don't use stand-ins or lorem. If a step needs a result you don't have, make it in the real app, and ask the owner about any cost first. Made-up results are the first thing people notice.
- **Compress time honestly.** A run of minutes plays in seconds, but the numbers stay true: if the demo shows a total, the line items add up to it, and any timestamp or balance keeps moving the way the app moves it. Fil's hero shows 18 s of app time for every demo second ("Made 5 things in 2:14").
- **Play only when it can be seen.** The engine's one rAF loop runs only while the window is at least 30% on screen (`IntersectionObserver`), skips frames while `document.hidden`, and clamps `dt` to 0.25 s, so a returning tab never fast-forwards through a step. Re-render only when `t` has advanced. Without this, a page of several windows burns CPU off screen.
- **Reduced motion means designed end frames.** Under `prefers-reduced-motion: reduce`, the engine never starts the loop and each step shows `t = dur`, with every animation and transition off on the stage; the steps bar still works (a click shows that step's end). So write every end frame as a complete, good picture on its own. A half-made frame or a blank window is the failure.
- **One prefix per window, for classes and keyframes alike.** Two windows that each define `.card` or `@keyframes in` collide, and the stylesheet loaded last restyles the other window. You only see it on the page that loads both.
- **Measure targets from the DOM, not coordinates.** Hard-coded ones drift the first time a font loads or a label changes. Mark the target `data-aim="name"` and call `point(name)`; the engine measures the element's box against the stage and divides out `--k`, so it works inside positioned or transformed ancestors too. Aim at 55% across and 60% down, roughly where a hand lands; for a button at the edge of something, aim beyond it.
- **Give each step its own starting picture.** The stage is keyed by step id: a new step rebuilds `html` and fades in over 0.45 s. Put the state the step starts from into its `html` (the finished line item, the sent invoice), and let `draw` move only what moves during that step. If a step's `html` shows a state its `draw` never sets, that state flashes for one frame at the cut.
- **Load the real fonts inside the demo.** Fallback metrics change line breaks, so the pointer's aims miss. The engine re-measures aims once `document.fonts.ready` resolves, but load the font up front regardless.
- **Preload the next scene's pictures** (`new Image().src = …`) while the current one plays. Otherwise the next step starts with empty boxes on a cold cache.
- **Mark it as a picture for assistive tech.** The stage gets `role="img"` and an `aria-label` listing the steps, and keeps `pointer-events: none` and `user-select: none`. The steps bar uses real buttons with `aria-current="step"` and a visible focus ring. A screen reader should hear "Import a page: Paste a link, Open in Design, Edit with the agent", not 400 nodes of fake UI.
- **`<figure>` needs `margin: 0`.** The browser's default 40 px side margins take 80 px off a 390 px phone. The engine's own `<figure>` does this; if you wrap the window again, do it there too.

## Numbers that shipped

| what | value |
| --- | --- |
| stage | 1200 × 750, `--k = clientWidth / 1200` |
| steps | 3–5 per window, 4–8 s each, 18–30 s per window |
| hold on the result | ≥ 1 s |
| typing | ~50 characters/s (90 characters in 1.8 s); a person reads it, nobody waits for it |
| pointer glide | 0.5–0.9 s, `cubic-bezier(0.55, 0, 0.25, 1)`; arrive 0.3–0.6 s early |
| click | 0.15–0.2 s pressed (`held`), arrow scale 1.15 → 0.98 |
| step fade-in | 0.45 s, `cubic-bezier(0.2, 0.7, 0.1, 1)` |
| clock | rAF, `dt ≤ 0.25 s`, on-screen threshold 0.3 (0.15 for a big hero) |

## Verify

- [ ] A frozen frame (`seek(seconds)`, or `play(i)` under reduced motion) at the same `t` looks the same on every run.
- [ ] Every step was shot every 0.5–1 s and compared side by side with the real app's references.
- [ ] Every label, menu item and number in the UI was found in the app's source or a reference.
- [ ] Reduced motion shows complete end frames, and the steps bar still works.
- [ ] It pauses off screen and in a hidden tab, and doesn't fast-forward when it comes back.
- [ ] At 390 px and 340 px there's no sideways scroll, and the window keeps its 16:10.
- [ ] Classes and keyframes use the window's prefix only (checked with grep).
- [ ] The console is clean.

## Files

- `scripts/demo-window.js`: the engine. One file, no dependencies, loaded with a plain `<script>` (works from `file://`). Exports `HTMLDemo` with `mount`, `ease`, `typed`, `cue`, `held`, `glide`, `measureAims`.
- `scripts/demo-window.css`: the frame: window chrome, stage scaling, pointer, steps bar, reduced-motion switch.
- `example/index.html`: a complete working example — a fictional invoicing app ("Ledgerline") across four steps: New invoice, Add a line, Send, Apply payment. Open it directly in a browser; it doubles as the style reference for a finished window.
