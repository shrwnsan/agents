#!/usr/bin/env node
// Sample the rendered visual language of a page via agent-browser.
// Usage: node sample.mjs <url-or-file> [--out file.json] [--keep-open]
// Emits a JSON sample on stdout. Judgment (tokens.css, design read, dials,
// audit) is the calling agent's job — see SKILL.md.

import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
const target = args.find(a => !a.startsWith("--"));
const outFlag = args.indexOf("--out");
const outFile = outFlag > -1 ? args[outFlag + 1] : null;
const keepOpen = args.includes("--keep-open");

if (!target) {
  console.error("usage: node sample.mjs <url-or-file> [--out file.json] [--keep-open]");
  process.exit(2);
}

const SAMPLE_JS = String.raw`
(() => {
  const cs = el => getComputedStyle(el);
  const root = cs(document.documentElement);
  const pickCount = Math.min(document.querySelectorAll("*").length, 1500);
  const stride = Math.max(1, Math.floor(pickCount / 400));
  const els = [...document.querySelectorAll("*")].filter((_, i) => i % stride === 0);

  const customProps = {};
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch { continue; }
    for (const rule of rules) {
      if (!rule.style || !rule.selectorText) continue;
      const sel = rule.selectorText;
      if (sel === ":root" || sel === "html" || sel === "body" || sel.includes("[data-theme") || sel.includes(".dark")) {
        for (let i = 0; i < rule.style.length; i++) {
          const p = rule.style[i];
          if (p.startsWith("--")) customProps[sel + " " + p] = rule.style.getPropertyValue(p).trim();
        }
      }
    }
  }

  const bump = (map, v) => { if (v && v !== "0px" && v !== "none" && v !== "normal" && !v.includes("rgba(0, 0, 0, 0")) map.set(v, (map.get(v) || 0) + 1); };
  const colors = new Map(), spacing = new Map(), radii = new Map();
  for (const el of els) {
    const s = cs(el);
    bump(colors, s.color); bump(colors, s.backgroundColor); bump(colors, s.borderTopColor);
    bump(spacing, s.paddingTop); bump(spacing, s.paddingBottom); bump(spacing, s.marginBottom);
    bump(spacing, s.gap === "normal" ? null : s.columnGap); bump(spacing, s.rowGap);
    bump(radii, s.borderRadius);
  }
  const top = (m, n) => [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([value, hits]) => ({ value, hits }));

  const type = {};
  for (const sel of ["h1", "h2", "h3", "h4", "p", "a", "button"]) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const s = cs(el);
    type[sel] = { font: s.fontFamily.split(",")[0].replace(/["']/g, ""), size: s.fontSize, weight: s.fontWeight, lineHeight: s.lineHeight, letterSpacing: s.letterSpacing, color: s.color, transform: s.textTransform };
  }

  const fonts = [...new Set(els.slice(0, 300).map(e => cs(e).fontFamily.split(",")[0].replace(/["']/g, "")))];
  const googleFonts = [...new Set([...document.querySelectorAll('link[href*="fonts.googleapis"],style')].map(x => x.href || x.textContent || "").join(" ").match(/family=[A-Za-z0-9+:,;=\.\-@]+/g) || [])].map(f => f.replace("family=", ""));

  const keyframes = [];
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch { continue; }
    for (const r of rules) { if (r.type === CSSRule.KEYFRAMES_RULE) keyframes.push(r.name); }
  }
  let transitionEls = 0, animatedEls = 0;
  for (const el of els) {
    const s = cs(el);
    if (s.transitionDuration && s.transitionDuration !== "0s") transitionEls++;
    if (s.animationName && s.animationName !== "none") animatedEls++;
  }

  const container = document.querySelector(".container, main, article, body");
  const containerStyle = container ? cs(container) : null;

  return JSON.stringify({
    url: location.href,
    title: document.title,
    theme: {
      colorScheme: root.colorScheme,
      metaColorScheme: document.querySelector('meta[name="color-scheme"]')?.content || null,
      hasDataTheme: !!document.querySelector("[data-theme]"),
      prefersDark: matchMedia("(prefers-color-scheme: dark)").matches
    },
    fonts, googleFonts, type,
    colors: top(colors, 24),
    spacing: top(spacing, 16),
    radii: top(radii, 10),
    motion: { keyframes: [...new Set(keyframes)].slice(0, 20), transitionEls, animatedEls, sampled: els.length },
    customProps,
    container: containerStyle ? { maxWidth: containerStyle.maxWidth, font: containerStyle.fontFamily.split(",")[0].replace(/["']/g, "") } : null,
    counts: { elements: document.querySelectorAll("*").length, gridish: document.querySelectorAll('[class*="grid"],[class*="card"]').length }
  });
})()
`;

function run(cmd, cmdArgs) {
  return execFileSync(cmd, cmdArgs, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
}

try {
  const url = /^https?:\/\//.test(target) || target.startsWith("file://")
    ? target
    : pathToFileURL(resolve(target)).href;   // bare paths: agent-browser only navigates URLs
  run("agent-browser", ["open", url]);
  try { run("agent-browser", ["wait", "--load", "networkidle"]); } catch { /* best effort */ }
  const raw = run("agent-browser", ["eval", SAMPLE_JS]);
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start === -1 || end === -1) throw new Error("no JSON object in eval output:\n" + raw.slice(0, 400));
  const jsonText = raw.slice(start, end + 1);
  let parsed;
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    // agent-browser prints string results quoted+escaped ({\"k\":...}); unwrap once
    parsed = JSON.parse(JSON.parse('"' + jsonText + '"'));
  }
  const sample = JSON.stringify(parsed, null, 2);
  if (outFile) writeFileSync(outFile, sample + "\n");
  console.log(sample);
} finally {
  if (!keepOpen) { try { run("agent-browser", ["close"]); } catch { /* already closed */ } }
}
