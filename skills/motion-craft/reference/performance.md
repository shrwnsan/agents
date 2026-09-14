# Performance and Accessibility

What may animate, main-thread traps, reduced motion, and how to debug motion.

## Only animate transform and opacity

These skip layout and paint and run on the GPU. Animating `padding`, `margin`,
`height`, or `width` triggers layout + paint + composite on every frame.

## CSS variables are inheritable

Changing a CSS variable on a parent recalculates styles for all children. In a
drawer with many items, updating `--swipe-amount` on the container causes an
expensive recalc per move. Write `transform` directly on the element instead:

```js
// Bad: recalcs every child
element.style.setProperty('--swipe-amount', `${distance}px`);

// Good: affects only this element
element.style.transform = `translateY(${distance}px)`;
```

## Motion-library shorthand props are not hardware-accelerated

Framer Motion's `x`, `y`, `scale` props run on the main thread via
requestAnimationFrame. Under load (page loads, heavy scripts) they drop
frames. The full `transform` string stays on the compositor:

```jsx
// Not hardware accelerated — convenient but drops frames under load
<motion.div animate={{ x: 100 }} />

// Hardware accelerated — smooth even when the main thread is busy
<motion.div animate={{ transform: "translateX(100px)" }} />
```

Real-world case: a dashboard tab animation built on shared-layout animations
dropped frames during page loads; switching it to CSS animations fixed it.

## CSS animations beat JS under load

CSS animations run off the main thread and stay smooth while the browser is
busy. Rule of thumb: **CSS for predetermined animations, JS for dynamic and
interruptible ones** (springs, gestures).

## WAAPI: JS control at CSS performance

The Web Animations API is hardware-accelerated, interruptible, and
dependency-free:

```js
element.animate(
  [{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
  { duration: 1000, fill: 'forwards', easing: 'cubic-bezier(0.77, 0, 0.175, 1)' }
);
```

## will-change, sparingly

Only for `transform`, `opacity`, and `filter` — the properties the GPU can
composite. Never `will-change: all`. Add it when you observe first-frame
stutter, not preemptively.

## prefers-reduced-motion

Reduced motion means **fewer and gentler animations, not zero**. Keep opacity
and color transitions that aid comprehension; remove movement and position
animation:

```css
@media (prefers-reduced-motion: reduce) {
  .element {
    animation: fade 0.2s ease;  /* opacity only — no transform-based motion */
  }
}
```

```jsx
const shouldReduceMotion = useReducedMotion();
const closedX = shouldReduceMotion ? 0 : '-100%';
```

## Gate hover animations to pointer devices

Touch devices fire hover on tap, causing false positives:

```css
@media (hover: hover) and (pointer: fine) {
  .element:hover {
    transform: scale(1.05);
  }
}
```

## Debugging

- **Slow motion:** raise the duration 2–5× temporarily or use DevTools'
  animation inspector to replay at 10%. Watch for: two distinct states
  overlapping during crossfades, abrupt easing start/stop, wrong
  transform-origin, desynced multi-property transitions.
- **Frame by frame:** step through coordinated properties in Chrome DevTools'
  Animations panel — inter-property timing issues are invisible at full speed.
- **Real devices:** for touch interactions (drawers, swipes), test on physical
  hardware via a local dev server and remote devtools. Simulators miss
  gesture feel.
