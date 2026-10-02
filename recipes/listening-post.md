---
id: listening-post
name: Listening Post — tailnet capture of a community you belong to
version: 0.1.0
description: Bounded, polite DOM capture of a logged-in web community through the operator's own browser - ephemeral tailnet membership, socat bridge to the browser's debug port, scroll-until-stagnant sweep, sanitize-at-ingest discipline, and a keyword-signature classifier with a committed calibration check. No API keys.
category: sense
requires: [socat, chromium-or-brave-with-debug-port, node-18+, tailscale-cli-1.102.x (fallback path only)]
secrets: []
health_checks:
  - "curl -sf http://<mac-tailnet-ip>:9222/json/version >/dev/null && echo 'CDP: OK' || echo 'CDP: FAIL'"
  - "ss -ltn | grep -q ':9222' && echo 'bridge: OK' || echo 'bridge: FAIL'"
setup_time: 20 min first run, ~2 min per session after
cost_estimate: "$0 - own hardware, existing tailnet, no API calls"
---

# Listening Post: Community Capture That Stays Polite and Private

Listen to a community you are a member of - support channels, forums, portals -
and turn raw scrollback into aggregate signal: recurring themes, unanswered
asks, who actually answers. The operator's own logged-in browser is the only
fetcher; the agent side connects over a tailnet and never holds a credential.

Worked example: a vendor's hosted community chat, captured in three bounded
sessions. Reference results (aggregate only): 17,451 repeat-aware messages
across 5 channels; the team answers 95%/78% of question-shaped asks
in-channel within 24h (median 112/301 min); theme shares hold stable across a
doubled corpus, which is what a depth pass should show.

## Legal and etiquette - read this first

- **Platform terms are the real exposure.** Most platforms prohibit automating
  user accounts, and the major hosted chat platforms say so explicitly
  (self-bot/user-bot clauses). Driving your own logged-in session via CDP
  falls under that even when you only read channels you can already see.
  Enforcement is account-level (suspension). You assume that risk on your own
  account.
- **Prefer the compliant path when it exists.** Official API or a bot invite
  with proper intents beats this recipe every time. Listening Post is the
  fallback for member communities with no API path - at friendly rates, for
  operational use, not bulk harvesting.
- **The data is third-party personal data.** Minimize fields (text, timestamp,
  role flag - not avatars or ids beyond need). Raw captures stay local-only
  and are never republished; committed outputs are aggregates only;
  paraphrase, don't quote. GDPR-style rules can reach hobby-scale collection -
  know your jurisdiction. Deletion requests get honored where feasible.
- **Politeness is engineering, not vibes.** Sessions bounded under an hour;
  scroll until the target stops serving history; back off on rate limits;
  off-peak windows; one community, not a fleet.
- Apache 2.0 covers this document, not your compliance. You are responsible
  for the target's terms and your local law.

## IMPORTANT: Instructions for the Agent

**You are the installer/operator.** Execute on behalf of the user. Every
snippet below runs as-is; placeholders are `<angle-bracketed>`. The default
transport holds no credential - if a step offers an auth-key path, that is the
fallback, not the default.

## Architecture

```
[agent container] --tailnet--> [socat on operator's Mac] --> [browser :9222]
     node driver                    TCP bridge, bound         debug port,
     sweep + classify               to the tailnet IP         throwaway
                                                              profile
```

- The browser runs on the operator's machine, logged into the target as the
  operator, with a **dedicated throwaway profile** - nothing else ever logs
  into that profile.
- socat exposes the browser's local-only debug port on the tailnet interface
  only - never on a public interface, never through a tunnel service.
- The agent container needs no Tailscale state of its own when the operator's
  machine is already a tailnet device: the container rides the host's egress,
  so the tailnet route is inherited and **no auth key is consumed anywhere**.
  (The keyed fallback - ephemeral device membership for the agent itself - is
  at the end.)

## Step 1 - Browser with debug port

```bash
open -na "Brave Browser" --args \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/listening-post-profile"
```

Log into the target in this profile once. Chrome/Chromium works identically.
The DevTools socket binds to 127.0.0.1, which is why the bridge exists.

## Step 2 - Tailnet-bound bridge

```bash
socat TCP-LISTEN:9222,bind=$(tailscale ip -4),fork TCP:127.0.0.1:9222
```

Bind to the tailnet IP, not 0.0.0.0. Teardown is `pkill -x socat` plus
quitting the browser - do both at the end of every session.

