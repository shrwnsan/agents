---
name: x-api-ops
license: Apache-2.0
description: >
  Bootstrap and operate X (Twitter) API v2 access with pay-per-usage spend
  discipline. One-time console app setup checklist, OAuth 2.0 PKCE token
  bootstrap through a local callback listener, credential storage under
  ~/.config/x-api, probe-first cost estimation, tiered pulls under a monthly
  spending cap, and a Lists read/manage quick reference. Use when a project
  needs to read or manage X Lists, audit followers or graph data, or make any
  call against api.x.com, or when an X API call fails with 403 Forbidden,
  spend-cap, or invalid-authorization-code errors.
user-invocable: true
metadata:
  version: "1.0.0"
---

# X API Ops

## Overview

The X API v2 moved to pay-per-usage credits with no subscription tiers. Access
is two-layer: an app-only **Bearer token** for public data, and an OAuth 2.0
**user token** (PKCE) for anything owned, private, or writable. This skill
sets both up, stores credentials the way local integrations should be stored
(chmod 600 files under `~/.config/x-api`, never in a repo or a chat), and
prices work before running it.

Everything here was field-tested during a Lists audit that started on the
web-UI route and ended on the API after scraping proved unverifiable.

## One-time console setup

At [console.x.com](https://console.x.com), per app:

| Setting | Value |
|---|---|
| App permissions | **Read and write** (the default "Read" blocks `list.write` scopes at consent) |
| Type of App | Web App, Automated App or Bot |
| Callback URI / Redirect URL | `http://localhost:3000/callback` |
| Website URL | any placeholder |

Save the credentials the user context needs, keyed to files, not chat:

```bash
mkdir -p ~/.config/x-api && chmod 700 ~/.config/x-api
# Consumer Key -> client-id, Secret Key -> client-secret, Bearer Token -> bearer
chmod 600 ~/.config/x-api/*
```

After completing "User authentication settings", the console may issue a
**new OAuth 2.0 Client ID/Secret pair** distinct from the Consumer Key pair.
Replace both files together: a mixed pair fails the token exchange with
`invalid_client`. Also set the **monthly spend cap** (billing settings) to
your credit balance; the default has been observed to block calls with a bare
403 `Forbidden`.

## Token bootstrap

```bash
scripts/x-api-pkce-bootstrap.sh                # port 3000, 300s wait, opens browser
scripts/x-api-pkce-bootstrap.sh --port 3001 --no-open
```

The script starts a local callback listener, generates the PKCE pair, opens
the authorize URL, and waits for the consent redirect (tick the trust
checkbox, then click Authorize). State is verified against CSRF before the
code is exchanged; the token set (access, refresh, scope, expiry) is written
to `~/.config/x-api/token.json` with mode 600. Access tokens last about two
hours; the refresh token is the reason `offline.access` is in the default
scopes.

## Spend discipline

Authorization codes expire in seconds to minutes, so exchange immediately
after the consent click. Credits are spent per resource returned, and a
monthly spend cap blocks every call once reached with a bare 403, so always:

1. **Probe first.** Pull one small object (a 4-member List, not an 881-member
   one), then check the console usage meter to learn the observed rate.
2. **Tier the pulls.** Cheap inventory first (metadata), expensive rosters
   only where a decision needs them.
3. **Stay under the cap.** Reads of the same resource dedupe within a 24h UTC
   window, so same-day re-runs are free.

Observed costs (2026-11 rates; verify in the console):

| Operation | Endpoint group | Price |
|---|---|---|
| Owned Reads: owned_lists, followed_lists, list_memberships, pinned_lists | `GET /2/users/:id/...` | $0.001 / resource |
| List read, including member rosters | `GET /2/lists/:id`, `GET /2/lists/:id/members` | $0.005 / resource |
| List create | `POST /2/lists` | $0.010 / request |
| List manage: update, delete, add or remove member | `PUT/DELETE /2/lists/:id` | $0.005 / request |
| User read, handle to user_id | `GET /2/users/by/username/:handle` | $0.010 / resource |

## Bearer vs user context

The app-only Bearer reads **public** data (List lookup, members of public
Lists). The user token reads owned and private Lists and performs writes.
A user token that 403s on every endpoint with a bare `Forbidden` while the
Bearer works means user-context access is gated at the app level, not a
billing or scope problem: check the app permission level and user
authentication settings in the console, then re-authorize to mint a fresh
token.

## Known gotchas

- The consent page disables Authorize behind an **"I trust this app"**
  checkbox. The checkbox is a human attestation; tick it in the visible
  window rather than clicking around it.
- X injects **rotating suggestion cards into members pages**. Any DOM scrape
  of a members page returns a different fake roster on every load. Member
  data is only trustworthy from `GET /2/lists/:id/members`.
- Members pages are **recency-ordered**: the top of a big List shows the
  currently active accounts, so per-member dormancy is not measurable from a
  page-one sample.
- An authorization code is single-use and short-lived. If the exchange fails
  with `Value passed for the authorization code was invalid`, do not retry
  the same code; run a fresh authorize round.
- Old API Keys (25-character IDs) are not OAuth 2.0 Client IDs (34
  characters ending `:MTpjaQ`). The authorize endpoint accepts the former but
  consent fails; use the OAuth 2.0 Client ID from after the user
  authentication settings were saved.

## Lists quick reference

| Operation | Endpoint | Notes |
|---|---|---|
| Lookup by id | `GET /2/lists/:id` | `list.fields=member_count,follower_count,private,description` |
| Owned / followed / memberships / pinned | `GET /2/users/:id/owned_lists` and siblings | Owned Read pricing when id is the app owner |
| Roster | `GET /2/lists/:id/members` | paginate with `next_token`; `max_results` up to 100 |
| Create / update / delete | `POST /2/lists`, `PUT /2/lists/:id`, `DELETE /2/lists/:id` | user token required |
| Add / remove member | `POST /2/lists/:id/members`, `DELETE /2/lists/:id/members/:user_id` | user_id required, resolve via users/by/username |

## Scope

Reads and List management only. Posting, timelines, DMs, and follow-graph
writes are out of scope. When the API is unavailable, a logged-in browser
session can substitute for reads, but member captures from the web UI are
unverifiable and should never feed decisions.
