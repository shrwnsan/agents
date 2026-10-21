# Provenance

Vendored from [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman), path `plugins/caveman/skills/caveman`, at commit `2178ed6495c3c0ecd7d037e60acf3b1d0c554b97` (2026-10-21 — latest commit touching that path). Apache-2.0 (upstream repo license).

Local changes vs upstream:

- Added this `PROVENANCE.md`.

## Layout note (2026-10-21)

Upstream moved to plugin-wrapper format (`plugins/caveman/` with a multi-skill `cavecrew` suite). We sync only the **inner** `plugins/caveman/skills/caveman` folder — same rule as frontend-design: never the wrapper. The old flat `skills/caveman` path still exists upstream but is legacy: its README references repo-root eval data (`evals/snapshots/results.json`) that is outside any skill folder; the plugin-path skill ships no README, which resolves the dangling-reference gate FAIL naturally. Do not re-add a README referencing repo-root paths.
