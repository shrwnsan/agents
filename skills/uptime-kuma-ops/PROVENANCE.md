# Provenance

- 2026-10-28, authored by shrwnsan + Claude Code session on oci-prime.
- Socket.io client interaction pattern adapted from nocoo/uptime-kuma-skill
  (Apache-2.0); all 2.5.3 field-contract findings independently source-verified
  against louislam/uptime-kuma `server/server.js` @ tag 2.5.3 the same day.
- Operational validation: live oci-micro Kuma 2.5.3-slim instance — three push
  monitors created, tokens minted client-side, heartbeats accepted (2026-10-28).
- Egress disclosure: connects only to the configured Kuma base_url (reads
  `/metrics`, speaks socket.io); sends push heartbeats to the same host.
  Credential sources are user-named env files read at runtime; values are
  never printed, logged, or transmitted anywhere except the Kuma host itself.
