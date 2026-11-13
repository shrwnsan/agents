---
name: homebrew-tap-release
description: "Cut and publish a Homebrew tap release: bump a formula (or cask) to a newly tagged version, recompute all sha256 checksums from the actual release artifacts, push the tap update, and verify the install surface with brew info, livecheck, and audit. Use when tagging a release that ships to Homebrew, when a tap formula needs a version bump, when updating the tap after a release, when shipping a new version to brew, when checksums must be recomputed for new release assets, or when debugging why brew still offers an old version or why a formula and its cask show different version numbers. Covers the two-stream scheme where a formula (bare v* tags) and a cask (app-v* tags) version independently."
license: Apache-2.0
compatibility: "Requires git and the gh CLI; curl and shasum for checksums; brew for post-publish verification."
metadata:
  author: shrwnsan
  version: "1.0.0"
---

# Homebrew tap release

Cut a release that ships through a GitHub-hosted Homebrew tap. Tag the
release, let CI publish the assets, recompute every checksum from the actual
artifacts, bump the formula or cask, then prove that brew serves the new
version. The flow here is generic. For one concrete two-stream tap, read
`references/tailroute-tap.md`. For the whole flow as ordered tick-boxes,
read `references/checklist.md`.

## The version lives in the tagged commit

The version constant inside the shipped code must be bumped in the same
commit that gets tagged, so `tool --version` matches the release tag. This
is easy to miss, and it has shipped wrong before: a tag went out while the
constant still reported the previous version. Flow:

1. Open a release-commit PR: bump the version constant and date the
   changelog entry.
2. Get tests green, merge the PR.
3. Tag `vX.Y.Z` (lightweight) on the merged release commit. Never tag an
   older commit.
4. Push the tag.

## If CI builds the assets, the tag completes the release

Many release workflows build binaries and `.sha256` sidecars on tag push.
If yours does, the tag is the whole release. Before touching the tap:

```bash
gh run list --workflow=release.yml --limit 3  # wait for this tag's run to go green
gh release view v0.0.0 --json assets          # substitute the real tag; count the assets
```

The GitHub release must carry every expected asset: each binary and each
sidecar. A missing asset is half a release, and the tap would ship it.

## Recompute every checksum, trust none of the old ones

One wrong sha256 makes every `brew install` of the formula fail. `brew
audit` catches a mismatch after the fact; recompute before pushing instead.

```bash
# Source archive named by the formula's url line:
curl -sL "https://github.com/OWNER/REPO/archive/refs/tags/vX.Y.Z.tar.gz" | shasum -a 256

# Each versioned binary or resource asset. Prefer the CI-published sidecar:
curl -sL "https://github.com/OWNER/REPO/releases/download/vX.Y.Z/ASSET" \
  | shasum -a 256
# The sidecar should match what you just computed:
curl -sL "https://github.com/OWNER/REPO/releases/download/vX.Y.Z/ASSET.sha256"
```

Never copy a sha from the previous release, and never reuse one sha across
assets. Recompute all of them, every release.

## Update the formula

1. Branch in the tap repo.
2. Replace the old version with the new one everywhere in the formula: the
   `url` lines (the source archive plus one per architecture resource) and
   every `sha256` line (one for the archive, one per resource).
3. Run `ruby -c Formula/<name>.rb`. It checks syntax only, which is why
   step 2 needs care.
4. Commit, push the branch, open the PR, merge it.

## Verify what brew serves

```bash
brew update && brew info yourtap/yourformula
```

The output must show the transition, for example `0.8.17 -> stable 0.9.0`.
Quote that line as evidence. "I bumped the file" is not evidence.
`brew livecheck yourtap/yourformula` confirms the tap reports the new
version upstream. Run `brew audit --formula yourtap/yourformula` when the
audit tooling is available.

## Formula and cask version independently

A tap can ship a formula and a cask on different tag grammars: the formula
follows bare `v*` tags, the cask follows `app-v*` tags. A formula release
never moves the cask, and the reverse holds too. Diverging numbers are
correct, not staleness. Do not sync them. A future session that "fixes" a
version gap between the two streams is introducing a bug. For the concrete
instance, see `references/tailroute-tap.md`.

## Release notes and PR text are public

The GitHub release body and the tap PR body are public. Describe changes on
their own merits: no internal vocabulary, no private repo or issue
references, and redact hostnames or peer names from pasted command output.

## The version constant is not the release tag

The constant and the tag are two different things. The constant is bumped
in the release commit, so a working tree reports the previous version even
while it carries unreleased features. When you verify a local build, probe
capabilities first, such as feature presence in `--help` output, before you
trust a version string.

## References

- `references/checklist.md`: the whole flow as an ordered tick-box list.
- `references/tailroute-tap.md`: one concrete tap, with a CI-built formula
  stream and an independently versioned cask stream.
