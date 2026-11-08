# Dual-run cross-validation — reproducer prompt template

Purpose: reproduce every count, byte offset, and hash from the primary run
before a verdict goes public. The reproducer is unscaffolded: it gets the
mechanical commands below and a report format, never attributions, never
the audit skill, never expected results. Pair one unscaffolded session with
the primary run; one flash-tier session is the documented pairing.

Fill in before pasting:

- `<APP_RESOURCES>`: the app Resources directory holding the files to sweep
- `<PRIMARY_FILE>`: the file the hash seal covers
- `<SWEEP_FILES>`: `<PRIMARY_FILE>` plus every sidecar script, space-separated,
  as paths relative to `<APP_RESOURCES>`
- `<NEEDLES>`: the signature needle list, space-separated, quoted per item,
  taken from the app's `guide-NNN` regression recipe

---

You are reproducing mechanical grep counts on binary files. Run the commands
exactly as given, in order, and report outputs verbatim. Do not read any
documentation, do not draw conclusions, do not commit anything, do not write
files. Work read-only.

All commands run from `<APP_RESOURCES>`. Use `rg`, never plain `grep`, which
times out on bundles this size. Count positions, not lines. In either tool,
`-c` counts matching lines, and a minified bundle can hold several matches
on one line.

1. Hash seal:

       shasum -a 256 <PRIMARY_FILE>

2. Needle counts, one line per needle and file:

       for s in <NEEDLES>; do for f in <SWEEP_FILES>; do
         printf "%-22s %-16s %s\n" "$s" "$f" \
           "$(rg -a -o -F -- "$s" "$f" | wc -l | tr -d ' ')"
       done; done

3. Byte offsets, one line per position, for every needle in every file. A
   needle with no hits in a file prints nothing. Do not cap or truncate
   this output:

       for s in <NEEDLES>; do for f in <SWEEP_FILES>; do
         rg -a -b -o -F -- "$s" "$f" | sed "s|^|$f:$s@|"
       done; done

4. Route extraction, count and filtered:

       rg -a -o "/api/v[0-9]/[a-zA-Z0-9/_-]+" <PRIMARY_FILE> | sort -u | wc -l
       rg -a -o "/api/v[0-9]/[a-zA-Z0-9/_-]+" <PRIMARY_FILE> | sort -u | rg -i "upload|ingest|snapshot" || echo "no matching routes"

Report format: the count lines from step 2, then the hash line, then every
offset line from step 3, then the two route lines. If a command errors,
report the error text verbatim and continue with the rest. Do not commit
anything, do not write files.

---

Acceptance: every count, every offset, and the hash match the primary run.
Any divergence blocks the public verdict until explained. Within the
reproducer's output, the offset lines for each needle and file must also
equal that pair's step-2 count; a mismatch means a command was altered or
its output was cut short. The reproducer's own mechanical observations are
welcome. Its conclusions are not, because attribution stays with the
primary run.
