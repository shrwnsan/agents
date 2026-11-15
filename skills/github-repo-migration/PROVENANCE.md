# Provenance

- **Skill:** github-repo-migration v0.2.0 (renamed from `git-fork-migration` v0.1.0 — the mechanics cover any repo relocation, not just forks)
- **Origin:** native (authored in-house, shrwnsan)
- **First authored:** 2026-11-13 (fork-migration spike after the misdirected-API-call lesson)
- **Renamed + hardening pass:** 2026-11-15
- **Validated live:** tranche 3, 2026-11-15 — 5 quiet-mirror forks re-forked onto a target machine account, 5/5 identity-verified (`full_name` + `parent.full_name` per repo). The same run verified the Node ≥24 proxy gotcha documented in SKILL.md rule 1: the bundled script's identity gate refused a run where the runtime still routed through a credential-injecting proxy, before any fork call was made. That gate behavior is the tested enforcement point, not a design claim.
- **Secrets contract:** the PAT is never in this repo. Config/state files hold account names and counters only; tokens come from the configured secret source at run time (`GFM_TOKEN`).
- **Pins:** no external dependencies (Node ≥18 stdlib only); GitHub REST API version pinned `2022-11-28` in the script headers.
