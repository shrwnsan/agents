# Techniques

Component patterns, clip-path recipes, transform mastery, springs, and
gestures. Values here are exact — use them as written.

## Component patterns

### Pressable elements

```css
.button {
  transition: transform 160ms ease-out;
}

.button:active {
  transform: scale(0.97);
}
```

Applies to any pressable element; keep the scale in 0.95–0.98. Combine with
the blur trick below for polished state swaps:

```css
.button-content {
  transition: filter 200ms ease, opacity 200ms ease;
}

.button-content.transitioning {
  filter: blur(2px);
  opacity: 0.7;
}
```

### Entries: never from scale(0)

```css
/* Bad */
.entering { transform: scale(0); }

/* Good */
.entering { transform: scale(0.95); opacity: 0; }
```

Even a barely-visible initial scale reads as a real object arriving, not
something materializing from nowhere.

### Origin-aware popovers

Popovers should scale in from their trigger. Default `transform-origin:
center` is wrong for almost every popover:

```css
.popover {
  transform-origin: var(--transform-origin);  /* Base UI provides the variable */
}
```

Exception: modals keep `transform-origin: center` — they are viewport-centered,
not anchored to a trigger.

### Tooltips: skip delay on subsequent hovers

Delay the first tooltip to prevent accidental activation; once one is open,
adjacent tooltips open instantly:

```css
.tooltip {
  transition: transform 125ms ease-out, opacity 125ms ease-out;
  transform-origin: var(--transform-origin);
}

.tooltip[data-starting-style],
.tooltip[data-ending-style] {
  opacity: 0;
  transform: scale(0.97);
}

.tooltip[data-instant] {
  transition-duration: 0ms;
}
```

### Transitions over keyframes for interruptible UI

Transitions can be interrupted and retargeted mid-animation; keyframes restart
from zero. For anything triggered rapidly (toasts, toggles), use transitions:

```css
/* Interruptible — good for dynamic UI */
.toast { transition: transform 400ms ease; }

/* Not interruptible — avoid for dynamic UI */
@keyframes slideIn {
  from { transform: translateY(100%); }
  to   { transform: translateY(0); }
}
```

Reserve keyframes for staged sequences that run once.

### Enter states with @starting-style

The modern CSS way to animate entry without JavaScript:

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 400ms ease, transform 400ms ease;

  @starting-style {
    opacity: 0;
    transform: translateY(100%);
  }
}
```

This replaces the `useEffect` → `setMounted(true)` pattern. Where browser
support doesn't allow it, fall back to the `data-mounted` attribute pattern.

### Stagger group entrances

```css
.item {
  opacity: 0;
  transform: translateY(8px);
  animation: fadeIn 300ms ease-out forwards;
}

.item:nth-child(1) { animation-delay: 0ms; }
.item:nth-child(2) { animation-delay: 50ms; }
.item:nth-child(3) { animation-delay: 100ms; }
.item:nth-child(4) { animation-delay: 150ms; }

@keyframes fadeIn {
  to { opacity: 1; transform: translateY(0); }
}
```

Keep gaps at 30–80ms — longer reads as slow. Stagger is decorative: never
block interaction while it plays. For an infrequent staged entrance where
sequence communicates hierarchy, split content into semantic chunks and
stagger those (~100ms) rather than animating one container.

### Theme switches: suppress transitions

A theme flip changes color, background, border, and shadow on nearly every
element at once — every transition fires and the switch smears. Inject
`*, *::before, *::after { transition: none !important; }`, force a reflow,
then remove it on the next frame.

### Motion-library page loads

Use `initial={false}` on `AnimatePresence` to keep enter animations off the
first render, and check that intentional page entrances survive.

## Transform mastery

### Percentages are relative to the element itself

`translateY(100%)` moves an element by its own height regardless of actual
dimensions — this is how toasts and drawers hide before animating. Prefer
percentages over hardcoded pixels; they adapt to content.

### scale() scales children too

Unlike width/height, `scale()` scales content proportionally — font, icons,
all of it. A feature, not a bug, for press feedback.

### transform-origin

Every element transforms from an anchor point (default: center). Set it to
match where the trigger lives for origin-aware interactions.

### 3D depth without JavaScript

```css
.wrapper { transform-style: preserve-3d; }

@keyframes orbit {
  from { transform: translate(-50%, -50%) rotateY(0deg) translateZ(72px) rotateY(360deg); }
  to   { transform: translate(-50%, -50%) rotateY(360deg) translateZ(72px) rotateY(0deg); }
}
```

Orbits, coin flips, and depth effects are all possible with pure CSS.

## clip-path for animation

`clip-path: inset(top right bottom left)` clips a rectangular region; each
value "eats" into that side. Fully hidden from the right is
`inset(0 100% 0 0)`; fully visible is `inset(0 0 0 0)`.

### Reveal from left to right

```css
.overlay {
  clip-path: inset(0 100% 0 0);
  transition: clip-path 200ms ease-out;
}

