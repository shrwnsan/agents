---
name: reverse-engineer-anything
license: Apache-2.0
description: Reverse engineer a product, app, agent harness, or workflow from shipped artifacts and observed behavior instead of source or vendor claims. Use when a teardown, due-diligence page, "how does X actually work" investigation, capture-to-replay reconstruction, or console/protocol recon is requested, or when a claim depends on evidence the vendor has not published. Inspired by the REA (Reverse Engineer Anything) ecosystem; this is an original method that needs no MCP server or special tooling.
metadata:
  version: "1.0.0"
---

# Reverse Engineer Anything

## Overview

Answer "how does this actually work, and what proves it" for a target you cannot read as source: a company's product, a desktop agent harness, a data pipeline, a capture format, a paid API. Every claim in the output must trace to an artifact you captured or an observation you ran. Vendor claims are hypotheses, not findings.

This skill encodes the same passes we already run ad hoc: company DD pages, agent-harness privacy audits, capture-to-vault flows, and console recon. It fixes the order and the exit criteria so the pass is repeatable and its coverage is checkable.

Relationship to other skills:
- `auditing-agent-harnesses` covers one target class in depth (privacy concern classes C1-C9 on agent desktop apps). Use it when the target is an agent harness; its verdict feeds this skill's teardown doc.
- `security-audit` hunts vulnerabilities in source you can read. This skill works without source.
- `live-system-forensics` audits a machine. This skill audits a product or mechanism.

## Scope the target first

Write one sentence before touching tools: "explain how [target] does [mechanism], evidenced by [artifact types]." A target without a named mechanism produces a tour, not a teardown. Bound it:

- **Mechanism, not the product.** "How does the editor's ghost-text caching work", not "everything about the editor".
- **Artifact types you can reach.** Shipped binaries, installers, network captures, console output, docs, changelogs. If none of these touch the mechanism, say so and stop before burning effort.
- **One deliverable.** The teardown doc (see Output). Everything else is a scratch artifact.

## Map the surface

Enumerate where the mechanism could live before choosing tools. In rough order of yield for a shipped product:

1. **Install artifacts**: the shipped bundle, package layout, sidecars, native modules, update manifests. File names, sizes, and hashes are evidence.
2. **Static strings and config**: identifiers, endpoint names, feature flags, protocol constants, telemetry SDK markers. `strings`, `grep`, and a package manifest get surprisingly far before decompilation.
3. **Declared behavior**: official docs, changelogs, release notes, public API references. Record each claim as a hypothesis to confirm or break, never as a finding.
4. **Runtime footprint**: processes spawned, sockets opened, files written, permissions requested. This is where static analysis lies get caught.
5. **Wire behavior**: captures of the protocol or API the mechanism uses. Capture before you theorize; a capture beats any guess about the format.

List the surface in the working notes with a one-line "checked, nothing relevant" for each dead end. Unchecked surface is the main source of wrong teardowns.

## Capture artifacts

Capture first, analyze second, and store everything before drawing conclusions, because the target moves under you (updates, A/B flags, region differences).

- Pin the exact build: version, download URL or capture date, `sha256` of every artifact you keep. A teardown that cannot name its build cannot be verified.
- Capture the runtime baseline before interacting: process list, open sockets, file writes. Interacting first pollutes the baseline.
- Capture network with full payloads, not just metadata, when the mechanism is protocol-shaped. Redact credentials at capture time, never by editing later from memory.
- Keep captures in a durable non-temp directory with one JSONL or manifest line per capture: what, when, build, source. A `/tmp` path must note its own volatility.
- Screenshot or export anything rendered (console, dashboard, UI state) the same session; renderers do not reproduce on demand.

If legal or terms-of-service bounds apply to the target, state them in the working notes before capture and stay inside them. Reverse engineering for understanding is the scope here; bypassing access controls is not.

## Trace data and control flow

Pick one observable input-output pair and follow it end to end: a button click to a socket write, a flag flip to a config file, a query to a response field. Work at the coarsest level that answers the scope question:

- **Crossing points** first: IPC boundaries, HTTP calls, file writes, subprocess spawns. Mechanisms almost always straddle one.
- **From both ends**: what the input looks like on the wire, and what code or config consumes it. Meet in the middle; do not linearly decompile.
- **Diff as a probe**: change one input, toggle one flag, use one older build. The delta names the responsible component more reliably than reading code.
- **Version compare** when a feature changed: the diff between two builds' artifacts is a map of the mechanism.

Stop expanding the trace the moment the scoped mechanism is explained. Adjacent interesting things go in a "found on the way" list, not the trace.

## Identify the mechanism

Convert the trace into a statement of mechanism: what component does what, in what order, over what data, and why it is built that way. Then falsify it once:

- Predict one behavior you have not observed yet and test the prediction. A mechanism claim that survives one deliberate falsification attempt is a finding; one that has never been tested is a hypothesis and gets labeled as such in the doc.
- Separate the layers: **observed** (capture or run backs it), **inferred** (artifact implies it), **claimed** (vendor said it). Each sentence in the teardown carries exactly one layer.
- Name the confidence and the falsifier for the top-level claim: "what evidence would break this".

## Produce the teardown doc

One document, structured so a reader can audit the coverage:

1. **Scope**—the scoping sentence, the build pin (version, dates, hashes).
2. **Mechanism**—the top-level answer in plain words, with confidence and falsifier.
3. **Evidence ledger**—every claim as a row: claim, layer (observed/inferred/claimed), backing artifact reference.
4. **Coverage statement**—which surface entries were checked and which were out of reach. "Checked with no finding" entries belong here; silence reads as skipped.
5. **Method**—the commands and captures, tight enough that a second person reproduces the pass.
6. **Found on the way**—unexplored leads, one line each.

Deliver the doc as a file, not a chat dump. Long doc plus a one-line summary beats a wall of chat text.

## Boundaries

- No source-level vulnerability hunting → `security-audit`.
- Agent-harness privacy verdicts → `auditing-agent-harnesses` (its verdict is an input here).
- Machine-level malware and persistence → `live-system-forensics`.
- Do not bypass authentication, DRM, or access controls. If the mechanism sits behind one, stop at the boundary and say so in the doc.
