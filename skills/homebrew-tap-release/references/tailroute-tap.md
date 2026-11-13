# The tailroute tap: concrete instance

Applies the generic flow in `../SKILL.md` to the shrwnsan taps. Read this
only when working on those repos; the main skill stays generic on purpose.

## Streams and repos

| Stream | Tag grammar | Source repo | Homebrew surface |
|---|---|---|---|
| CLI package (bash CLI + daemon + `tailroute-proxy` Go binary) | `v*` | shrwnsan/tailroute-cli | formula `tailroute-cli` in shrwnsan/homebrew-tap |
| Menu-bar app (closed source, separate stream) | `app-v*` | separate app repo | cask `tailroute` in shrwnsan/homebrew-tap |

- On a bare `v*` tag push, the cli repo's `.github/workflows/release.yml`
  builds `tailroute-proxy-darwin-arm64` and `tailroute-proxy-darwin-amd64`
  plus a `.sha256` sidecar for each, and publishes all four on the GitHub
  release.
- The cask tracks the app stream. NEVER touch the cask's livecheck
  `app-v*` regex. A formula release never moves the cask. Diverging
  formula/cask numbers are the healthy state, not drift.

## What a formula bump touches

`Formula/tailroute-cli.rb` carries three `url` lines and three `sha256`
lines:

1. the source archive `.../archive/refs/tags/vX.Y.Z.tar.gz` and its sha,
2. the `resource "proxy"` arm64 url `.../releases/download/vX.Y.Z/tailroute-proxy-darwin-arm64` and its sha,
3. the `resource "proxy"` amd64 url `.../releases/download/vX.Y.Z/tailroute-proxy-darwin-amd64` and its sha.

A bump is one global replace of the old tag with the new tag across those
url lines, then the three shas recomputed. `ruby -c` afterwards, then a PR.

## Verified example: v0.9.0, 2026-10-27

1. Release commit `182995e` bumped the VERSION constant in
   `bin/tailroute.sh` and dated the changelog entry.
2. Tag `v0.9.0` pushed; CI published 4 assets (2 binaries + 2 sidecars)
   in about 4 minutes.
3. The formula needed three new checksums: the archive sha plus the arm64
   and amd64 asset shas.
4. `brew info shrwnsan/tap/tailroute-cli` showed `0.8.17 -> stable 0.9.0`.

Historical note for the golden rule: the v0.8.17 tag shipped while the
VERSION constant still read 0.8.16. Same-commit bumps exist because of it.

## User-upgrade caveat: stale root-owned keg

The formula's service runs as root, so Homebrew takes root:admin ownership
of the Cellar paths. A keg installed during a past launchd incident can
survive `brew cleanup`, leaving users on the old binary after an upgrade.
Fix on the affected machine: stop the service, `sudo rm -rf` the stale keg
under `$(brew --prefix)/Cellar/tailroute-cli`, then restart the service.

## Release-notes hygiene for this project

- The GitHub release body and the tap PR body are public. No private-repo
  references, no internal vocabulary, no umbrella-repo URLs or issue
  numbers.
- Redact peer and tailnet names in example output as `<peer>` and
  `<tailnet>`.
