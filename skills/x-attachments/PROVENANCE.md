# Provenance

- Original work, written 2026-11-23. No upstream.
- External dependency: X's undocumented syndication endpoint
  (`cdn.syndication.twimg.com/tweet-result`) — login-free, no key. Not a
  stable contract; if it breaks, the script degrades to a graceful
  `ok:false` and callers fall back to text-only behavior.
- The System One / System Two gate framing follows the in-repo convention
  used across skills (cheap typed decision before any deliberate pass).
