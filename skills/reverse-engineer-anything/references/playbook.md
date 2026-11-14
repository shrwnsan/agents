# Playbook: recurring teardown targets

Worked applications of the SKILL.md method to the passes we run most. Each entry maps the generic phases onto the target class and names the artifacts that usually decide the case. Load only the entry you need.

## Company due-diligence page

Question shape: "what does this company's product actually do, and is the pitch real?"

- **Surface:** marketing claims (hypotheses), shipped app or extension, public API and docs, changelog cadence, job postings (they admit the roadmap), status page history, protocol captures of the free tier.
- **Deciding artifacts:** the shipped artifact almost always disagrees with the landing page in at least one checkable way (what ships client-side vs server-side, which model powers a feature, where data is stored). Feature-flag endpoints and config payloads fetched by the shipped client are the richest single capture.
- **Teardown doc layer discipline matters most here:** investors repeat "claimed" as if it were "observed". Keep the ledger rows honest; the coverage statement is what makes the page defensible when challenged.

## Agent harness or desktop app

Question shape: "what does this app do that it does not say?"

- **Surface:** follow `auditing-agent-harnesses` Phases 0-3 for the privacy pass. This skill adds the mechanism layer: how a headline feature actually executes (local model call, remote API, sidecar process, MCP relay).
- **Deciding artifacts:** the sidecar or main-process bundle; IPC channel names; the update channel manifest (C4); outbound socket captures during a representative feature run.
- **Split of work:** the harness skill issues the privacy verdict; this skill writes the mechanism section and the teardown doc. Run both in one capture session so the baseline is shared.

## Capture-to-vault flow (replay a product's own data)

Question shape: "can we reconstruct and replay what this pipeline captured, and is anything lost?"

- **Surface:** capture format on disk, writer code paths, redaction applied at write time, retention and deletion paths, the reader/import path of the vault side.
- **Deciding artifacts:** a raw capture file from each format version the target shipped; the schema or deserializer; a round-trip (capture → vault → replay) diff. Field-level diff of the round trip is the whole verdict: what survives, what is dropped, what is mutated.
- **Pitfall:** formats drift silently. Pin each capture to the writer version and re-round-trip after every target update.

## Console or protocol recon

Question shape: "what does this client and server actually exchange?"

- **Surface:** the client's endpoint list (static strings), one live session's full-payload capture, auth handshake shape, error responses under malformed input.
- **Deciding artifacts:** the full-payload capture of a representative session; a second capture after one deliberate input change to split request-shaped fields from session-shaped fields.
- **Pitfall:** one session is not a protocol. Capture at least two sessions that differ in one dimension before claiming a field is constant. Redact tokens at capture time; store the redaction rule in the evidence ledger, not just memory.

## Cross-cutting rules

- Every entry above ends in the same teardown doc structure from SKILL.md. Vary the surface list, not the output format, so docs stay comparable across targets.
- Timebox: if the scoping sentence cannot name a reachable artifact type within one working session of probing, record the target as "surface out of reach" with what was tried, and stop. Absence of a documented dead end is how teardowns get half-finished.
- Legal bounds: reverse engineering for understanding, interoperability documentation, and security review only. Never bypass auth, DRM, or rate-limit controls; never redistribute captured proprietary payloads.
