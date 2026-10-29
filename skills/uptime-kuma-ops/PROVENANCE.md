# Provenance

- Socket.io client interaction pattern adapted from nocoo/uptime-kuma-skill
  (Apache-2.0); all 2.5.3 field-contract findings independently source-verified
  against louislam/uptime-kuma `server/server.js` @ tag 2.5.3.
- Operational validation: live Kuma 2.5.3-slim instance — three push monitors
  created, tokens minted client-side, heartbeats accepted.
- Egress disclosure: connects only to the configured Kuma base_url (reads
  `/metrics`, speaks socket.io); sends push heartbeats to the same host.
  Credential sources are user-named env files read at runtime; values are
  never printed, logged, or transmitted anywhere except the Kuma host itself.
