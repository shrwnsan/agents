#!/usr/bin/env node
// vercel-domain-search — batch availability + pricing via Vercel's authless
// registrar API. Read-only: never calls buy/transfer/renew.
// Usage: node check-domains.mjs <names-file | name...> [--years 1] [--limit USD] [--json]

import { existsSync, readFileSync } from "node:fs";

const BASE = "https://api.vercel.com";
const AVAIL_CHUNK = 200; // search endpoint cap
const PRICE_CHUNK = 50; // price endpoint cap

const args = process.argv.slice(2);
const flags = { years: 1, limit: null, json: false };
const nameArgs = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--years") flags.years = Number(args[++i]) || 1;
  else if (args[i] === "--limit") flags.limit = Number(args[++i]) || null;
  else if (args[i] === "--json") flags.json = true;
  else nameArgs.push(args[i]);
}
if (!nameArgs.length) {
  console.error("usage: node check-domains.mjs <names-file | name...> [--years N] [--limit USD] [--json]");
  process.exit(1);
}

// Collect names: a single existing file arg = one-per-line list; rest are inline.
let raw = [];
if (nameArgs.length === 1 && existsSync(nameArgs[0])) {
  try {
    raw = readFileSync(nameArgs[0], "utf8").split("\n");
  } catch {
    console.error(`no such file: ${nameArgs[0]}`);
    process.exit(1);
  }
} else {
  raw = nameArgs;
}

// Normalize: lowercase, strip scheme/path, keep dotted names only, dedupe, cap 200.
const seen = new Set();
const names = [];
for (const line of raw) {
  const n = line.trim().toLowerCase().replace(/^[a-z]+:\/\//, "").replace(/\/.*$/, "").replace(/^www\./, "");
  if (!n) continue;
  if (!/^[a-z0-9-]+(\.[a-z0-9-]+)+$/.test(n)) {
    console.error(`skipping (not a domain): ${line.trim()}`);
    continue;
  }
  if (!seen.has(n)) {
    seen.add(n);
    names.push(n);
  }
}
if (!names.length) {
  console.error("no valid domain names to check");
  process.exit(1);
}
if (names.length > 200) names.length = 200;

async function post(path, body) {
  const r = await fetch(BASE + path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const t = (await r.text()).slice(0, 200);
    throw new Error(`${path} -> ${r.status}: ${t}`);
  }
  return r.json();
}

function chunks(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

// Availability pass via the search endpoint (keyless, 200/chunk).
const rows = [];
for (const chunk of chunks(names, AVAIL_CHUNK)) {
  const data = await post("/v1/registrar/domains/search", { domains: chunk });
  for (const r of data.results ?? []) rows.push({ domain: r.domain, available: !!r.available, price: null, renewal: null });
}

// Pricing pass: only the available subset (taken domains price as null anyway).
const free = rows.filter((r) => r.available).map((r) => r.domain);
for (const chunk of chunks(free, PRICE_CHUNK)) {
  const data = await post("/v1/registrar/domains/price", { domains: chunk, years: flags.years });
  for (const r of data.results ?? []) {
    const row = rows.find((x) => x.domain === r.domain);
    if (row) {
      row.price = r.purchasePrice;
      row.renewal = r.renewalPrice;
    }
  }
}

const priced = rows.filter((r) => r.available);
for (const r of priced) if (r.price == null) r.price = r.renewal;
priced.sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity));

if (flags.json) {
  console.log(JSON.stringify({ years: flags.years, limit: flags.limit, results: rows }, null, 2));
  process.exit(0);
}

const underCap = flags.limit ? priced.filter((r) => r.price != null && r.price <= flags.limit).length : priced.length;
console.log(
  `**${priced.length} of ${rows.length} available**` +
    (flags.limit ? `, ${underCap} at or under $${flags.limit}/yr (${flags.years}yr pricing)` : ` (${flags.years}yr pricing)`)
);
if (!priced.length) {
  console.log("\nNone available. Widen the candidate list or try other TLDs.");
  process.exit(0);
}
console.log("");
console.log("| Domain | Price ($/yr) | Renewal ($/yr) | Note |");
console.log("|--------|-------------|----------------|------|");
for (const r of priced) {
  const premium = flags.limit && r.price != null && r.price > flags.limit ? "premium" : "";
  console.log(`| ${r.domain} | ${r.price ?? "—"} | ${r.renewal ?? "—"} | ${premium} |`);
}
