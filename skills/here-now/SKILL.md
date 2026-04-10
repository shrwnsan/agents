---
name: here-now
description: >
  Publish files and folders to the web instantly. Static hosting for HTML sites,
  images, PDFs, and any file type. Sites can connect to external APIs (LLMs,
  databases, email, payments) via proxy routes with server-side credential
  injection. Use when asked to "publish this", "host this", "deploy this",
  "share this on the web", "make a website", "put this online", "upload to
  the web", "create a webpage", "share a link", "serve this site", "generate
  a URL", or "build a chatbot". Outputs a live, shareable URL at {slug}.here.now.
metadata:
  agent_affinity: nanoclaw
  upstream: heredotnow/skill
  upstream_version: "1.11.0"
  hardening:
    - dangerous_extension_blocking
    - suspicious_extension_warnings
    - pre_upload_secret_scanning
    - credential_file_permissions
    - unknown_mime_type_blocking
    - bundled_jq_binary
---

# here.now

**Skill version: 1.11.0 (NanoClaw hardened)**

Create a live URL from any file or folder. Static hosting with optional proxy routes for calling external APIs server-side.

> **NanoClaw hardening**: This fork adds security layers on top of the upstream [heredotnow/skill](https://github.com/heredotnow/skill) publish script. Dangerous file types are blocked, suspicious types require opt-in, and pre-upload scanning detects leaked credentials.

## Requirements

- Required binaries: `curl`, `jq` (bundled in `bin/jq`)
- Optional environment variable: `$HERENOW_API_KEY`
- Optional credentials file: `~/.herenow/credentials`

**Note:** The `file` command is intentionally NOT required. Unknown file types are blocked by default rather than detected via libmagic.

## Create a site

```bash
./scripts/publish.sh {file-or-dir}
```

Outputs the live URL (e.g. `https://bright-canvas-a7k2.here.now/`).

## Security Layers

### Layer 1: Dangerous extensions (always blocked)

Files with these extensions or names are **never** uploaded:

| Type | Extensions / Patterns |
|------|----------------------|
| Secrets | `.env*`, `*.secret*`, `*.credential*` |
| Keys | `.pem`, `.key`, `.p12`, `.pfx`, `.jks`, `.keystore`, `id_rsa*`, `id_ed25519*`, `.gpg`, `.asc`, `.ppk`, `.ssh`, `.rsa`, `.ec`, `.der` |
| Certificates | `.crt`, `.cer`, `.p7b`, `.p7c` |
| Auth | `.htpasswd`, `.netrc` |

### Layer 2: Suspicious extensions (warn + opt-in)

Files with backup/temp/unknown extensions are blocked unless `--allow-suspicious` is passed:

`.bak`, `.old`, `.tmp`, `.temp`, `.cache`, `.log`, `.swp`, `.swo`, `.orig`, `.save`, `.dist`, `.map`, and files with **no extension**.

### Layer 3: Unknown extensions (warn + opt-in)

Extensions not in the known web-safe list (30+ types) are blocked unless `--allow-unknown` is passed. These are published as `application/octet-stream`.

### Layer 4: Pre-upload secret scanning

Text files are scanned for leaked credentials before upload. If any matches are found, the publish is **aborted**:

| Pattern | Matches |
|---------|---------|
| `sk-[...]` | OpenAI API keys |
| `ghp_/gho_/ghu_/ghs_` | GitHub tokens |
| `xox[bsp]-` | Slack tokens |
| `AKIA[...]` | AWS access keys |
| `-----BEGIN.*PRIVATE KEY-----` | Private keys |
| `AIza[...]` | Google API keys |
| `hooks.slack.com/services/` | Slack webhooks |

Binary files (images, fonts, media) and files over 1MB are skipped during scanning.

### Layer 5: Credential file permissions

If `~/.herenow/credentials` exists and is world-readable, a warning is printed recommending `chmod 600`.

## Script options

| Flag | Description |
|------|-------------|
| `--slug {slug}` | Update an existing site instead of creating |
| `--claim-token {token}` | Override claim token for anonymous updates |
| `--title {text}` | Viewer title (non-HTML sites) |
| `--description {text}` | Viewer description |
| `--ttl {seconds}` | Set expiry (authenticated only) |
| `--client {name}` | Agent name for attribution |
| `--base-url {url}` | API base URL (default: `https://here.now`) |
| `--allow-nonherenow-base-url` | Allow sending auth to non-default base URL |
| `--allow-suspicious` | Include files with suspicious extensions |
| `--allow-unknown` | Include files with unknown extensions |
| `--api-key {key}` | API key override (prefer credentials file) |
| `--spa` | Enable SPA routing (serve index.html for unknown paths) |

## Update an existing site

```bash
./scripts/publish.sh {file-or-dir} --slug {slug}
```

The script auto-loads the `claimToken` from `.herenow/state.json` when updating anonymous sites.

## API key storage

The publish script reads the API key from these sources (first match wins):

1. `--api-key {key}` flag (CI/scripting only)
2. `$HERENOW_API_KEY` environment variable
3. `~/.herenow/credentials` file (recommended for agents)

To store a key:
```bash
mkdir -p ~/.herenow && echo "{API_KEY}" > ~/.herenow/credentials && chmod 600 ~/.herenow/credentials
```

**IMPORTANT**: After receiving an API key, save it immediately. Never commit credentials or local state files to source control.

## What to tell the user

- Always share the `siteUrl` from the current script run.
- When `publish_result.auth_mode=authenticated`: tell the user the site is **permanent**.
- When `publish_result.auth_mode=anonymous`: tell the user the site **expires in 24 hours** and share the claim URL if available.

## Limits

| | Anonymous | Authenticated |
|---|---|---|
| Max file size | 250 MB | 5 GB |
| Expiry | 24 hours | Permanent |
| Rate limit | 5 / hour / IP | 60 / hour free, 200 / hour hobby |

## Beyond the script

For delete, metadata patch (password protection, payment gating), duplicate, claim, list, custom domains, handles, links, proxy routes, and SPA routing, see [references/REFERENCE.md](references/REFERENCE.md).

## Pre-publish sanitization (agent guidelines)

Before publishing, verify content is safe for public consumption:

1. **No secrets** — API keys, tokens, passwords, private keys, connection strings
2. **No PII** — real names, personal emails, phone numbers, addresses
3. **No internal references** — server hostnames, internal URLs, project codenames
4. **No absolute paths** — sanitize `/workspace/group` → `./`

## Differences from upstream

| Change | Upstream | NanoClaw fork |
|--------|----------|---------------|
| `file` command | Required (MIME detection fallback) | Not required (unknown types blocked) |
| `jq` | System dependency | Bundled in `bin/jq` |
| Dangerous extensions | Not checked | Always blocked |
| Suspicious extensions | Not checked | Blocked unless `--allow-suspicious` |
| Secret scanning | Not present | Pre-upload content scanning |
| Credential permissions | Not checked | Warns if world-readable |
| `.herenow/` in publish target | Included | Skipped |
| Client attribution | `here-now-publish-sh` | `nanoclaw/publish-sh` |

## Upstream

Based on [heredotnow/skill](https://github.com/heredotnow/skill/tree/main/here-now) v1.11.0.
