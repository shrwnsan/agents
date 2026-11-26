#!/usr/bin/env node
// migrate-batch.mjs—fork a batch of upstream repos onto a target GitHub
// account with per-call identity verification, throttling, and state
// writing. Node 18+, no dependencies.
//
// Usage:
//   node migrate-batch.mjs --parent owner/repo [--parent owner/repo ...]
//                          [--config <path>] [--state <path>]
//                          [--allow-proxy]
//
// Refuses to run behind a credential-injecting proxy unless --allow-proxy
// is passed (see references/PLATFORMS.md, rule 1 in SKILL.md).

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { homedir } from 'os';
import { join, dirname } from 'path';

function fail(msg) { console.error('FAIL: ' + msg); process.exit(1); }

let varCfg, varState;

// ---- path resolution by ROLE (per references/PLATFORMS.md) -------------
const isWin = process.platform === 'win32';
function configPath() {
  if (process.env.GIT_FORK_MIGRATION_CONFIG) return process.env.GIT_FORK_MIGRATION_CONFIG;
  if (isWin) return join(process.env.APPDATA || join(homedir(), 'AppData', 'Roaming'), 'github-repo-migration', 'config.yaml');
  return join(process.env.XDG_CONFIG_HOME || join(homedir(), '.config'), 'github-repo-migration', 'config.yaml');
}
function statePath() {
  if (process.env.GIT_FORK_MIGRATION_STATE) return process.env.GIT_FORK_MIGRATION_STATE;
  if (isWin) return join(process.env.LOCALAPPDATA || join(homedir(), 'AppData', 'Local'), 'github-repo-migration', 'state', 'progress.json');
  return join(process.env.XDG_STATE_HOME || join(homedir(), '.local', 'state'), 'github-repo-migration', 'progress.json');
}

// ---- minimal YAML subset reader (flat key: value + one nesting level) --
function readConfig(path) {
  if (!existsSync(path)) return {};
  const cfg = {};
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const m = line.match(/^([A-Za-z_][\w-]*):\s*(.*?)\s*$/);
    if (m && !line.startsWith(' ')) cfg[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  return cfg;
}

// ---- args ---------------------------------------------------------------
const args = process.argv.slice(2);
const allowProxy = args.includes('--allow-proxy');
const parents = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--parent') parents.push(args[++i]);
  else if (args[i] === '--config') varCfg = args[++i];
  else if (args[i] === '--state') varState = args[++i];
}
if (!parents.length) fail('no --parent owner/repo entries given');

// ---- proxy gate ---------------------------------------------------------
// Modern Node (>=24) honors HTTPS_PROXY for global fetch via EnvHttpProxyAgent;
// a credential-injecting gateway then overrides our Authorization header and
// every call lands on the WRONG account (SKILL.md rule 1). Default: strip the
// proxy env in-process so calls go direct. --allow-proxy keeps the proxy.
const proxySet = !!(process.env.HTTPS_PROXY || process.env.https_proxy || process.env.HTTP_PROXY || process.env.http_proxy);
if (proxySet && !allowProxy) {
  // GOTCHA (verified 2026-11-15, Node >=24): deleting env vars here is NOT
  // enough—undici's EnvHttpProxyAgent is configured from the environment at
  // process startup, before this code runs, so fetch keeps routing through
  // the proxy and the gateway still overrides Authorization (the 2026-11-13
  // misfire). The only reliable fix is to start node with the vars already
  // unset (e.g. `env -u HTTPS_PROXY node migrate-batch.mjs ...`). We still
  // strip them for child processes, and the /user identity gate below is
  // the real enforcement point.
  for (const k of ['HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy']) delete process.env[k];
  console.error('note: proxy env vars stripped in-process—NOTE: Node >=24 may still route via EnvHttpProxyAgent; prefer launching with `env -u HTTPS_PROXY …` (verified gotcha)');
}

const cfg = readConfig(typeof varCfg !== 'undefined' ? varCfg : configPath());
const target = process.env.GFM_TARGET || cfg.target_account;
const token = process.env.GFM_TOKEN; // by reference: set from the configured secret source
const throttleMs = Number(cfg.throttle_seconds || 1) * 1000;
const stateFile = typeof varState !== 'undefined' ? varState : statePath();
if (!target) fail('target account unset: config.yaml target_account or GFM_TARGET');
if (!token) fail('no PAT: set GFM_TOKEN from the configured secret source (never inline it here)');

