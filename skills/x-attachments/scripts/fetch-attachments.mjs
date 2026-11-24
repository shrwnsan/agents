#!/usr/bin/env bun
// Fetch an X/Twitter post's attached images login-free via the syndication API.
// Usage: bun run fetch-attachments.mjs <status_id> [--out-dir DIR]
// Prints a JSON summary on stdout. Exits 0 with {"photos": 0} when the post has no images.

import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

const args = process.argv.slice(2);
const id = args.find((a) => /^\d{15,19}$/.test(a));
const outIdx = args.indexOf("--out-dir");
const outDir = outIdx >= 0 ? args[outIdx + 1] : "/tmp/x-attachments";

if (!id) {
  console.error('usage: fetch-attachments.mjs <status_id> [--out-dir DIR] — status id is the 15-19 digit number after /status/');
  process.exit(2);
}

const API = `https://cdn.syndication.twimg.com/tweet-result?id=${id}&lang=en&token=a`;

async function j() {
  const res = await fetch(API, {
    signal: AbortSignal.timeout(20_000),
    headers: { "user-agent": "Mozilla/5.0 (compatible; x-attachments/1.0)" },
  });
  if (res.status === 404) return null; // post gone or no embed — treat as no-images
  if (!res.ok) throw new Error(`syndication API ${res.status}`);
  return res.json();
}

let post;
try {
  post = await j();
} catch (e) {
  console.log(JSON.stringify({ ok: false, error: `fetch-failed: ${String(e).slice(0, 120)}` }));
  process.exit(0); // graceful: caller falls back to text-only behavior
}

if (!post) {
  console.log(JSON.stringify({ ok: true, photos: 0, note: "post not embeddable or missing" }));
  process.exit(0);
}

const photos = post.photos ?? [];
await mkdir(join(outDir, "attachments"), { recursive: true });

const files = [];
for (const [i, p] of photos.slice(0, 4).entries()) {
  const url = `${p.url}?name=large`;
  const file = join("attachments", `photo-${i + 1}.png`);
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(30_000) });
    if (!res.ok) throw new Error(String(res.status));
    const buf = Buffer.from(await res.arrayBuffer());
    await writeFile(join(outDir, file), buf);
    files.push({ file, bytes: buf.length, source: url });
  } catch (e) {
    files.push({ file, error: String(e).slice(0, 80), source: url });
  }
}

console.log(JSON.stringify({
  ok: true,
  statusId: id,
  author: post.user?.name ?? post.user?.screen_name ?? null,
  handle: post.user?.screen_name ?? null,
  text: post.text ?? "",
  photos: photos.length,
  downloaded: files,
}, null, 2));