## Step 3 - Verify, bypassing any egress proxy

```js
import { get as httpGet } from "node:http"; // NOT fetch - see below
httpGet("http://<mac-tailnet-ip>:9222/json/version", (r) => {
  let b = ""; r.on("data", (c) => (b += c));
  r.on("end", () => console.log(r.statusCode, b.slice(0, 80)));
});
```

**Hard-won:** container runtimes often preload undici's `EnvHttpProxyAgent`,
which silently routes fetch() through an egress proxy - and the proxy mangles
tailnet-bound traffic. Use `node:http` for anything that must go direct.

## Step 4 - Driver: connect + eval with a hard timeout

```js
import { createRequire } from "node:module";
import { get as httpGet } from "node:http";
const require = createRequire(import.meta.url);
const WebSocket = require("ws");
const CDP_HTTP = process.env.CDP_HTTP || "http://<mac-tailnet-ip>:9222";

function httpJson(path) {
  return new Promise((res, rej) => {
    httpGet(`${CDP_HTTP}${path}`, (r) => {
      let b = ""; r.on("data", (c) => (b += c));
      r.on("end", () => { try { res(JSON.parse(b)); } catch (e) { rej(e); } });
    }).on("error", rej);
  });
}

export async function findTab(match = process.env.TARGET_MATCH || "<target-domain>") {
  const list = await httpJson("/json/list");
  const tab = list.find((t) => t.type === "page" && t.url.includes(match));
  if (!tab) throw new Error(`no tab matching ${match}`);
  return tab;
}

export function connect(wsUrl) {
  const ws = new WebSocket(wsUrl, { maxPayload: 256 * 1024 * 1024 });
  let id = 0;
  const pending = new Map();
  const opened = new Promise((res, rej) => { ws.once("open", res); ws.once("error", rej); });
  ws.on("message", (d) => {
    const m = JSON.parse(d.toString());
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  const send = async (method, params = {}) => {
    await opened;
    const mid = ++id;
    return new Promise((res, rej) => {
      pending.set(mid, (m) => (m.error ? rej(new Error(`${method}: ${m.error.message}`)) : res(m.result)));
      ws.send(JSON.stringify({ id: mid, method, params }));
    });
  };
  return { ws, send, close: () => ws.close() };
}

export async function evalJS(cdp, expression) {
  // A wedged DevTools socket hangs silently otherwise. 30s is generous for a
  // page eval; a timeout means the session is dead - fail loudly.
  const r = await Promise.race([
    cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true, userGesture: true }),
    new Promise((_, rej) => setTimeout(() => rej(new Error("page eval timed out after 30s")), 30_000)),
  ]);
  if (r.exceptionDetails) throw new Error("page eval failed: " + JSON.stringify(r.exceptionDetails).slice(0, 300));
  return r.result.value;
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
```

## Step 5 - The bounded sweep

Three rules keep a sweep polite and honest: **scroll-until-stagnant** (the
target's DOM is virtualized - it only renders what you scroll to), **round
caps** (a hard ceiling per channel even if history keeps flowing), and
**retry-on-rate-limit** (when the target shows an error bar, click its retry
instead of pushing harder).

The collect pass reads rendered rows and derives timestamps from snowflake
ids. The selectors below are the worked example's - swap in your target's.
Hardening worth copying whatever your target is:

- usernames render only on group headers - carry the last author forward in
  DOM order;
- the username span carries clan/server-tag suffixes - strip them;
- **role identity rides the role icon's alt text**, not name colors (computed
  colors were identical corpus-wide in the worked example);
- strip the "(edited)" tail the platform appends.

