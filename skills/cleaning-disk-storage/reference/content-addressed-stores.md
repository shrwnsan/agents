# Content-addressed caches (symlink stores)

Some tools deduplicate downloads. Payload bytes live once in a global
store. Visible per-package folders hold pointers (symlinks) into that
store instead of holding the bytes. Removing a folder removes pointers
only, so payloads with no remaining pointer ("orphans") pile up
invisibly: the store grows to tens of GB while every visible folder
looks small.

The same pattern appears in Hugging Face model caches, git object
stores, pnpm's store, and container layer caches. One method covers all
of them: compute which payloads still have live pointers, reclaim the
rest.

## Detection

Signals that a cache uses this pattern:

- A store directory holding many payload files named by hash, often
  under a two-character fan-out prefix (`store/ab/<hash>`)
- Package folders whose payload files are symlinks into the store
- Per-payload bookkeeping files next to the payloads (`.refs`, `.lock`,
  or similar)
- A store marker file (dotfile at the store root)

```bash
# do symlinks leave the visible folders into a hash store?
find <cache-root> -maxdepth 5 -type l | head

# store size vs visible folder sizes
du -sh <cache-root>/<store> <cache-root>/*/ | sort -rh | head
```

## Hugging Face hub cache

Instance of the pattern, installed at `~/.cache/huggingface/hub`
(HF_HOME overrides the location). Layout:

```
hub/
├── blobs/                          # the payload store
│   ├── <2-char>/<hash>             # payload bytes, deduplicated across models
│   ├── <2-char>/<hash>.refs        # bookkeeping: model blob paths claiming this payload
│   ├── <2-char>/<hash>.lock        # download bookkeeping
│   └── .huggingface-shared-blobs   # store marker. never delete
├── models--<org>--<name>/          # per-repo entry
│   ├── blobs/<hash>                # symlink into the store
│   └── snapshots/<rev>/<file>      # symlink into the store
└── <plain-name>/                   # locally converted models may hold real files
```

Rules of this layout:

- Payload bytes exist only under `hub/blobs`. Visible files are
  pointers or small metadata.
- A `.refs` sidecar lists the per-model blob paths that claim the
  payload. One payload can serve several models.
- Model directories from any project or tool sharing this cache hold
  pointers into it. A sweep that scans only one project's folders
  misclassifies live payloads as orphans.
- `huggingface-cli delete-cache` is deprecated and blind to store
  orphans. It operates per visible repo. No vendor command reclaims
  store orphans.

## The orphan test

A payload file is an orphan only when both signals agree:

1. **No live pointer.** Resolve every file under the cache root
   (excluding the store subtree) to its real path. The payload's real
   path appears in none of them.
2. **Stale bookkeeping.** Every path in the payload's `.refs` sidecar
   either no longer exists, or no longer resolves to this payload.

Algorithm, implementation-independent:

```
1. referenced = realpaths of all files under cache root,
   store subtree excluded
2. candidates = payload files in the store
   (skip dotfiles, skip *.refs, skip *.lock)
3. drop candidates whose realpath is in referenced
4. for each remaining candidate: read its .refs. If any listed path
   exists and resolves back to this payload, drop the candidate
5. plan = candidates, each with its own .refs and .lock sidecars
6. STOP. Re-run steps 1-5 immediately before deleting. If the plan
   changed, or any candidate became referenced, abort and re-review
```

## Hard rules

- Never candidate store metadata. Dotfiles, `.refs`, and `.lock` files
  keep live payloads working. A naive "unreferenced means orphan" scan
  flags the sidecars of live payloads, and deleting those corrupts the
  cache.
- Protect by resolution, not by name. The referenced set from step 1
  already protects every model that any project, tool, or concurrent
  process points at, including entries added after the scan started.
  Hardcoded protected-name lists go stale.
- Move to Trash, never delete in place. Reclamation stays reversible.
- `df` is not the success metric. Trashing to the Trash frees no
  reported space until the Trash is emptied. Measure the store with
  `du` before and after, report that the Trash holds the bytes, and
  leave emptying the Trash to the user.
- Two independent computations must agree exactly before any deletion.
  Do not gate on sizes; measured sizes go stale between scan and
  execute.
- Stop model servers before sweeping. Payloads may be memory-mapped.
  Restart servers afterward and confirm the served model.

## Verification after reclamation

- Functional: run a real workload against each protected model
  (generate text, encode a sentence, score a pair).
- Structural: open payload files and read them completely. For
  safetensors, fetch every tensor. This reads every byte and takes
  seconds. Prefer it over slow inference when a model loads but
  responds slowly; slow inference is not evidence of corruption.
- Bookkeeping: the referenced set after reclamation must match the set
  from before, byte for byte.

## What not to do

- Do not delete a visible model folder as a cleanup. It frees nothing
  from the store and may break the model.
- Do not trust `df` deltas right after trashing.
- Do not wrap a vendor cleaner (delete-cache style) and assume store
  orphans are covered.
