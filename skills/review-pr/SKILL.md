---
name: review-pr
description: >
  Perform comprehensive peer code review of GitHub pull requests. Analyzes code
  quality, security, performance, testing, and architecture. Use when user asks to
  review a PR, check a pull request, or says "review PR #<number>". Also triggers
  on "code review", "PR review", "check this PR", or when a PR URL is provided.
user-invocable: true
---

# Peer Code Review

Review pull requests with structured feedback using severity-tagged findings.
Reads the diff and CI status — does not modify the working tree.

## Pre-Review Confirmation

- **User-invoked** (`/review-pr <number>`): proceed directly, no confirmation needed.
- **Auto-invoked** (harness matched the description): confirm the PR number and repo
  with the user before gathering context. Example: "I'll review PR #42 in
  `owner/repo`. Shall I proceed?"

## Repository Detection

Detect the repository from git remotes:

```bash
ORIGIN_URL="$(git remote get-url origin 2>/dev/null || echo '')"
UPSTREAM_URL="$(git remote get-url upstream 2>/dev/null || echo '')"

ORIGIN_REPO="$(echo "$ORIGIN_URL" | sed -E 's|.*[:/]([^/]+/[^/.]+)(\.git)?$|\1|')"
UPSTREAM_REPO="$(echo "$UPSTREAM_URL" | sed -E 's|.*[:/]([^/]+/[^/.]+)(\.git)?$|\1|')"
```

- Single remote: use it directly.
- Multiple remotes (origin + upstream): default to origin. Mention both if ambiguous.
- No remotes: ask the user for `owner/repo`.

If the argument contains a full URL or `owner/repo` format, use that instead.

## Context Gathering

Collect PR context using `gh` CLI. Always pass `--repo "$REPO"` explicitly.

1. **PR details**: `gh pr view <number> --repo "$REPO" --json title,body,author,headRefName,baseRefName,additions,deletions,files,commits`
2. **Changed files**: `gh pr diff <number> --repo "$REPO" --name-only`
3. **Code diff**: `gh pr diff <number> --repo "$REPO" | head -n 1000`
4. **CI status**: `gh pr checks <number> --repo "$REPO"`

## Review Framework

Read the diff **twice** before commenting. Focus on these areas:

### 1. Understanding & Intent
- Does the title and description communicate the purpose?
- Are changes scoped appropriately?
- Does the PR link to relevant issues?

### 2. Code Correctness
- Logic correctness: does the code do what it claims?
- Edge cases: null/undefined, empty collections, boundaries, errors
- Bugs: off-by-one, race conditions, resource leaks

### 3. Security & Safety
- Input validation and sanitization
- Injection risks (SQL, XSS, command)
- Hardcoded credentials or API keys

### 4. Architecture & Design
- Appropriate abstraction level
- Follows existing patterns in the codebase
- Code smells: long functions, deep nesting, duplication

### 5. Performance
- Algorithmic complexity (O(n²) when O(n) possible?)
- N+1 queries, unnecessary computations in loops

### 6. Testing Coverage
- Unit tests for new functions
- Edge case coverage
- Are existing tests still passing? (check CI status)

### 7. Code Style & Consistency
- Follows project style guidelines?
- Clear, intention-revealing naming?
- Comments explain "why" not "what"

## Finding Format

Use severity + category tags for every finding:

- **Severity**: `[CRITICAL]` (must fix), `[MAJOR]` (should fix), `[MINOR]` (nice to have)
- **Category**: `[BUG]` `[SECURITY]` `[PERF]` `[STYLE]` `[DOCS]` `[TEST]` `[NIT]`

For each finding provide:
- Reference in `path/to/file.ext:line-start-line-end` form
- A short title
- A 1-3 sentence explanation
- An optional suggested patch in a fenced diff block

**Only report findings you are confident about.** Do not speculate.

## Output Format

### Review Summary

| Category | Count |
| --- | --- |
| [BUG] | n |
| [SECURITY] | n |
| [PERF] | n |
| [STYLE] | n |
| [DOCS] | n |
| [TEST] | n |
| [NIT] | n |

### Executive Summary

2-3 sentence overview of PR quality and readiness.

**Overall Assessment:** [Strong Approve | Approve | Approve with Suggestions | Request Changes]

**Key Strengths:**
- strength 1

**Key Concerns:**
- concern 1

### Detailed Findings

#### Critical/Major Issues

1. **[CRITICAL][BUG] path/to/file.ext:42-47 – Short title**
   Explanation.

   ```diff
   - problematic code
   + suggested fix
   ```

#### Minor Issues/Nits

1. **[MINOR][STYLE] path/to/file.ext:110 – Variable naming**
   Explanation.

### Kudos

- `path/to/file.ext:line` – Great use of [specific pattern]!

### Verdict

- **Blocking issues exist**: "This PR requires changes before merge. Please address the Critical and Major issues above."
- **No blockers but has suggestions**: "Ready to merge. Consider the Minor improvements for future iterations."
- **PR is excellent**: "Well-crafted and ready to merge."

## Post-Review

After presenting the review, ask the user:

> "Would you like me to post this review as a comment on PR #<number>?"

If yes, post using:

```bash
gh pr comment <number> --repo "$REPO" --body "<review-content>"
```

## Special Considerations

- **First-time contributors**: be more educational and encouraging
- **Large PRs**: suggest splitting into smaller, focused PRs
- **Refactoring PRs**: ensure tests cover the refactored code
- **Breaking changes**: verify migration guide and documentation
- **Security-sensitive code**: extra thorough security review
