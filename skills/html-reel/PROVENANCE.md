# PROVENANCE — html-reel

- **Source:** [MengTo/Skills](https://github.com/MengTo/Skills) `agent-skills/media/html-reel`
- **Pinned:** `a45892d2fdadab75b31fb16abecc02f101b31c43` (2026-10-25, "HTML Reel: paint the macOS hand cursor out of a source recording")
- **License:** MIT (upstream repo root LICENSE vendored verbatim in this directory). This directory is **excluded from the hub's Apache-2.0** — see the vendor-and-pin policy in `skills/README.md`.
- **Vendored:** 2026-10-27, byte-true (no edits to SKILL.md, references, scripts, agents, or demo).
- **Tracking:** listed in `.upstream.yml` (`preserve: [PROVENANCE.md, LICENSE]`); refresh by hand-running the sync-upstream workflow, then diff against this pin. Bumping the pin repeats the vetting pass.

## What it does

Turns a tweet, landing page, YouTube video, or video file into a 9:16 (or 4:5/1:1/16:9) reel cut to a voiceover, word by word: HTML scenes drawn from one clock (`window.__frame(t)`), a cloned ElevenLabs voice with word timestamps, demo video framed and cut to words, assembled in Fil's video editor over MCP, scored by blind judges. Faceless or with a camera placeholder swapped for real takes and retimed by word anchors.

## Vendor review notes (2026-10-27)

- **Quality:** exceptional SKILL.md — failure-driven rules each naming the failure it prevents, verification checklist, real measured numbers from shipped reels. Among the strongest skills in the upstream repo.
- **Safety scan:** clean. `child_process` calls are ffmpeg/playwright/sips invocations for the media pipeline; the ElevenLabs key is read from `ELEVENLABS_API_KEY` (env or `--env-file`) and never printed; outbound hosts are api.elevenlabs.io, api.fxtwitter.com, fil.design, fonts.googleapis.com, x.com/youtu.be — all expected for the pipeline.
- **Not live-tested** — the gate's behavioral pass could not run here: the pipeline needs `ELEVENLABS_API_KEY` (paid), Fil's video editor over MCP, ffmpeg + OpenCV in a venv + python3, and several scripts are macOS-centric (DreamCut window recording, macOS cursor templates). Structural phases applied by hand: frontmatter valid, files match the upstream tree at the pin, scripts referenced from SKILL.md all exist. Reviewer rerun: `git diff a45892d2fd~1 a45892d2fd -- agent-skills/media/html-reel` against this directory.
- **Dependency reality:** usable where a Mac + Fil + ElevenLabs key exist; in the Linux agent container, expect read/reference value (the SKILL.md's rules on covers, captions, cut-to-words, retiming) rather than end-to-end runs.
- **Fit:** no overlap with motion-craft (web motion design) or og-social-cards (static card QA) — this is the hub's first vertical-video skill. Adopted on owner instruction (review of Meng To's latest publication).
