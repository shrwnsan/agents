# Retro 001: cross-harness skill state and the ZCode v3.18.2 regression round

Date: 2026-11-16. Scope: the auditing-agent-harnesses state migration and the ZCode v3.18.2.10443 regression round. Harness: pi (glm-5.3-flash), ported from Claude Code.

## What we set out to do

Close the harness-portability gap in the audit workflow. Session state died with Claude Code transcripts, evidence lived in `~/.cache` under cache semantics, and open questions had no harness-neutral home. Then run the first audit round under the new layout.

## What happened

1. **Sync staleness resolved itself mid-flight.** Our drift check found 10 installed skills stale. Before we could pull, the agents repo advanced upstream and the installed skills were synced between our checks. We verified the new state instead of redoing the work.
2. **The pycache root cause was structural.** Untracked, gitignored caches in the agents repo working tree get rsynced verbatim by any skill-sync tooling that copies the working tree rather than git HEAD. `rsync --delete` cannot remove them; from rsync's point of view they are part of the source. Live-side re-pollution appeared the same day when our own pytest run created caches in an installed skill, which proved the second vector. The fix belongs in the sync tool (a cache sweep before the rsync loop), so it runs on every sync instead of relying on manual cleanup.
3. **Evidence migration split by skill boundary.** The old shared cache directory served two skills. App-audit receipts moved to `~/.local/share/agent-skills/auditing-agent-harnesses/evidence/<app>/`, and machine sweeps moved to `~/.local/share/agent-skills/live-system-forensics/evidence/`. A breadcrumb README at the old path redirects readers until contracts sync.
4. **Open-threads backfill recovered state that existed only in session data.** Six threads distilled from transcripts, receipts, and the app's guide. Three of them (a vendor privacy-policy residual, a pending accelerator baseline, the bounding of a lost receipt) existed only in Claude Code session files before the backfill.
5. **The v3.18.2 round was the first under the new layout and wrote nothing to /tmp.** The failure mode behind a previously lost receipt (written to a volatile directory during the 2026-10-23 round) can no longer occur.

## What the round found

- Verdict CLEAN, 9 of 9 classes cleared with evidence. The coverage ledger holds 14 validated rounds and the guide's coverage table is regenerated. Codesign deep-strict verify and spctl both passed in this session.
- **State restructure.** The vendor moved all `~/.zcode/*.json` state files under `~/.zcode/v2/` in this build. A C6 check at the old paths would have reported total data loss. We re-checked modes at the new location: the sensitive set held at 0600. The known v2-remnant files remain 0644 at their new paths.
- **Needle counts changed; their roles did not.** `relayWsUrl` fell from 10 occurrences to 8, `autoDownloadAndInstallUpdates` from 53 to 8, and `registry.npmjs.org` from 10 to 8. Context sampling confirmed the same role families: the settings schema still defaults auto-update to off, and the relay sites remain the known auth-gated template and QR pairing flow. Counting without contexts would have produced either a false alarm or false comfort.
- **One vendor watch resolved itself.** The vendor removed the stale v3.18.0 computer-use helper copy, and the bundled helper now matches the host at 3.18.2.
- **captureRepoSnapshot is still a dead flag.** Exactly one occurrence, never read. Its watch thread carries.
- **The accelerator escalated all four needle windows.** Zero auto-resolves; all four were human-resolved as benign per lineage. The model alias is unchanged since the last round, so no baseline re-run was owed.

## Lessons (now folded into auditing-agent-harnesses 1.5.0)

1. **Regression recipes need to re-enumerate paths, not pin them.** The C6 recipe named absolute paths that the vendor restructured. It survived because we enumerated the data directory before concluding anything. Phase 1 now says: re-enumerate state/data directories on every version jump, next to the existing sidecar and package rule.
2. **Cache hygiene belongs in the sync tool.** Without the sweep, the caches reappear on every sync, because rsync copies the working tree and gitignore hides them from review. This lesson lives in local sync tooling, not in this repo.
3. **Count drift is normal; role drift is signal.** The Version-Jump Regression section now requires a sampled byte-window context in the receipt for every changed needle count.
4. **State files want current-state semantics; logs want append-only.** The open-threads file updates each thread in place. The ledger and receipts stay append-only. Phase 4 now states which artifact is which.
