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
