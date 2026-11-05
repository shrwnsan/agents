# Provenance

- Vendored from upstream: [herdrdev/herdr](https://github.com/herdrdev/herdr),
  `skills/herdr/SKILL.md`, pinned @ `1cbd794559fb139f95f1bdb4b2a8998082017d0e`
  (2026-11-05). Upstream repo is Apache-2.0; this skill file carries no
  separate license header — the repo license governs.
- Source of truth for updates: the upstream file. Re-vendor by re-fetching
  at a newer pin and updating the pin recorded here. Also listed in
  [.upstream.yml](../../.upstream.yml) for the sync-upstream workflow.
- Motivation (2026-11-05): local-llm UAT sessions are driven across Herdr
  panes (Pi and Claude Code against the local LFM3 stack). Pane targeting
  and output capture were hand-rolled with cached pane IDs, which churn;
  the official skill teaches the correct pane/agent control patterns
  (`herdr agent prompt/wait/read`), including running commands without
  stealing focus.
- Guard behavior kept verbatim from upstream: the skill verifies
  `HERDR_ENV=1` and refuses to control Herdr from outside a Herdr pane,
  and its description gates activation on explicit Herdr mentions.
- Egress disclosure: the skill is instructions only; it invokes the local
  `herdr` binary, which talks to the local Herdr socket
  (`~/.config/herdr/herdr.sock`). No external network calls.
