# Dual-run cross-validation — reproducer prompt template

Purpose: reproduce every count, byte offset, and hash from the primary run
before a verdict goes public. The reproducer is unscaffolded: it gets the
mechanical commands below and a report format, never attributions, never
the audit skill, never expected results. Pair one unscaffolded session with
the primary run; one flash-tier session is the documented pairing.

Fill in before pasting:

- `<APP_RESOURCES>` — the app Resources directory holding the files to sweep
- `<PRIMARY_FILE>` — the file the hash seal covers
- `<NEEDLES>` — the signature needle list, space-separated, quoted per item,
  taken from the app's `guide-NNN` regression recipe
- `<VARIANT_NEEDLES>` — the needles with at least one positive hit, for the
  offset pass

---

You are reproducing mechanical grep counts on binary files. Run the commands
exactly as given, in order, and report outputs verbatim. Do not read any
documentation, do not draw conclusions, do not commit anything, do not write
files. Work read-only.

All commands run from `<APP_RESOURCES>`. Use `rg`, never plain `grep`:
`grep -c` counts lines, not matches, and times out on bundles this size.

1. Hash seal:

       shasum -a 256 <PRIMARY_FILE>

2. Needle counts, one line per needle, repeated for each file in the sweep
   set (primary bundle plus every sidecar script):

       for s in <NEEDLES>; do printf "%-22s file:%s\n" "$s" \
         "$(rg -a --no-filename -F -c "$s" <FILE> 2>/dev/null || echo 0)"; done

3. Byte offsets of every needle with a positive count:

       rg -a -b -o "<VARIANT_NEEDLES>" <PRIMARY_FILE> | head -8

4. Route extraction, count and filtered:

       rg -a -o "/api/v[0-9]/[a-zA-Z0-9/_-]+" <PRIMARY_FILE> | sort -u | wc -l
       rg -a -o "/api/v[0-9]/[a-zA-Z0-9/_-]+" <PRIMARY_FILE> | sort -u | rg -i "upload|ingest|snapshot" || echo "no matching routes"

Report format: a plain table of needle counts (needle, per-file counts),
then the hash line, then the offsets, then the two route lines. If a
command errors, report the error text verbatim and continue with the rest.
Do not commit anything, do not write files.

---

Acceptance: every count, every offset, and the hash match the primary run.
Any divergence blocks the public verdict until explained. The reproducer's
own mechanical observations (such as line-count versus match-count notes)
are welcome; its conclusions are not — attribution stays with the primary
run.
