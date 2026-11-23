# Provenance

- Original work, first version 2026-11-24. No upstream.
- All quirks verified live against api.agentmail.to during Oct–Nov 2026 inbox
  operations (thread/split behavior, 404 on the thread-level reply route,
  mint-time key scoping, no archive op). See SKILL.md.
- The probe-safety rules were added after a live mis-send on 2026-11-24: a
  probe of the reply endpoint delivered its literal probe text. The rule is
  learn shapes from existing objects, never from live side-effecting calls.
