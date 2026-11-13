# Provenance

- Authored natively for this repo (2026-10-31). No text copied from other
  skills or vendors.
- Flag surface verified against the installed GitHub Copilot CLI 1.0.105
  (npm `@github/copilot`, 2026-10-31) by reading `copilot --help` directly;
  see [references/flags.md](references/flags.md). The community
  copilot-cli delegation skill on skills.sh
  (giuseppe-trisciuoglio/developer-kit) was reviewed first and motivated this
  one, but it documents flags that do not exist in 1.0.105
  (`--allow-tool`, `--allow-all-urls`, `--yolo`); nothing was copied from it.
- Premium-request billing model per GitHub's Copilot SDK/CLI documentation
  (GA 2026-06): CLI usage consumes the signed-in plan's premium-request
  quota. The ledger counts calls, not metered units—GitHub does not expose
  per-call unit counts to the CLI.
- Egress disclosure: the prompt text and any files the delegate reads go to
  GitHub via the pinned copilot binary; the wrapper itself makes no network
  calls, writes nothing outside the ledger path
  (`$COPILOT_DELEGATE_LEDGER`, default `~/.config/copilot-delegate/ledger.jsonl`),
  and passes `--disable-client-telemetry` by default. Credentials are never
  read, printed, or stored by the wrapper—the CLI owns its own auth state.
- The JSON output contract is a prompt-side convention, not a CLI feature;
  `--output-format json` exists (JSONL events) and is documented as an
  alternative in flags.md.
- Install channels verified 2026-11-03 against docs.github.com: npm
  (Node 22+; with `ignore-scripts=true` the documented form is
  `npm_config_ignore_scripts=false npm install -g @github/copilot@<pin>`),
  Homebrew cask `copilot-cli`, the gh.io install script, and release
  downloads. The bare `copilot` Homebrew formula is Amazon's AWS Copilot
  CLI, not this tool. The published packages carry no install scripts;
  the docs' ignore-scripts note is followed as the official line rather
  than second-guessed from package internals.
- 2026-11-13 revision 1.1.0 after the first live cross-check run (a Buzz
  harness-support lookup that ended in exit 3). The run confirmed the
  refusal path works and exposed blind spots. Changes: failed replies are
  now saved under the ledger directory's `failed/` folder; ledger rows carry
  a per-attempt `outcome`; the parse retry quotes the failed reply with flag
  names redacted; `--context-file` passes structured context; the preflight
  auth probe caches for one hour (`--fresh` forces a re-probe); and
  `check --expect-version` asserts the pin against a version found anywhere
  in the version output. No new Copilot CLI flags are constructed; the flag
  surface in references/flags.md is unchanged. Behavior verified with a stub
  binary (success path, double contract failure, cached probe, version
  mismatch, context passthrough) with no quota spent.
- 2026-11-13 revision 1.1.1: relocated runtime files to the XDG base
  directories. The ledger and failed-reply dumps now default to
  `${XDG_STATE_HOME:-~/.local/state}/copilot-delegate/` and the auth-probe
  timestamp to `${XDG_CACHE_HOME:-~/.cache}/copilot-delegate/`; the old
  `~/.config/copilot-delegate/` location is migrated in place on first use
  (`COPILOT_DELEGATE_STATE_DIR` and `COPILOT_DELEGATE_LEGACY_DIR` override
  for tests and exotic setups). Rationale: the agentskills.io specification
  (checked 2026-11-13, specification.md plus the scripts and best-practices
  guides) is silent on where skills write runtime state, so the platform
  convention applies, and XDG puts state and caches outside ~/.config.
  Verified with a stub binary against XDG test roots, including a
  legacy-directory migration run.