.button:active .overlay {
  clip-path: inset(0 0 0 0);
  transition: clip-path 2s linear;
}
```

### Tabs with perfect color transitions

Duplicate the tab list; style the copy as "active" (different background and
text color); clip the copy so only the active tab shows; animate the clip on
tab change. A seamless color shift that timing individual color transitions
can never match.

### Hold-to-delete

`clip-path: inset(0 100% 0 0)` on a colored overlay; on `:active` transition
to `inset(0 0 0 0)` over 2s linear (slow and deliberate — the user is
deciding); on release snap back at 200ms ease-out (fast — the system
responds). Add `scale(0.97)` on the button for press feedback.

### Image reveals on scroll

Start at `clip-path: inset(0 0 100% 0)`; animate to `inset(0 0 0 0)` on
viewport entry via `IntersectionObserver` or `useInView` with
`{ once: true, margin: "-100px" }`.

### Comparison sliders

Overlay two images; clip the top one with `inset(0 50% 0 0)`; drive the right
inset from drag position. No extra DOM, fully hardware-accelerated.

## Springs

Springs settle from physical parameters instead of fixed durations — more
natural for anything with momentum.

**When to use springs:** drag interactions with momentum; elements that should
feel alive; gestures that can be interrupted mid-animation; decorative
mouse-tracking.

**Mouse tracking needs a spring.** Tying visuals directly to mouse position
feels artificial because it lacks motion. Interpolate with a spring:

```jsx
import { useSpring } from 'framer-motion';

// Without spring: feels artificial, instant
const rotation = mouseX * 0.1;

// With spring: natural, has momentum
const springRotation = useSpring(mouseX * 0.1, { stiffness: 100, damping: 10 });
```

This works because the animation is decorative. A functional graph in a
banking app should not animate at all — know when decoration helps.

**Configuration** — Apple-style duration/bounce is easier to reason about:

```js
{ type: "spring", duration: 0.5, bounce: 0.2 }
```

Physics params give more control:

```js
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }
```

Keep bounce subtle (0.1–0.3) and only for drag-to-dismiss and playful
interactions; avoid it in most UI contexts.

**Interruptibility is the killer feature:** springs keep their velocity when
interrupted; CSS animations and keyframes restart from zero. Click an expanded
item then quickly press Escape — a spring reverses smoothly from wherever it
is.

## Gestures

### Momentum-based dismissal

Don't require dragging past a threshold — compute velocity:

```js
const timeTaken = new Date().getTime() - dragStartTime.current.getTime();
const velocity = Math.abs(swipeAmount) / timeTaken;

if (Math.abs(swipeAmount) >= SWIPE_THRESHOLD || velocity > 0.11) {
  dismiss();
}
```

A quick flick should be enough regardless of distance.

### Damping at boundaries

Dragging past a natural boundary (a drawer already at top) applies increasing
resistance — the more they drag, the less it moves. Real objects slow down
before they stop; allow the over-drag with friction instead of an invisible
wall.

### Pointer capture and multi-touch

Once dragging starts, capture the pointer so the drag survives leaving the
element bounds. Ignore additional touch points after a drag begins — switching
fingers mid-drag otherwise makes the element jump.

## Component principles

1. **Developer experience is key.** No hooks, no context, no complex setup.
   The less friction to adopt, the more people use it.
2. **Good defaults matter more than options.** Ship excellent out of the box —
   default easing, timing, and visual design. Most users never customize.
3. **Naming creates identity.** A component name can sacrifice discoverability
   for memorability.
4. **Handle edge cases invisibly.** Pause timers when the tab hides. Fill gaps
   between stacked items with pseudo-elements to preserve hover state. Capture
   the pointer during drags. Users never notice — that is exactly right.
5. **Transitions, not keyframes, for dynamic UI** (see above).
6. **Build documentation people can touch.** Interactive examples with
   ready-to-use snippets lower adoption barriers.

### Cohesion

An animation feels satisfying partly because everything fits: easing and
duration match the component's design, the page, the name. Match motion to
personality — a playful component can be bouncier; a professional dashboard
should be crisp and fast.

### Pair opacity with height in list transitions

When items enter and exit a list, the opacity change must work with the height
animation. This is trial and error — adjust until it feels right.

### Review with fresh eyes

Review animations the next day; play them in slow motion or frame by frame.
Timing issues invisible at full speed show up immediately. For touch
interactions, test on real hardware — the simulator misses gesture feel.
