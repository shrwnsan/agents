# Provenance — dataviz

Ported from the copy bundled inside the Claude Code CLI. There is no git
upstream: Anthropic ships this skill only inside the binary.

- **Source:** Claude Code CLI **2.1.267**, bundled skill `dataviz`
- **Copyright:** © Anthropic PBC. All rights reserved. This content is Anthropic
  proprietary and is **not** covered by this repository's Apache-2.0 license; it
  is vendored verbatim here for personal use.
- **Fidelity:** `references/` and `scripts/` are byte-identical to the CLI's
  runtime extraction (unchanged since CLI 2.1.226; re-verified byte-for-byte
  against an independent carve from the 2.1.267 binary, 2026-09-10). The
  SKILL.md body is verbatim from the runtime skill loader (same cross-check).
  The frontmatter (`name` + `description`) is reconstructed from the CLI's
  skill-registration metadata; `description` is the 2.1.267 text (the 2.1.260
  wording was replaced upstream).
- **Pin:** CLI 2.1.267, per the vendor-and-pin policy in the README. Refreshing
  to a newer CLI version re-triggers the full vetting pass.

## Refreshing (manual — no sync-upstream entry)

1. On the target CLI version, invoke `/dataviz` once. `references/` +
   `scripts/` extract to
   `/tmp/claude-<uid>/bundled-skills/<cli-version>/<hash>/dataviz/` (uid-keyed
   path; `<hash>` is content-addressed and churns per version).
2. Diff that directory against `skills/dataviz/` and copy over changes.
3. The SKILL.md body is never written to disk — capture it by invoking the
   skill (the loader emits the body with frontmatter stripped), then re-attach
   the frontmatter from this repo's SKILL.md if the upstream text is unchanged.
4. Verify the frontmatter against the binary's registration block when in
   doubt: `strings <claude-binary> | grep -A2 'menuDescription:"Chart and'`.

## Install notes (Claude Code)

- Installing this skill to `~/.claude/skills/dataviz` (or a project
  `.claude/skills/`) **shadows the built-in `/dataviz`** — Claude Code gives
  your copy the name, and the bundled skill defines no aliases, so nothing is
  orphaned. The personal copy stays frozen at the pinned version while
  `claude update` keeps improving the built-in one; delete the directory to
  restore the built-in. (Flip side: under `disableBundledSkills: true`, a
  personal copy is the only way to keep `/dataviz`.)
- Description length: the 2.1.260 wording (~1.4k chars) exceeded the
  agentskills.io spec's hard 1024-char limit, so strictly spec-conforming
  clients (claude.ai upload, Skills API) returned HTTP 400 for it. The 2.1.267
  wording (~975 chars) is within the limit and loads untruncated everywhere.
