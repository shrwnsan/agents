---
name: x-attachments
description: >-
  Fetch and mine an X/Twitter post's attached images without login. Reads the
  post via the syndication API (no auth, no cookie, no third-party service),
  downloads each attachment, then runs a two-stage read: a System One gate
  classifies the image (substantive content vs decorative), and only
  substantive images get the full extraction pass. Use when an x.com or
  twitter.com status URL is shared and its images may carry content the post
  text doesn't (slide decks, charts, tables, screenshots of documents).
  Triggers on: an x.com/twitter.com status link shared by the user, "what's
  in the attachments", "read the images in this post".
metadata:
  version: "1.0.0"
---

# X Attachments

Post text is the cheap half of an X post; the attachments often carry the real
content. This skill retrieves them without login and reads only what pays for
its tokens.

## Step 1 — Fetch (script, deterministic)

Extract the numeric status id from the URL (the 15–19 digit number after
`/status/`), then run:

```bash
bun run scripts/fetch-attachments.mjs <status_id> --out-dir /tmp/x-attachments
```

The script:
- calls `https://cdn.syndication.twimg.com/tweet-result?id=<id>&lang=en&token=a`
  (login-free; `token=a` is a static placeholder the endpoint accepts)
- writes `post.json` (full payload) and `attachments/` (each `photos[]` entry
  as PNG, `name=large`)
- prints a JSON summary: post text, author, per-file sizes

If the endpoint 404s or returns no `photos`, the post has no images — say so
and stop. Never fall back to authenticated scrapers.

## Step 2 — Gate (System One, per image)

Read each image once and make ONE typed decision, evidence in hand:

```
substantive: text | slides | chart | table | document | meme | photo | decorative
```

Judgment standard: does the image carry information the post text does not
contain? A slide deck with the whole playbook is substantive. A product logo,
a reaction meme, a stock photo is not. When borderline (e.g. a photo of a
whiteboard), lean `substantive` — the deep read of a borderline image costs
one call; a missed deck costs the whole point of the skill.

Record every verdict. Non-substantive images are done: report "n of m images
non-substantive, skipped" and move on.

## Step 3 — Deep read (System Two, only on gate passes)

For each substantive image, extract the full content: transcribe structured
text (headings, bullets, numbers) preserving hierarchy, describe charts with
their axes and the actual data points, and note anything the post text
contradicts. Output one merged markdown block per image, then fold all of
them into a single distilled summary that answers: what do the attachments
add that the post text lacks?

## Cost discipline

- Hard cap 4 images per post (the endpoint returns at most 4; never paginate around it)
- One gate read per image, one deep read per gate pass — never re-read
- If the fetch fails or the API errors, degrade gracefully: report the post
  text only, note the failure mode, never block the caller on attachment errors

## Vault integration

When called from the Sumi drain flow, the deep-read output is appended to the
item's markdown result (section `## Attachments`), so the vault stores
distilled text, never raw images. Raw PNGs stay in the out-dir and are the
caller's to delete.
