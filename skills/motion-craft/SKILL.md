---
name: motion-craft
description: >-
  Animation and interaction craft for web UI — motion decisions, easing,
  springs, micro-interactions, and transition performance. Use when building
  or polishing any animated or interactive element (buttons, modals, drawers,
  toasts, tooltips, popovers, lists, gestures, theme switches), reviewing UI
  code for motion quality, or diagnosing why an interface feels sluggish,
  janky, or subtly off. Aesthetic direction (palette, typography, layout
  identity) is the frontend-design skill's job; this one owns the execution
  craft that makes an interface feel right. Triggers on: "animation",
  "transition", "easing", "spring", "feels sluggish", "polish this
  interaction", "micro-interaction".
---

# Motion Craft

Polish comes from a pile of small details that compound. In a world where
everyone's software is good enough, feel is the differentiator — most details
are never consciously noticed, and that is the point: when a feature behaves
exactly as someone assumes it should, they proceed without a second thought.

Rules below use exact values, not ranges to approximate. `cubic-bezier(0.2, 0,
0, 1)` is not `cubic-bezier(0.4, 0, 0.2, 1)`, and `0.96` is not `0.95`. Use
what is written. Respect the project's existing component library, tokens, and
density, and match its motion language except where a rule here prescribes an
exact interaction.

## The animation decision framework

Before writing any animation code, answer these in order.

### 1. Should this animate at all?

Ask: how often will users see it?

| Frequency | Decision |
| --- | --- |
| 100+ times/day (keyboard shortcuts, command palette toggle) | No animation. Ever. |
| Tens of times/day (hover effects, list navigation) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare/first-time (onboarding, feedback forms, celebrations) | Can add delight |

**Never animate keyboard-initiated actions.** They repeat hundreds of times a
day; animation makes them feel slow, delayed, and disconnected from the user.

### 2. What is the purpose?

Every animation needs a clear answer to "why does this animate?"

- **Spatial consistency** — a toast enters and exits the same direction, so swipe-to-dismiss feels intuitive
- **State indication** — a morphing feedback button shows the state change
- **Explanation** — an explanatory animation that shows how a feature works
- **Feedback** — a button scales down on press, confirming the interface heard the user
- **Preventing jarring changes** — elements appearing or disappearing without transition feel broken

If the only answer is "it looks cool" and users will see it often, don't animate.

### 3. What easing?

- Entering or exiting → **ease-out** (starts fast, feels responsive)
- Moving or morphing on screen → **ease-in-out**
- Hover or color change → **ease**
- Constant motion (marquee, progress bar) → **linear**
- Default → **ease-out**

Built-in CSS easings are too weak; use stronger custom curves:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);        /* strong ease-out for UI interactions */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);    /* strong ease-in-out for on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);     /* iOS-like drawer curve */
```

**Never use `ease-in` for UI animations.** It delays the initial movement —
the exact moment the user is watching most closely. Find and tune curves at
easings.co or easing.dev instead of inventing them from scratch.

### 4. How fast?

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing/explanatory | Can be longer |

**UI animations stay under 300ms.** A 180ms dropdown feels more responsive
than a 400ms one. Perceived speed is real speed: a fast-spinning spinner makes
loading feel faster at identical load time, and `ease-out` at 200ms *feels*
faster than `ease-in` at 200ms because movement starts immediately.

## Quick values

- **Press feedback:** `transform: scale(0.97)` on `:active`, `transition: transform 160ms ease-out`. Applies to any pressable element; keep scale in 0.95–0.98.
- **Entries:** never from `scale(0)` — nothing in the real world appears from nothing. Start at `scale(0.95)` or higher plus `opacity: 0`.
- **Popovers** scale from their trigger, not center: `transform-origin: var(--transform-origin)`. **Exception: modals stay centered** — they aren't anchored to a trigger.
- **Tooltips:** initial delay prevents accidental activation; once one is open, adjacent tooltips open instantly with `transition-duration: 0ms`.
- **Exits are faster and smaller than enters** — a small fixed `translateY`, not full height, `ease-out` both directions. Slow where the user is deciding, fast where the system responds.
- **Transitions, not keyframes**, for anything triggered rapidly — transitions retarget mid-flight, keyframes restart from zero.
- **Stagger** group entrances 30–80ms per item; never block interaction while stagger plays. Keep high-frequency interactions unstaggered.
- **Blur trick:** when a crossfade feels off, add `filter: blur(2px)` during the transition — it blends the two overlapping states into one perceived transformation. Keep blur under 20px (expensive in Safari).
- **Motion restraint:** high-frequency interactions get instant feedback or a ≤150ms opacity/color transition. Every animated state change also needs a static cue — color, icon, or label. Motion is never the only feedback channel.

## Review output format

When reviewing UI code, report findings as one markdown table — never a
Before/After list:

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | Specify exact properties; avoid `all` |
| `transform: scale(0)` | `transform: scale(0.95); opacity: 0` | Nothing appears from nothing |
| `ease-in` on dropdown | `ease-out` with custom curve | `ease-in` delays the moment users watch most |
| No `:active` state | `transform: scale(0.97)` on `:active` | Buttons must feel responsive to press |
| `transform-origin: center` on popover | `transform-origin: var(--transform-origin)` | Popovers scale from their trigger (modals exempt) |

## Review checklist

| Issue | Fix |
| --- | --- |
| `transition: all` | Specify exact properties |
| `scale(0)` entry | Start from `scale(0.95)` with `opacity: 0` |
| `ease-in` on a UI element | Switch to `ease-out` or a custom curve |
| `transform-origin: center` on popover | Set to trigger location (modals exempt) |
| Animation on keyboard action | Remove entirely |
| Duration > 300ms on a UI element | Reduce to 150–250ms |
| Hover animation without media query | Gate behind `@media (hover: hover) and (pointer: fine)` |
| Keyframes on a rapidly-triggered element | Use CSS transitions for interruptibility |
| Motion-library `x`/`y` props under load | Use the full `transform` string for hardware acceleration |
| Same enter/exit speed | Make exit faster than enter |
| Elements all appear at once | Stagger 30–80ms apart |
| Whole-page crossfade on theme switch | Suppress transitions for the swap, restore next frame |

## Reference files

Read on demand — don't load these for every task:

- [`reference/techniques.md`](reference/techniques.md) — component patterns
  (press, popovers, tooltips, enter/exit, `@starting-style`), clip-path
  recipes, transform mastery, springs, gesture handling, component principles.
- [`reference/performance.md`](reference/performance.md) — what may animate,
  main-thread traps, WAAPI, `prefers-reduced-motion`, debugging technique.

---

Adapted from Emil Kowalski's `emil-design-eng` skill (MIT) — see PROVENANCE.md
for source pin and the full list of departures.
