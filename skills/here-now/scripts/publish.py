#!/usr/bin/env python3
"""
here.now publish script — Python implementation (zero dependencies).

Reimplements publish.sh logic using only Python stdlib.
Works in any environment with Python 3.6+.

Security layers ported from NanoClaw-hardened publish.sh:
  1. Dangerous extension blocking
  2. Suspicious extension warnings
  3. Unknown extension warnings
  4. Pre-upload secret scanning
  5. Credential file permission checks
"""

import argparse
import hashlib
import json
import mimetypes
import os
import re
import stat
import sys
import urllib.request
import urllib.error
from pathlib import Path

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://here.now"
CREDENTIALS_FILE = os.path.expanduser("~/.herenow/credentials")
STATE_DIR = ".herenow"
STATE_FILE = os.path.join(STATE_DIR, "state.json")
USER_AGENT = "nanoclaw/publish-py"

DANGEROUS_EXTENSIONS = frozenset({
    "env", "pem", "key", "p12", "pfx", "jks", "keystore",
    "gpg", "asc", "ppk", "ssh", "rsa", "ec", "der",
    "crt", "cer", "p7b", "p7c",
})

DANGEROUS_PATTERNS = [
    re.compile(r"^\.env"),
    re.compile(r"\.secret", re.IGNORECASE),
    re.compile(r"\.credential", re.IGNORECASE),
    re.compile(r"^id_rsa"),
    re.compile(r"^id_ed25519"),
    re.compile(r"^id_ecdsa"),
    re.compile(r"\.pem$", re.IGNORECASE),
    re.compile(r"\.key$"),
    re.compile(r"^known_hosts"),
    re.compile(r"^\.htpasswd"),
    re.compile(r"^\.netrc"),
]

SUSPICIOUS_EXTENSIONS = frozenset({
    "bak", "old", "tmp", "temp", "cache", "log",
    "swp", "swo", "orig", "save", "dist", "map",
})

KNOWN_EXTENSIONS = frozenset({
    "html", "htm", "css", "js", "mjs", "json", "md", "txt", "xml",
    "svg", "png", "jpg", "jpeg", "gif", "webp", "pdf", "mp4", "mov",
    "mp3", "wav", "woff2", "woff", "ttf", "ico", "wasm", "webmanifest",
    "eot", "otf", "avif", "tiff", "tif", "bmp", "cur", "svgz",
})

BINARY_EXTENSIONS = frozenset({
    "png", "jpg", "jpeg", "gif", "webp", "svg", "avif", "tiff", "tif",
    "bmp", "ico", "cur", "mp4", "mov", "mp3", "wav", "woff2", "woff",
    "ttf", "eot", "otf", "wasm",
})

