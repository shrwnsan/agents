# Evaluations

Two machine-readable eval files pin this skill's behavior. They follow the
`evals.json` + `trigger-evals.json` pattern from
[avdlee/xcode-disk-cleanup-agent-skill](https://github.com/avdlee/xcode-disk-cleanup-agent-skill).

## Files

- **`trigger-evals.json`** — does the skill *fire*? Each case gives a user
  prompt and whether the skill should trigger. Catches trigger failures: the
  skill loading on unrelated requests ("clean the gutters") or failing to load
  on real cleanup requests ("my disk is almost full"). Frontmatter
  `name`/`description` drive triggering; changes there are what these catch.
- **`evals.json`** — given the skill loaded, does the agent *behave*? Each
  scenario gives a synthetic fixture, a prompt, steps, and objectively
  checkable assertions (`file-exists`, `file-not-exists`, `output-contains`,
  `output-not-contains`). Catches workflow violations: deleting before
  confirmation, `rm -rf` instead of trash, scanning outside the requested
  scope, flagging `.env*` secrets, missing regeneration notes, missing >1 GB
  warnings.

## Running them today (manual)

No automated runner exists yet — it is a tracked backlog item. Until it lands:

1. Start a fresh agent session with the skill available (fresh per case so a
   prior case's context cannot leak).
2. **Trigger cases**: paste the `prompt` verbatim. Record whether the skill
   activated (skill-listing/tool-use shows it loading). Pass if activation
   matches `expected`.
3. **Behavior scenarios**: build the fixture from `setup` (all under
   `$TMPDIR`; the >1 GB fixtures cost ~1.2 GB of real temp-disk and should be
   removed afterwards), paste the `prompt`, walk the `steps` as the runner
   (including the scripted confirmation replies), then check every entry in
   `assertions` and `must_not`. A scenario passes only when all of them hold.

## Re-run rule

Any change to `SKILL.md` (including frontmatter) or `reference/targets.json`
requires re-running both files before merge. Trigger wording and cleanup
behavior are load-bearing: the evals are the regression net for them.
