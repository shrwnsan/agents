# Provenance

- Schema findings (events vs events_v2, events_v2 columns, empty-legacy-table
  signature) verified against a live Plausible CE v3-era stack
  (ClickHouse 24.12.6); all example queries executed for real.
- Stats API pairing rules (metric/dimension combinations, pagination object,
  filter wildcards, date-range tokens) cross-checked against the community
  skill alexanderop/claude-plausible-analytics; that repo is unlicensed, so
  no text was copied — the rules were treated as API-behavior claims and
  re-expressed in our own words.
- Platform referrer-behavior notes are operational observations from real
  traffic, not vendor documentation; treat the Instagram and Threads rows as
  empirically stable, not contractual.
- Egress disclosure: connects only to the configured ClickHouse HTTP endpoint
  (or, if a human runs the Stats API fallback, the Plausible app host).
  Read-only: the bundled script refuses any non-SELECT statement. Credential
  sources are user-named env vars (PLAUSIBLE_CH_USER / PLAUSIBLE_CH_PASSWORD)
  resolved at runtime; values are never printed, logged, or transmitted
  anywhere except the configured ClickHouse host itself.