// fetch uses the proxy env state fixed above: stripped (direct) by default.

const api = 'https://api.github.com';
const headers = {
  Authorization: `Bearer ${token}`,
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
  'User-Agent': 'github-repo-migration',
};
const gh = (path, opts = {}) => fetch(api + path, { ...opts, headers: { ...headers, ...(opts.headers || {}) } });
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// identity gate: confirm we are the target account before any fork call
const me = await gh('/user');
const meLogin = (await me.json()).login;
if (meLogin !== target) fail(`token authenticates as "${meLogin}", expected "${target}"—refusing to fork (SKILL.md rule 2)`);

// preflight mode: verify the plan without forking. For each parent, resolve the
// upstream repo, the would-be destination, and any existing fork collision.
const preflight = process.argv.includes('--preflight');
if (preflight) {
  console.log(`preflight: authenticated as "${meLogin}" (target "${target}")—identity OK`);
  const plan = [];
  for (const p of parents) {
    await sleep(throttleMs);
    const upstream = await (await gh(`/repos/${p}`)).json().catch(() => ({}));
    if (!upstream.full_name) { plan.push({ parent: p, ok: false, reason: 'upstream not found/private' }); continue; }
    const existing = await (await gh(`/repos/${target}/${upstream.name}`)).json().catch(() => ({}));
    plan.push({
      parent: p,
      ok: true,
      upstream_default_branch: upstream.default_branch,
      destination: `${target}/${upstream.name}`,
      collision: existing.full_name ? `fork already exists at ${existing.full_name} (parent: ${existing.parent ? existing.parent.full_name : '?'})` : null,
    });
  }
  for (const r of plan) {
    if (!r.ok) { console.log(`ERR ${r.parent}—${r.reason}`); continue; }
    console.log(`OK  ${r.parent} -> ${r.destination} (default: ${r.upstream_default_branch})${r.collision ? ' | ' + r.collision : ''}`);
  }
  const bad = plan.filter(r => !r.ok).length;
  console.log(`preflight ${plan.length - bad}/${plan.length} resolvable; no forks created`);
  if (bad) process.exit(1);
  process.exit(0);
}

// load state
let state = { batches: [] };
if (existsSync(stateFile)) { try { state = JSON.parse(readFileSync(stateFile, 'utf8')); } catch {} }

const results = [];
for (const p of parents) {
  const [owner, repo] = p.split('/');
  if (!owner || !repo) { results.push({ parent: p, ok: false, reason: 'bad parent format' }); continue; }
  await sleep(throttleMs);
  const res = await gh(`/repos/${owner}/${repo}/forks`, { method: 'POST', body: JSON.stringify({ name: repo }) });
  const body = await res.json().catch(() => ({}));
  const fullName = body.full_name || '';
  // rule 2: identity, not status
  if (res.status === 202 || (res.status >= 200 && res.status < 300)) {
    if (!fullName.startsWith(`${target}/`)) {
      results.push({ parent: p, ok: false, reason: `landed as "${fullName || '(no body)'}", not ${target}/—wrong account`, status: res.status });
      continue;
    }
    results.push({ parent: p, ok: true, fork: fullName, status: res.status });
  } else {
    results.push({ parent: p, ok: false, reason: `HTTP ${res.status} ${body.message || ''}`.trim(), status: res.status });
  }
}

state.batches.push({ at: new Date().toISOString(), results });
mkdirSync(dirname(stateFile), { recursive: true });
writeFileSync(stateFile, JSON.stringify(state, null, 2));

const ok = results.filter(r => r.ok).length;
for (const r of results) console.log(`${r.ok ? 'OK  ' : 'ERR '} ${r.parent}${r.ok ? ' -> ' + r.fork : '—' + r.reason}`);
console.log(`${ok}/${results.length} verified on ${target}; state written to ${stateFile}`);
if (ok !== results.length) process.exit(1);