```js
const COLLECT = `(() => {
  let last = null;
  return [...document.querySelectorAll('[id^="chat-messages-"]')].map(el => {
    const parts = el.id.split("-");
    const id = parts[parts.length - 1];
    const content = el.querySelector('div[id^="message-content-"]');
    const head = el.querySelector('[id^="message-username-"]');
    if (head) {
      const tags = [...head.querySelectorAll('img[alt], [class*="roleIcon"]')]
        .map(i => i.getAttribute("alt") || i.getAttribute("aria-label") || "").filter(Boolean);
      last = {
        name: head.textContent.replace(/,?\\s*Server Tag:[\\s\\S]*$/, "").split(/\\s*\\[/)[0].trim(),
        tags: tags.join(","),
      };
    }
    return {
      id,
      ts: String((BigInt(id) >> 22n) + 1420070400000n),
      author: last ? last.name : null,
      authorTags: last ? last.tags : null,
      text: content ? content.innerText.replace(/\\s*\\(edited\\)[\\s\\S]*$/, "").trim() : "",
    };
  });
})()`;

// per channel: click sidebar link, wait for rows, then
for (let round = 0; round < MAX_ROUNDS && stagnant < 4; round++) {
  try {
    const batch = await evalJS(cdp, COLLECT);
    let fresh = 0;
    for (const m of batch) if (!seen.has(m.id)) { seen.set(m.id, m); fresh++; }
    stagnant = fresh === 0 ? stagnant + 1 : 0;
    if (await evalJS(cdp, `!!document.querySelector('[class*="channelBeginning"]')`)) break;
    if ([...seen.values()].some((m) => Number(m.ts) < CUTOFF_TS)) break;
  } catch (e) { console.error(`round ${round} failed - keeping what it has`); break; }
  if (stagnant > 0) {
    // try the target's own retry button first, then nudge with wheel events
    await cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x: vp.x, y: vp.y, deltaX: 0, deltaY: -5000 });
    await sleep(1500);
  } else {
    await evalJS(cdp, `(() => { let n = document.querySelector('[data-list-id="chat-messages"]');
      while (n && n.scrollHeight <= n.clientHeight) n = n.parentElement;
      if (n) { n.scrollTop = 0; n.dispatchEvent(new WheelEvent("wheel", { deltaY: -6000, bubbles: true })); } })()`);
    await sleep(1200);
  }
}
```

Worked-example sizing: a busy 20K-message channel tops out a 300-round cap in
~16 min; a full-history channel (6 months) completes in ~11 min. Recent busy
days can run ~1,700 messages/day - split deep scrollback across sessions
rather than raising the caps.

## Step 6 - Sanitize at ingest

- `captures/` is **gitignored, local-only, forever**. Third-party usernames
  and messages never enter git.
- Dedupe before counting: key = author (when present) + whitespace-normalized
  lowercased text; collapse repeats of the same key within 10 minutes (edit
  re-renders and rapid re-posts). State the rule in the committed code.
- Everything committed downstream is role-attributed aggregates - counts,
  shares, medians - never names, never verbatim quotes.

## Step 7 - Classifier with a committed calibration check

Keyword-signature themes (case-insensitive regex lists, a message can hit
several) are enough for theme sizing. The discipline that matters:

```js
// node classify.mjs --check prints got/target per channel against the
// baseline captured when the signatures were last calibrated. If a later
// pass silently drifts, --check says so - calibration cannot rot quietly.
if (process.argv.includes("--check")) { /* print got/target table */ }
```

Commit the baseline table with the classifier. When a rule legitimately
changes (a signature re-derived, an ambiguous token dropped), say so in the
file and re-baseline - never compare a new pass against numbers produced by a
different rule.

## Step 8 - Teardown and data lifecycle

1. `pkill -x socat` on the operator machine; quit the throwaway browser.
2. If the fallback keyed path was used: the single-use key died at join; the
   ephemeral device disappears when the agent container restarts. Confirm in
   the tailnet admin console and revoke anything minted and unused.
3. Raw captures: keep locally for analysis, delete on a schedule you can
   defend (the worked example keeps one pass of snapshots, then prunes).

## Fallback: keyed ephemeral membership

Only if direct TCP ever stops working (it removes all keys from the
equation, so treat this as plan B): run `tailscaled` in userspace mode in the
agent container from pinned static binaries, mint a **single-use, ephemeral,
short-expiry** auth key in the admin console, join with
`tailscale --socket=... up --authkey=...`, and tear the device down after.
Note `--ephemeral` is a property of the key, not a flag on `up` in recent
versions. Buggy egress gateways that reject the Tailscale controlplane TLS
make this path unavailable in some containers - which is why the default
path above holds no membership at all.

## Scaling to other targets

A new target is mostly a new collect selector plus a targets file (names +
ids). The transport, sweep discipline, dedupe, and calibration pattern are
target-independent. Before trusting a zero in your counts, probe the live
DOM once - in the worked example, thread affordances simply do not render
in-message, and a missing element looks exactly like an unused feature.

## What this is not

No bot invites. No account sharing. No fleet of targets. No republishing of
raw captures. One polite listener on a community the operator belongs to,
feeding aggregate insight - support themes, answer latency, gap shortlists -
that the raw scrollback cannot show.
