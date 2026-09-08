---
name: extract-design-tokens
description: >
  Extract a site's design tokens and read its taste. Loads a live URL (or
  local HTML file) in agent-browser, samples the rendered visual language, and
  produces tokens.css (semantic design tokens, light+dark), a one-line design
  read, three taste dials scored 1-10 with evidence, and optional audit notes.
  Use when asked to "extract design tokens", "pull the design language /
  visual language from this site", "clone the look of <site>", "grab the
  style/tokens from <url>", or "audit this page's design".
user-invocable: true
---

# Extract Design Tokens

Pull a site's design tokens and read its taste. The mechanical sampling is a
script; the judgment — semantic naming, the design read, the dials, the audit
— is yours. Method inspired by the taste-skill suite (design read + dials)
and the designer-skills semantic token schema; this is a native implementation
on agent-browser.

## Workflow

1. Run the sampler:

```bash
node "${SKILL_DIR:-.}/scripts/sample.mjs" "<url-or-file>" --out /tmp/sample.json
```

It opens the page in agent-browser, waits for network idle, samples computed
styles (custom properties, color/font/spacing/radius frequencies, motion
counts), and prints JSON. `--keep-open` leaves the browser open for follow-up
`agent-browser` probes; local files work via their `file://` path.

2. If `customProps` is empty, the site's stylesheets were cross-origin or
   runtime-injected — fall back to the frequency data (`colors`, `fonts`,
   `type`, `spacing`), or probe specific elements:
   `agent-browser eval "getComputedStyle(document.querySelector('h1')).color"`.

3. Produce the four outputs below. Deliver `tokens.css` as a file; deliver the
   design read, dials, and audit inline in your response.

## Output 1 — tokens.css

Semantic tokens named by ROLE, never by value. Required structure:

```css
/* extract-design-tokens — source: <url> — <date> */
:root {
  --bg: ...; --fg: ...; --muted: ...; --border: ...; --card: ...;
  --accent: ...; --accent-hover: ...;
  --input-bg: ...; --input-border: ...;
  --font-display: ...; --font-body: ...;
  /* spacing scale: pick 4-6 values from the spacing frequencies */
  --space-1: ...; --space-2: ...; --space-3: ...; --space-4: ...;
  /* type ramp from the h1..p sizes */
  --text-xs: ...; --text-sm: ...; --text-md: ...; --text-lg: ...; --text-xl: ...;
  --radius: ...;
}
[data-theme="dark"] { /* remap bg/fg/muted/border/card/accent */ }
```

Rules: dark mode is required (if the source has none, derive one that keeps
contrast; say so in a comment); one `--accent` (primary action, not
decorative filler); opacity tints of tokens are the sanctioned way to shade.
If the page ships its own custom properties, prefer adopting their names.

## Output 2 — design read (one line)

Page kind + audience + vibe + aesthetic family, e.g.:
"Editorial research brief for founders; quiet-luxury paper aesthetic,
serif-display + sans-body, low-chrome with a single teal accent."

## Output 3 — taste dials (1-10, each with one-line evidence from the sample)

- **DESIGN_VARIANCE** — how many distinct visual voices coexist (font count,
  color spread, radius spread).
- **MOTION_INTENSITY** — transition/animation coverage vs. element count,
  keyframe count.
- **VISUAL_DENSITY** — element count, container max-width, spacing values.

## Output 4 — audit notes (optional, when asked to audit)

Scan → diagnose → fix, three to five bullets max. Diagnose with the dials as
evidence ("MOTION_INTENSITY 8/10 but zero keyframes = transition spam"); every
fix maps to a token or a concrete CSS change.

## Guardrails

- Sample only pages you were pointed at. Don't sample authenticated or
  private pages without explicit permission.
- Never execute page interactions beyond loading — no clicks, no form fills.
- The sample is evidence, not truth: rendered values can come from
  runtime-injected styles that differ from the source CSS.
- Keep the source URL and date in the tokens.css header — extracted tokens
  are reference material, and unattributed clones are plagiarism.
