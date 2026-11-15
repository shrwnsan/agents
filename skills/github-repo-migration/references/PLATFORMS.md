# Platforms: config/state locations, tools, proxy detection

Resolve directories by ROLE at run time. Do not hardcode paths from this
file into scripts when a runtime library can resolve them.

## Directory roles

| Role | Purpose | Linux/macOS (XDG) | Windows-native |
|------|---------|-------------------|----------------|
| Config | `config.yaml`—accounts, batch size, throttle, secret reference | `$XDG_CONFIG_HOME/github-repo-migration/` (fallback `~/.config/github-repo-migration/`) | `%APPDATA%\github-repo-migration\` |
| State | `progress.json`—batch results, counters | `$XDG_STATE_HOME/github-repo-migration/` (fallback `~/.local/state/github-repo-migration/`) | `%LOCALAPPDATA%\github-repo-migration\state\` |

macOS note: XDG paths are the convention here too; do NOT use
`~/Library/Application Support` for this skill—XDG keeps the three
platforms semantically aligned, and macOS agents honor the fallback chain.

WSL is a convenience, not a dependency: a Windows-native harness uses the
Windows column directly.

## Tool availability

| Tool | Linux | macOS | Windows-native |
|------|-------|-------|----------------|
| git | standard | standard | Git for Windows |
| curl | standard | standard | ships with Windows 10+ |
| jq | package manager | brew | scoop / winget |
| Node.js 18+ | standard | standard | standard installer |

The bundled script (`scripts/migrate-batch.mjs`) needs only Node 18+
(no npm dependencies). curl/jq are for manual, non-scripted runs.

## Secrets

- The PAT is referenced in `config.yaml` under `secret_source` (e.g. an
  env var name or a secrets-manager entry name). Never the value itself.
- Retrieve at run time per platform: env var, or the platform's secrets
  CLI. Common gotcha: secrets-manager values are sometimes stored wrapped
  (e.g. a JSON envelope)—unwrap per that store's documented format
  before assuming a 401 means the token is dead. Never print the value.
- Scopes needed: `repo` (fork + push). `delete_repo` is NOT required for
  migration and should only exist on a short-lived token minted for a
  specific cleanup, with the operator's approval.

## Credential-injecting proxies (the #1 failure mode)

Some agent environments route all HTTP through a gateway that injects
`Authorization` headers with its own credentials. Effects:

- An explicit `Authorization` header you set is OVERRIDDEN—calls
  authenticate as the gateway's account, not the header's.
- Node `fetch` honors proxy env vars on Node >= 24 (EnvHttpProxyAgent);
  older Node ignores them. curl always honors them unless `--noproxy` is
  given. GOTCHA (verified 2026-11-15): on Node >= 24, stripping the env
  vars in-process after startup does NOT disable the agent—it was already
  configured, so fetch still goes through the proxy. Only launching the
  process with the vars unset works (`env -u HTTPS_PROXY …`).
  given. Test, don't assume.
- GitHub's fork API is idempotent per account: if the gateway's account
  already has the fork, the misdirected call returns it silently. Status
  codes look fine; the result is wrong.

Detection: are `HTTPS_PROXY` / `HTTP_PROXY` set, and does a
`GET /user` with your explicit token return the WRONG account login?
If yes—all target-account calls must go direct (`--noproxy '*'`,
or fetch with a dispatcher that ignores the proxy) with the explicit
PAT header. The bundled script strips proxy env in-process unless
`--allow-proxy` is given (best-effort—see the Node >= 24 gotcha above),
then enforces the identity gate before any fork.

## Version drift

Re-check the parent repo's default branch at the start of each batch. A
"quiet mirror" classification is a snapshot; upstream may have moved since
it was taken.