SECRET_PATTERNS = [
    ("OpenAI API key",         re.compile(r"sk-[a-zA-Z0-9]{20,}")),
    ("GitHub PAT",             re.compile(r"ghp_[a-zA-Z0-9]{30,}")),
    ("GitHub OAuth",           re.compile(r"gho_[a-zA-Z0-9]{30,}")),
    ("GitHub user token",      re.compile(r"ghu_[a-zA-Z0-9]{30,}")),
    ("GitHub App token",       re.compile(r"ghs_[a-zA-Z0-9]{30,}")),
    ("Slack token",            re.compile(r"xox[bsp]-[a-zA-Z0-9\-]+")),
    ("AWS access key",         re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private key",            re.compile(r"-----BEGIN.*PRIVATE KEY-----")),
    ("RSA private key",        re.compile(r"-----BEGIN.*RSA.*PRIVATE KEY-----")),
    ("Google API key",         re.compile(r"AIza[a-zA-Z0-9_\-]{35}")),
    ("Slack webhook",          re.compile(r"hooks\.slack\.com/services/T[A-Z0-9]{8,}")),
]

CONTENT_TYPE_MAP = {
    "html": "text/html; charset=utf-8",
    "htm":  "text/html; charset=utf-8",
    "css":  "text/css; charset=utf-8",
    "js":   "text/javascript; charset=utf-8",
    "mjs":  "text/javascript; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "md":   "text/plain; charset=utf-8",
    "txt":  "text/plain; charset=utf-8",
    "svg":  "image/svg+xml",
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "gif":  "image/gif",
    "webp": "image/webp",
    "pdf":  "application/pdf",
    "mp4":  "video/mp4",
    "mov":  "video/quicktime",
    "mp3":  "audio/mpeg",
    "wav":  "audio/wav",
    "xml":  "application/xml",
    "woff2": "font/woff2",
    "woff":  "font/woff",
    "ttf":  "font/ttf",
    "ico":  "image/x-icon",
    "wasm": "application/wasm",
    "webmanifest": "application/manifest+json",
    "map":  "application/json",
    "eot":  "application/vnd.ms-fontobject",
    "otf":  "font/otf",
    "avif": "image/avif",
    "tiff": "image/tiff",
    "tif":  "image/tiff",
    "bmp":  "image/bmp",
    "cur":  "image/x-icon",
    "svgz": "image/svg+xml",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)

def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def guess_content_type(filepath):
    ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
    return CONTENT_TYPE_MAP.get(ext, "application/octet-stream")


def get_extension(filename):
    """Return lowercase extension without dot, or empty string."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


# ---------------------------------------------------------------------------
# Security layers
# ---------------------------------------------------------------------------

def is_dangerous(filename):
    ext = get_extension(filename)
    if ext in DANGEROUS_EXTENSIONS:
        return True
    for pat in DANGEROUS_PATTERNS:
        if pat.search(filename):
            return True
    return False


def is_suspicious(filename):
    ext = get_extension(filename)
    if ext in SUSPICIOUS_EXTENSIONS:
        return True
    # No extension at all is suspicious
    if "." not in filename:
        return True
    return False


def is_known(filename):
    ext = get_extension(filename)
    return ext in KNOWN_EXTENSIONS


def scan_for_secrets(filepath, rel_path):
    """Scan text files for leaked credentials. Returns list of (pattern_name, pattern_str)."""
    ext = get_extension(filepath)
    # Skip binary files
    if ext in BINARY_EXTENSIONS:
        return []
    # Skip large files (>1MB)
    try:
        fsize = os.path.getsize(filepath)
    except OSError:
        return []
    if fsize > 1_048_576:
        return []

    try:
        with open(filepath, "r", errors="ignore") as f:
            content = f.read()
    except (OSError, IOError):
        return []

    findings = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            findings.append((name, pattern.pattern))
    return findings


def check_credentials_permissions():
    """Warn if credentials file is world-readable."""
    if not os.path.isfile(CREDENTIALS_FILE):
        return
    try:
        st = os.stat(CREDENTIALS_FILE)
        mode = stat.S_IMODE(st.st_mode)
        if mode & stat.S_IROTH:
            warn(f"credentials file {CREDENTIALS_FILE} is world-readable "
                 f"(permissions: {oct(mode)}). Consider: chmod 600 {CREDENTIALS_FILE}")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# File manifest
# ---------------------------------------------------------------------------

def build_manifest(target, allow_suspicious, allow_unknown):
    """
    Walk target (file or dir) and build upload manifest.
    Returns (files_list, file_map, blocked, secrets_found).

    files_list: [{"path": ..., "size": ..., "contentType": ..., "hash": ...}, ...]
    file_map:   {rel_path: abs_path, ...}
    blocked:    [rel_path, ...]
    secrets:    [(rel_path, [(pattern_name, pattern_str), ...]), ...]
    """
    files_list = []
    file_map = {}
    blocked = []
    secrets = []

    def process_file(abs_path, rel_path):
        basename = os.path.basename(rel_path)

        # Skip .DS_Store
        if basename == ".DS_Store":
            return

        # Layer 1: Dangerous extensions
        if is_dangerous(basename):
            warn(f"BLOCKED: {rel_path} — dangerous file type ({get_extension(basename)})")
            blocked.append(rel_path)
            return

        # Layer 2: Suspicious extensions
        if is_suspicious(basename):
            if not allow_suspicious:
                warn(f"BLOCKED: {rel_path} — suspicious file type ({get_extension(basename)}). "
                     f"Pass --allow-suspicious to include.")
                blocked.append(rel_path)
                return
            warn(f"including suspicious file: {rel_path}")

        # Layer 3: Unknown extensions
        ext = get_extension(basename)
        if ext and ext not in KNOWN_EXTENSIONS and not is_suspicious(basename):
            if not allow_unknown:
                warn(f"BLOCKED: {rel_path} — unknown file type ({ext}). "
                     f"Pass --allow-unknown to include (published as application/octet-stream).")
                blocked.append(rel_path)
                return
            warn(f"including unknown-type file: {rel_path} (published as application/octet-stream)")

        # Layer 4: Secret scanning
        findings = scan_for_secrets(abs_path, rel_path)
        if findings:
            secrets.append((rel_path, findings))

        # Build manifest entry
        size = os.path.getsize(abs_path)
        ct = guess_content_type(abs_path)
        sha = compute_sha256(abs_path)

        files_list.append({
            "path": rel_path,
            "size": size,
            "contentType": ct,
            "hash": sha,
        })
        file_map[rel_path] = abs_path

    target = os.path.abspath(target)

    if os.path.isfile(target):
        process_file(target, os.path.basename(target))
    elif os.path.isdir(target):
        for root, dirs, filenames in os.walk(target):
            # Skip .herenow state directory
            rel_root = os.path.relpath(root, target)
            if rel_root == STATE_DIR or rel_root.startswith(STATE_DIR + os.sep):
                dirs.clear()
                continue
            # Sort for deterministic output
            for fname in sorted(filenames):
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, target)
                process_file(abs_path, rel_path)
    else:
        die(f"not a file or directory: {target}")

    return files_list, file_map, blocked, secrets


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_request(url, method="GET", data=None, headers=None, timeout=30):
    """Make an HTTP request and return (status_code, response_body)."""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", USER_AGENT)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    if body is not None:
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8")
        except Exception:
            pass
        return e.code, body_text


def upload_file(url, filepath, content_type=None, timeout=60):
    """Upload a file to a presigned URL via PUT. Returns status code."""
    with open(filepath, "rb") as f:
        data = f.read()
    headers = {"User-Agent": USER_AGENT}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status
    except urllib.error.HTTPError as e:
        return e.code


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state():
    if os.path.isfile(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"publishes": {}}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="publish.py",
        description="Publish files/folders to here.now (Python implementation, zero dependencies)",
    )
    parser.add_argument("target", help="File or directory to publish")
    parser.add_argument("--api-key", dest="api_key", help="API key (or set $HERENOW_API_KEY)")
    parser.add_argument("--slug", help="Update existing publish")
    parser.add_argument("--claim-token", dest="claim_token", help="Claim token for anonymous updates")
    parser.add_argument("--title", help="Viewer title")
    parser.add_argument("--description", help="Viewer description")
    parser.add_argument("--ttl", type=int, help="Expiry in seconds (authenticated only)")
    parser.add_argument("--client", help="Agent name for attribution (e.g. hermes, claude-code)")
    parser.add_argument("--base-url", dest="base_url", default=BASE_URL, help=f"API base URL (default: {BASE_URL})")
    parser.add_argument("--allow-nonherenow-base-url", action="store_true", help="Allow auth to non-default base URL")
    parser.add_argument("--allow-suspicious", action="store_true", help="Include suspicious extension files")
    parser.add_argument("--allow-unknown", action="store_true", help="Include unknown extension files")
    parser.add_argument("--spa", action="store_true", help="Enable SPA routing (serve index.html for unknown paths)")
    parser.add_argument("--password", help="Password protect the site (authenticated only)")

    args = parser.parse_args()

    # --- Load API key ---
    api_key = args.api_key or os.environ.get("HERENOW_API_KEY", "")
    api_key_source = "***"
    if args.api_key:
        api_key_source = "***"
    elif os.environ.get("HERENOW_API_KEY"):
        api_key_source = "***"

    if not api_key and os.path.isfile(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                api_key = f.read().strip()
            if api_key:
                api_key_source = "***"
        except OSError:
            pass

    # --- Normalize base URL ---
    base_url = args.base_url.rstrip("/")

    # --- Safety guard ---
    if api_key and base_url != BASE_URL and not args.allow_nonherenow_base_url:
        die(f"refusing to send API key to non-default base URL; pass --allow-nonherenow-base-url to override")

    # --- Auto-load claim token from state ---
    claim_token = args.claim_token or ""
    if args.slug and not claim_token and not api_key:
        state = load_state()
        claim_token = state.get("publishes", {}).get(args.slug, {}).get("claimToken", "")

    # --- Credential permissions check ---
    check_credentials_permissions()

    # --- Validate target ---
    if not os.path.exists(args.target):
        die(f"path does not exist: {args.target}")

    # --- Build manifest ---
    files_list, file_map, blocked, secrets = build_manifest(
        args.target, args.allow_suspicious, args.allow_unknown
    )

    # Report blocked files
    if blocked:
        print("", file=sys.stderr)
        print("=== Publish Blocked ===", file=sys.stderr)
        print(f"{len(blocked)} file(s) blocked from upload:", file=sys.stderr)
        for bf in blocked:
            print(f"  - {bf}", file=sys.stderr)
        print("", file=sys.stderr)
        die("publish aborted — dangerous/suspicious files detected. Fix or use --allow-suspicious / --allow-unknown")

    # Report secret findings
    if secrets:
        print("", file=sys.stderr)
        print("=== WARNING: Secrets Detected ===", file=sys.stderr)
        print("The following files may contain credentials:", file=sys.stderr)
        for sf, findings in secrets:
            print(f"  - {sf}", file=sys.stderr)
            for name, pat in findings:
                print(f"    matches: {name} ({pat})", file=sys.stderr)
        print("", file=sys.stderr)
        die("publish aborted — potential secrets detected. Remove sensitive content before publishing.")

    if not files_list:
        die("no files found")

    # --- Build request body ---
    body = {"files": files_list}

    if args.ttl:
        body["ttlSeconds"] = args.ttl

    if args.title or args.description:
        viewer = {}
        if args.title:
            viewer["title"] = args.title
        if args.description:
            viewer["description"] = args.description
        body["viewer"] = viewer

    if args.spa:
        body["spa"] = True

    if claim_token and args.slug and not api_key:
        body["claimToken"] = claim_token

    # --- Determine endpoint and method ---
    if args.slug:
        url = f"{base_url}/api/v1/publish/{args.slug}"
        method = "PUT"
    else:
        url = f"{base_url}/api/v1/publish"
        method = "POST"

    # --- Auth headers ---
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # --- Client header ---
    if args.client:
        normalized = re.sub(r"[^a-z0-9._\-]", "-", args.client.lower()).strip("-")
        if normalized:
            headers["x-herenow-client"] = f"{normalized}/publish-py"
    else:
        headers["x-herenow-client"] = USER_AGENT

    # --- Step 1: Create/update publish ---
    print(f"creating publish ({len(files_list)} files)...", file=sys.stderr)
    status, response_text = api_request(url, method=method, data=body, headers=headers)

    try:
        response = json.loads(response_text)
    except json.JSONDecodeError:
        die(f"unexpected response (HTTP {status}): {response_text[:500]}")

    if "error" in response:
        details = response.get("details", "")
        die(f"{response['error']}{f' ({details})' if details else ''}")

    out_slug = response.get("slug")
    version_id = response.get("upload", {}).get("versionId")
    finalize_url = response.get("upload", {}).get("finalizeUrl")
    site_url = response.get("siteUrl")
    uploads = response.get("upload", {}).get("uploads", [])
    skipped = response.get("upload", {}).get("skipped", [])

    if not out_slug:
        die(f"unexpected response: {response_text[:500]}")

    upload_count = len(uploads)
    skipped_count = len(skipped)

    # --- Step 2: Upload files ---
    if skipped_count > 0:
        print(f"uploading {upload_count} files ({skipped_count} unchanged, skipped)...", file=sys.stderr)
    else:
        print(f"uploading {upload_count} files...", file=sys.stderr)

    upload_errors = 0
    for upload_info in uploads:
        upload_path = upload_info.get("path", "")
        upload_url = upload_info.get("url", "")
        upload_ct = upload_info.get("headers", {}).get("Content-Type", "")

        local_file = file_map.get(upload_path)
        if not local_file or not os.path.isfile(local_file):
            warn(f"missing local file for {upload_path}")
            upload_errors += 1
            continue

        http_code = upload_file(upload_url, local_file, content_type=upload_ct or None)
        if http_code < 200 or http_code >= 300:
            warn(f"upload failed for {upload_path} (HTTP {http_code})")
            upload_errors += 1

    if upload_errors:
        die(f"{upload_errors} file(s) failed to upload")

    # --- Step 3: Finalize ---
    print("finalizing...", file=sys.stderr)
    fin_status, fin_text = api_request(
        finalize_url, method="POST",
        data={"versionId": version_id},
        headers=headers,
    )

    try:
        fin_response = json.loads(fin_text)
    except json.JSONDecodeError:
        die(f"finalize failed: unexpected response (HTTP {fin_status}): {fin_text[:500]}")

    if "error" in fin_response:
        die(f"finalize failed: {fin_response['error']}")

    # --- Password protect (optional) ---
    if args.password:
        print("setting password...", file=sys.stderr)
        pw_headers = dict(headers)
        pw_headers["Authorization"] = f"Bearer {api_key}" if api_key else ""
        pw_status, pw_text = api_request(
            f"{base_url}/api/v1/publish/{out_slug}/metadata",
            method="PATCH",
            data={"password": args.password},
            headers=pw_headers,
        )
        try:
            pw_response = json.loads(pw_text)
        except json.JSONDecodeError:
            pass
        else:
            if "error" in pw_response:
                warn(f"password protection failed: {pw_response['error']}")

    # --- Save state ---
    state = load_state()
    entry = {"siteUrl": site_url}

    response_claim_token = response.get("claimToken", "")
    response_claim_url = response.get("claimUrl", "")
    response_expires = response.get("expiresAt", "")

    if response_claim_token:
        entry["claimToken"] = response_claim_token
    if response_claim_url:
        entry["claimUrl"] = response_claim_url
    if response_expires:
        entry["expiresAt"] = response_expires

    if "publishes" not in state:
        state["publishes"] = {}
    state["publishes"][out_slug] = entry
    save_state(state)

    # --- Output ---
    print(site_url)

    # Determine persistence
    if api_key:
        auth_mode = "authenticated"
        persistence = "permanent"
    else:
        auth_mode = "anonymous"
        persistence = "expires_24h"
    if response_expires:
        persistence = "expires_at"

    safe_claim_url = response_claim_url if response_claim_url.startswith("https://") else ""

    print("", file=sys.stderr)
    print(f"publish_result.site_url={site_url}", file=sys.stderr)
    print(f"publish_result.auth_mode={auth_mode}", file=sys.stderr)
    print(f"publish_result.api_key_source={api_key_source}", file=sys.stderr)
    print(f"publish_result.persistence={persistence}", file=sys.stderr)
    print(f"publish_result.expires_at={response_expires}", file=sys.stderr)
    print(f"publish_result.claim_url={safe_claim_url}", file=sys.stderr)

    if auth_mode == "authenticated":
        print("authenticated publish (permanent, saved to your account)", file=sys.stderr)
    else:
        print("anonymous publish (expires in 24h)", file=sys.stderr)
        if safe_claim_url:
            print(f"claim URL: {safe_claim_url}", file=sys.stderr)
        if response_claim_token:
            print(f"claim token saved to {STATE_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
