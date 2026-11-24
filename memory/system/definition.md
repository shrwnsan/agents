---
type: system
---

# Memory system

This bundle stores durable, operation-tested knowledge about external APIs and
services (under `tools/`), so any agent can read it before touching the
service instead of rediscovering quirks by trial and error.

Conventions:

- OKF v0.2: one Markdown concept per file, opened by YAML frontmatter whose
  first field is `type` (e.g. `tool`). `index.md` and this file are exempt.
- Optional frontmatter fields: `title`, `description`, `tags`.
- Every claim in `tools/` files should be verified against the live service
  (or clearly marked as unverified/inferred) — these files exist because
  documentation drifted from behavior.
- When a claim is corrected, update the file and keep only useful history.
- Keep `index.md` accurate; it is the retrieval entry point.
