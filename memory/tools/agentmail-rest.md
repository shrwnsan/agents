---
type: tool
title: AgentMail REST
description: Endpoint quirks and probe-safety rules for api.agentmail.to, verified against the live API
tags: [email, api, agentmail]
---

# AgentMail REST

Inbox + API wrapper knowledge for `api.agentmail.to`. Auth is injected by the
local HTTP proxy—never set an Authorization header yourself; a placeholder
header passes through raw and fails.

## Core endpoints

| Action | Call |
|---|---|
| List threads | `GET /threads` |
| Read thread | `GET /threads/{thread_id}` |
| List messages | `GET /inboxes/{inbox}/messages` |
| Send (new or forced thread) | `POST /inboxes/{inbox}/messages/send` |
| Reply to one message | `POST /inboxes/{inbox}/messages/{message_id}/reply` |
| Label a thread | `PATCH /inboxes/{inbox}/threads/{thread_id}` with `{"add_labels":["…"]}` |
| Delete a message | `DELETE /inboxes/{inbox}/messages/{message_id}` (permanent, no trash) |
| Mint a key | `POST /api-keys` |

## Quirks that bite

- **`thread_id` in a send body is ignored** — `POST /messages/send` with a
  `thread_id` still opens a new thread on your side. The recipient sees the
  matching subject, but your thread list splits. To stay in a thread, use the
  message-level `/reply` endpoint.
- **`message_id` is an RFC-2822 string** (`<…@email.amazonses.com>`). URL-encode
  it fully (angle brackets included) for per-message endpoints; `thread_id` is a
  plain UUID.
- **No archive operation exists.** Archiving = label a thread `archived` via
  PATCH; the message list has no label filter, so exclude client-side.
- **DELETE is permanent** — no trash, no undo. Archiving covers almost every
  "tidy up" need; reserve DELETE for messages you sent in error.
- **Key scopes are mint-time fixed.** `POST /api-keys` mints inbox/pod-scoped
  keys only; org-level keys cannot be self-served (support request territory).
  A key's prefix tells you its scope (`am_us_inbox_…` = inbox-scoped).

## Probe safety (read before touching the API)

Never probe a POST/DELETE endpoint against the live mailbox. `POST /api-keys`
mints a real key; `/messages/send` and `/reply` deliver real email—there is no
dry-run flag. To learn a request shape:

1. Read the message objects you already have (`GET /threads/{id}`) and mirror
   their field structure.
2. If a probe is unavoidable, use synthetic content, expect delivery, and
   delete the result the moment it lands—then say so in your report.

A shape learned from existing objects costs nothing; a shape learned by
sending costs an email.

## Provenance

Original work, first version 2026-11-24. Every quirk verified live against
api.agentmail.to during Oct–Nov 2026 inbox operations (thread-split behavior,
404 on the thread-level reply route, mint-time key scoping, no archive op).
The probe-safety rules were added after a live mis-send on 2026-11-24: a probe
of the reply endpoint delivered its literal probe text. The rule is learn
shapes from existing objects, never from live side-effecting calls.
