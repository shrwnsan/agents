# Provenance

Vendored from [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) at commit `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8` (MIT license, upstream `LICENSE` copied alongside). Source path upstream: `skills/security-audit/`.

Local changes vs upstream:

- Removed upstream `*.test.cjs` test files (Node built-in test runner artifacts; the two validators `validate-findings.cjs` / `validate-coverage-ledger.cjs` are retained and verified working).
- No other edits; SKILL.md body is upstream-verbatim.

Overlap check at acceptance: no duplicate coverage in this repo. `review-pr` is diff-scoped peer review; `live-system-forensics` is host runtime forensics; `auditing-agent-harnesses` audits agent desktop apps. This skill is the only whole-codebase adversarial vulnerability audit here. Trigger overlap with `review-pr` is limited to the word "security" — SKILL.md self-guards via its guidance/full-audit mode split.
