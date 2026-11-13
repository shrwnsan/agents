# Tap release checklist

Ordered. Do not start a section before the previous one is fully checked.

## Tag the release

- [ ] Version constant bumped in the release commit (the same commit that will be tagged)
- [ ] Changelog entry dated
- [ ] Tests green
- [ ] Release-commit PR merged
- [ ] Lightweight tag `vX.Y.Z` on the release commit, pushed

## Confirm CI shipped the assets

- [ ] Release workflow run green for this tag
- [ ] GitHub release carries all expected assets (every binary + every `.sha256` sidecar; count them)

## Recompute checksums

- [ ] Source archive sha256 recomputed (`curl -sL <archive-url> | shasum -a 256`)
- [ ] Every asset sha256 fetched from its sidecar or recomputed from the artifact
- [ ] Sidecars match the values you computed

## Bump the tap

- [ ] Formula updated: one global version replace across all `url` lines, all `sha256` lines recomputed
- [ ] `ruby -c Formula/<name>.rb` passes
- [ ] Tap PR opened with a hygienic public body, merged

## Verify

- [ ] `brew update && brew info <user>/tap/<name>` shows the transition; quote the `old -> stable new` line as evidence
- [ ] (Optional) `brew audit --formula <user>/tap/<name>` clean
