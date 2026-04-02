#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://here.now"
CREDENTIALS_FILE="$HOME/.herenow/credentials"
API_KEY="${HERENOW_API_KEY:-}"
API_KEY_SOURCE="none"
if [[ -n "${HERENOW_API_KEY:-}" ]]; then
  API_KEY_SOURCE="env"
fi
ALLOW_NON_HERENOW_BASE_URL=0
ALLOW_SUSPICIOUS=0
ALLOW_UNKNOWN=0
SLUG=""
CLAIM_TOKEN=""
TITLE=""
DESCRIPTION=""
TTL=""
CLIENT=""
TARGET=""

usage() {
  cat <<'USAGE'
Usage: publish.sh <file-or-dir> [options]

Options:
  --api-key <key>         API key (or set $HERENOW_API_KEY)
  --slug <slug>           Update existing publish
  --claim-token <token>   Claim token for anonymous updates
  --title <text>          Viewer title
  --description <text>    Viewer description
  --ttl <seconds>         Expiry (authenticated only)
  --client <name>         Agent name for attribution (e.g. cursor, claude-code)
  --base-url <url>        API base (default: https://here.now)
  --allow-nonherenow-base-url
                         Allow auth requests to non-default API base URL
  --allow-suspicious      Allow files with suspicious extensions (warn only)
  --allow-unknown         Allow files with unknown extensions (application/octet-stream)

Security:
  Dangerous extensions (.env, .pem, .key, etc.) are always blocked.
  Suspicious extensions (.bak, .tmp, no extension) warn unless --allow-suspicious.
  Unknown extensions default to application/octet-stream unless --allow-unknown.
  Pre-upload secret scanning checks for leaked credentials in file content.
USAGE
  exit 1
}

die() { echo "error: $1" >&2; exit 1; }

warn() { echo "warning: $1" >&2; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUNDLED_JQ="${SKILL_DIR}/bin/jq"

if [[ -x "$BUNDLED_JQ" ]]; then
  JQ_BIN="$BUNDLED_JQ"
elif command -v jq >/dev/null 2>&1; then
  JQ_BIN="$(command -v jq)"
else
  die "requires jq (bundled binary not found and jq not on PATH)"
fi

file command is optional — unknown types get application/octet-stream
# instead of being detected via libmagic
for cmd in curl; do
  command -v "$cmd" >/dev/null 2>&1 || die "requires $cmd"
done

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-key)      API_KEY="$2"; API_KEY_SOURCE="flag"; shift 2 ;;
    --slug)         SLUG="$2"; shift 2 ;;
    --claim-token)  CLAIM_TOKEN="$2"; shift 2 ;;
    --title)        TITLE="$2"; shift 2 ;;
    --description)  DESCRIPTION="$2"; shift 2 ;;
    --ttl)          TTL="$2"; shift 2 ;;
    --client)       CLIENT="$2"; shift 2 ;;
    --base-url)     BASE_URL="$2"; shift 2 ;;
    --allow-nonherenow-base-url) ALLOW_NON_HERENOW_BASE_URL=1; shift ;;
    --allow-suspicious) ALLOW_SUSPICIOUS=1; shift ;;
    --allow-unknown) ALLOW_UNKNOWN=1; shift ;;
    --help|-h)      usage ;;
    -*)             die "unknown option: $1" ;;
    *)              [[ -z "$TARGET" ]] && TARGET="$1" || die "unexpected argument: $1"; shift ;;
  esac
done

[[ -n "$TARGET" ]] || usage
[[ -e "$TARGET" ]] || die "path does not exist: $TARGET"

Warn if credentials file is world-readable
if [[ -f "$CREDENTIALS_FILE" ]]; then
  perms=$(stat -c '%a' "$CREDENTIALS_FILE" 2>/dev/null || echo "unknown")
  if [[ "$perms" != "unknown" && "${perms: -1}" -ge 4 ]]; then
    warn "credentials file $CREDENTIALS_FILE is world-readable (permissions: $perms). Consider: chmod 600 $CREDENTIALS_FILE"
  fi
fi

# Load API key from credentials file if not provided via flag or env
if [[ -z "$API_KEY" && -f "$CREDENTIALS_FILE" ]]; then
  API_KEY=$(cat "$CREDENTIALS_FILE" | tr -d '[:space:]')
  [[ -n "$API_KEY" ]] && API_KEY_SOURCE="credentials"
fi

BASE_URL="${BASE_URL%/}"
STATE_DIR=".herenow"
STATE_FILE="$STATE_DIR/state.json"

# Safety guard: avoid accidentally sending bearer auth to arbitrary endpoints.
if [[ -n "$API_KEY" && "$BASE_URL" != "https://here.now" && "$ALLOW_NON_HERENOW_BASE_URL" -ne 1 ]]; then
  die "refusing to send API key to non-default base URL; pass --allow-nonherenow-base-url to override"
fi

# Auto-load claim token from state file for anonymous updates
if [[ -n "$SLUG" && -z "$CLAIM_TOKEN" && -z "$API_KEY" && -f "$STATE_FILE" ]]; then
  CLAIM_TOKEN=$("$JQ_BIN" -r --arg s "$SLUG" '.publishes[$s].claimToken // empty' "$STATE_FILE" 2>/dev/null || true)
fi

compute_sha256() {
  local f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | cut -d' ' -f1
  else
    shasum -a 256 "$f" | cut -d' ' -f1
  fi
}

Dangerous extensions — always blocked
is_dangerous_extension() {
  local ext="$1"
  local name="$2"
  # Block by extension
  case "$ext" in
    env|pem|key|p12|pfx|jks|keystore|gpg|asc|ppk|ssh|rsa|ec|der|crt|cer|p7b|p7c)
      return 0 ;;
    *)
      # Block by filename pattern
      case "$name" in
        .env*|*.secret*|*.credential*|id_rsa*|id_ed25519*|id_ecdsa*|*.pem|*.key|known_hosts|.htpasswd|.netrc)
          return 0 ;;
        *)
          return 1 ;;
      esac ;;
  esac
}

Suspicious extensions — warn unless --allow-suspicious
is_suspicious_extension() {
  local ext="$1"
  local name="$2"
  case "$ext" in
    bak|old|tmp|temp|cache|log|swp|swo|orig|save|dist|map)
      return 0 ;;
    *)
      # No extension at all (filename has no dot) is suspicious
      if [[ "$name" != *.* ]]; then
        return 0
      fi
      return 1 ;;
  esac
}

# Known web-safe extensions (from upstream mapping + common additions)
is_known_extension() {
  local ext="$1"
  case "$ext" in
    html|htm|css|js|mjs|json|md|txt|xml|svg|png|jpg|jpeg|gif|webp|pdf|mp4|mov|mp3|wav|woff2|woff|ttf|ico|wasm|webmanifest|map|eot|otf|avif|tiff|tif|bmp|ico|cur|svgz)
      return 0 ;;
    *)
      return 1 ;;
  esac
}

guess_content_type() {
  local f="$1"
  case "${f##*.}" in
    html|htm) echo "text/html; charset=utf-8" ;;
    css)      echo "text/css; charset=utf-8" ;;
    js|mjs)   echo "text/javascript; charset=utf-8" ;;
    json)     echo "application/json; charset=utf-8" ;;
    md|txt)   echo "text/plain; charset=utf-8" ;;
    svg)      echo "image/svg+xml" ;;
    png)      echo "image/png" ;;
    jpg|jpeg) echo "image/jpeg" ;;
    gif)      echo "image/gif" ;;
    webp)     echo "image/webp" ;;
    pdf)      echo "application/pdf" ;;
    mp4)      echo "video/mp4" ;;
    mov)      echo "video/quicktime" ;;
    mp3)      echo "audio/mpeg" ;;
    wav)      echo "audio/wav" ;;
    xml)      echo "application/xml" ;;
    woff2)    echo "font/woff2" ;;
    woff)     echo "font/woff" ;;
    ttf)      echo "font/ttf" ;;
    ico)      echo "image/x-icon" ;;
    wasm)     echo "application/wasm" ;;
    webmanifest) echo "application/manifest+json" ;;
    map)      echo "application/json" ;;
    eot)      echo "application/vnd.ms-fontobject" ;;
    otf)      echo "font/otf" ;;
    avif)     echo "image/avif" ;;
    tiff|tif) echo "image/tiff" ;;
    bmp)      echo "image/bmp" ;;
    *)
      No file command dependency — unknown types get generic MIME
      echo "application/octet-stream" ;;
  esac
}

Pre-upload secret scanning — check file content for leaked credentials
scan_for_secrets() {
  local f="$1"
  local rel="$2"
  local issues=0

  # Skip binary files (images, fonts, media) — not worth scanning
  case "${f##*.}" in
    png|jpg|jpeg|gif|webp|svg|avif|tiff|tif|bmp|ico|cur|mp4|mov|mp3|wav|woff2|woff|ttf|eot|otf|wasm)
      return 0 ;;
  esac

  # Only scan text files (reasonable size limit)
  local fsize
  fsize=$(wc -c < "$f" | tr -d ' ')
  if [[ "$fsize" -gt 1048576 ]]; then
    return 0
  fi

  # Check for common secret patterns
  local patterns=(
    'sk-[a-zA-Z0-9]{20,}'                    # OpenAI-style API keys
    'ghp_[a-zA-Z0-9]{30,}'                    # GitHub PATs
    'gho_[a-zA-Z0-9]{30,}'                    # GitHub OAuth
    'ghu_[a-zA-Z0-9]{30,}'                    # GitHub user tokens
    'ghs_[a-zA-Z0-9]{30,}'                    # GitHub App tokens
    'xox[bsp]-[a-zA-Z0-9-]+'                  # Slack tokens
    'AKIA[0-9A-Z]{16}'                        # AWS access keys
    '-----BEGIN.*PRIVATE KEY-----'             # Private keys
    '-----BEGIN.*RSA.*PRIVATE KEY-----'        # RSA private keys
    'AIza[a-zA-Z0-9_-]{35}'                   # Google API keys
    'hooks\.slack\.com/services/T[A-Z0-9]{8,}' # Slack webhooks
  )

  for pattern in "${patterns[@]}"; do
    if grep -qE "$pattern" "$f" 2>/dev/null; then
      warn "SECRET DETECTED in $rel — matches pattern: $pattern"
      issues=$((issues + 1))
    fi
  done

  return $issues
}

# Build file manifest as JSON array
FILES_JSON="[]"
BLOCKED_FILES=()
SUSPICIOUS_FILES=()
UNKNOWN_FILES=()
SECRET_FILES=()

if [[ -f "$TARGET" ]]; then
  bn=$(basename "$TARGET")
  ext="${bn##*.}"
  filename="${bn%.*}"

  if is_dangerous_extension "$ext" "$bn"; then
    die "BLOCKED: $bn has a dangerous extension ($ext). This file type should never be published to a public site."
  fi

  if is_suspicious_extension "$ext" "$bn"; then
    if [[ "$ALLOW_SUSPICIOUS" -ne 1 ]]; then
      die "BLOCKED: $bn has a suspicious extension ($ext). Pass --allow-suspicious to include it."
    fi
    warn "including suspicious file: $bn"
  fi

  if ! is_known_extension "$ext" && ! is_suspicious_extension "$ext" "$bn"; then
    if [[ "$ALLOW_UNKNOWN" -ne 1 ]]; then
      die "BLOCKED: $bn has an unknown extension ($ext). Pass --allow-unknown to include it (will be published as application/octet-stream)."
    fi
    warn "including unknown-type file: $bn (published as application/octet-stream)"
  fi

  if ! scan_for_secrets "$TARGET" "$bn"; then
    SECRET_FILES+=("$bn")
  fi

  sz=$(wc -c < "$TARGET" | tr -d ' ')
  ct=$(guess_content_type "$TARGET")
  h=$(compute_sha256 "$TARGET")
  FILES_JSON=$("$JQ_BIN" -n --arg p "$bn" --argjson s "$sz" --arg c "$ct" --arg h "$h" \
    '[{"path":$p,"size":$s,"contentType":$c,"hash":$h}]')
  FILE_MAP=$("$JQ_BIN" -n --arg p "$bn" --arg a "$(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")" \
    '{($p):$a}')
elif [[ -d "$TARGET" ]]; then
  FILE_MAP="{}"
  while IFS= read -r -d '' f; do
    rel="${f#$TARGET/}"
    [[ "$rel" == ".DS_Store" ]] && continue
    [[ "$(basename "$rel")" == ".DS_Store" ]] && continue
    # Skip .herenow state directory
    [[ "$rel" == ".herenow/"* ]] && continue
    [[ "$rel" == ".herenow" ]] && continue

    bn=$(basename "$f")
    ext="${bn##*.}"
    filename="${bn%.*}"

    Block dangerous extensions
    if is_dangerous_extension "$ext" "$bn"; then
      BLOCKED_FILES+=("$rel")
      warn "BLOCKED: $rel — dangerous file type ($ext)"
      continue
    fi

    Warn on suspicious extensions
    if is_suspicious_extension "$ext" "$bn"; then
      if [[ "$ALLOW_SUSPICIOUS" -ne 1 ]]; then
        BLOCKED_FILES+=("$rel")
        warn "BLOCKED: $rel — suspicious file type ($ext). Pass --allow-suspicious to include."
        continue
      fi
      SUSPICIOUS_FILES+=("$rel")
      warn "including suspicious file: $rel"
    fi

    Warn on truly unknown extensions
    if ! is_known_extension "$ext" && ! is_suspicious_extension "$ext" "$bn"; then
      if [[ "$ALLOW_UNKNOWN" -ne 1 ]]; then
        BLOCKED_FILES+=("$rel")
        warn "BLOCKED: $rel — unknown file type ($ext). Pass --allow-unknown to include."
        continue
      fi
      UNKNOWN_FILES+=("$rel")
      warn "including unknown-type file: $rel (published as application/octet-stream)"
    fi

    Pre-upload secret scanning
    if ! scan_for_secrets "$f" "$rel"; then
      SECRET_FILES+=("$rel")
    fi

    sz=$(wc -c < "$f" | tr -d ' ')
    ct=$(guess_content_type "$f")
    h=$(compute_sha256 "$f")
    abs=$(cd "$(dirname "$f")" && pwd)/$(basename "$f")
    FILES_JSON=$(echo "$FILES_JSON" | "$JQ_BIN" --arg p "$rel" --argjson s "$sz" --arg c "$ct" --arg h "$h" \
      '. + [{"path":$p,"size":$s,"contentType":$c,"hash":$h}]')
    FILE_MAP=$(echo "$FILE_MAP" | "$JQ_BIN" --arg p "$rel" --arg a "$abs" '. + {($p):$a}')
  done < <(find "$TARGET" -type f -print0 | sort -z)
else
  die "not a file or directory: $TARGET"
fi

# Report blocked files
if [[ ${#BLOCKED_FILES[@]} -gt 0 ]]; then
  echo "" >&2
  echo "=== Publish Blocked ===" >&2
  echo "${#BLOCKED_FILES[@]} file(s) blocked from upload:" >&2
  for bf in "${BLOCKED_FILES[@]}"; do
    echo "  - $bf" >&2
  done
  echo "" >&2
  die "publish aborted — dangerous/suspicious files detected. Fix or use --allow-suspicious / --allow-unknown"
fi

# Report secret findings
if [[ ${#SECRET_FILES[@]} -gt 0 ]]; then
  echo "" >&2
  echo "=== WARNING: Secrets Detected ===" >&2
  echo "The following files may contain credentials:" >&2
  for sf in "${SECRET_FILES[@]}"; do
    echo "  - $sf" >&2
  done
  echo "" >&2
  die "publish aborted — potential secrets detected. Remove sensitive content before publishing."
fi

file_count=$(echo "$FILES_JSON" | "$JQ_BIN" 'length')
[[ "$file_count" -gt 0 ]] || die "no files found"

# Build request body
BODY=$(echo "$FILES_JSON" | "$JQ_BIN" '{files: .}')

if [[ -n "$TTL" ]]; then
  BODY=$(echo "$BODY" | "$JQ_BIN" --argjson t "$TTL" '.ttlSeconds = $t')
fi

if [[ -n "$TITLE" || -n "$DESCRIPTION" ]]; then
  viewer="{}"
  [[ -n "$TITLE" ]] && viewer=$(echo "$viewer" | "$JQ_BIN" --arg t "$TITLE" '.title = $t')
  [[ -n "$DESCRIPTION" ]] && viewer=$(echo "$viewer" | "$JQ_BIN" --arg d "$DESCRIPTION" '.description = $d')
  BODY=$(echo "$BODY" | "$JQ_BIN" --argjson v "$viewer" '.viewer = $v')
fi

if [[ -n "$CLAIM_TOKEN" && -n "$SLUG" && -z "$API_KEY" ]]; then
  BODY=$(echo "$BODY" | "$JQ_BIN" --arg ct "$CLAIM_TOKEN" '.claimToken = $ct')
fi

# Determine endpoint and method
if [[ -n "$SLUG" ]]; then
  URL="$BASE_URL/api/v1/publish/$SLUG"
  METHOD="PUT"
else
  URL="$BASE_URL/api/v1/publish"
  METHOD="POST"
fi

# Build auth header
AUTH_ARGS=()
if [[ -n "$API_KEY" ]]; then
  AUTH_ARGS=(-H "authorization: Bearer $API_KEY")
fi

AUTH_MODE="anonymous"
if [[ -n "$API_KEY" ]]; then
  AUTH_MODE="authenticated"
fi

CLIENT_HEADER_VALUE="nanoclaw/publish-sh"
if [[ -n "$CLIENT" ]]; then
  normalized_client=$(echo "$CLIENT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9._-' '-')
  normalized_client="${normalized_client#-}"
  normalized_client="${normalized_client%-}"
  if [[ -n "$normalized_client" ]]; then
    CLIENT_HEADER_VALUE="${normalized_client}/publish-sh"
  fi
fi
CLIENT_ARGS=(-H "x-herenow-client: $CLIENT_HEADER_VALUE")

# Step 1: Create/update publish
echo "creating publish ($file_count files)..." >&2
RESPONSE=$(curl -sS -X "$METHOD" "$URL" \
  "${AUTH_ARGS[@]+"${AUTH_ARGS[@]}"}" \
  "${CLIENT_ARGS[@]+"${CLIENT_ARGS[@]}"}" \
  -H "content-type: application/json" \
  -d "$BODY")

# Check for errors
if echo "$RESPONSE" | "$JQ_BIN" -e '.error' >/dev/null 2>&1; then
  err=$(echo "$RESPONSE" | "$JQ_BIN" -r '.error')
  details=$(echo "$RESPONSE" | "$JQ_BIN" -r '.details // empty')
  die "$err${details:+ ($details)}"
fi

OUT_SLUG=$(echo "$RESPONSE" | "$JQ_BIN" -r '.slug')
VERSION_ID=$(echo "$RESPONSE" | "$JQ_BIN" -r '.upload.versionId')
FINALIZE_URL=$(echo "$RESPONSE" | "$JQ_BIN" -r '.upload.finalizeUrl')
SITE_URL=$(echo "$RESPONSE" | "$JQ_BIN" -r '.siteUrl')
UPLOAD_COUNT=$(echo "$RESPONSE" | "$JQ_BIN" '.upload.uploads | length')
SKIPPED_COUNT=$(echo "$RESPONSE" | "$JQ_BIN" '.upload.skipped // [] | length')

[[ "$OUT_SLUG" != "null" ]] || die "unexpected response: $RESPONSE"

# Step 2: Upload files (skipped files are unchanged from previous version)
if [[ "$SKIPPED_COUNT" -gt 0 ]]; then
  echo "uploading $UPLOAD_COUNT files ($SKIPPED_COUNT unchanged, skipped)..." >&2
else
  echo "uploading $UPLOAD_COUNT files..." >&2
fi
upload_errors=0

for i in $(seq 0 $((UPLOAD_COUNT - 1))); do
  upload_path=$(echo "$RESPONSE" | "$JQ_BIN" -r ".upload.uploads[$i].path")
  upload_url=$(echo "$RESPONSE" | "$JQ_BIN" -r ".upload.uploads[$i].url")
  upload_ct=$(echo "$RESPONSE" | "$JQ_BIN" -r ".upload.uploads[$i].headers[\"Content-Type\"] // empty")

  if [[ -f "$TARGET" && ! -d "$TARGET" ]]; then
    local_file="$TARGET"
  else
    local_file=$(echo "$FILE_MAP" | "$JQ_BIN" -r --arg p "$upload_path" '.[$p]')
  fi

  if [[ ! -f "$local_file" ]]; then
    echo "warning: missing local file for $upload_path" >&2
    upload_errors=$((upload_errors + 1))
    continue
  fi

  ct_args=()
  [[ -n "$upload_ct" ]] && ct_args=(-H "Content-Type: $upload_ct")

  http_code=$(curl -sS -o /dev/null -w "%{http_code}" -X PUT "$upload_url" \
    "${ct_args[@]+"${ct_args[@]}"}" \
    --data-binary "@$local_file")

  if [[ "$http_code" -lt 200 || "$http_code" -ge 300 ]]; then
    echo "warning: upload failed for $upload_path (HTTP $http_code)" >&2
    upload_errors=$((upload_errors + 1))
  fi
done &
wait

[[ "$upload_errors" -eq 0 ]] || die "$upload_errors file(s) failed to upload"

# Step 3: Finalize
echo "finalizing..." >&2
FIN_RESPONSE=$(curl -sS -X POST "$FINALIZE_URL" \
  "${AUTH_ARGS[@]+"${AUTH_ARGS[@]}"}" \
  "${CLIENT_ARGS[@]+"${CLIENT_ARGS[@]}"}" \
  -H "content-type: application/json" \
  -d "{\"versionId\":\"$VERSION_ID\"}")

if echo "$FIN_RESPONSE" | "$JQ_BIN" -e '.error' >/dev/null 2>&1; then
  err=$(echo "$FIN_RESPONSE" | "$JQ_BIN" -r '.error')
  die "finalize failed: $err"
fi

# Save state
mkdir -p "$STATE_DIR"
if [[ -f "$STATE_FILE" ]]; then
  STATE=$(cat "$STATE_FILE")
else
  STATE='{"publishes":{}}'
fi

entry=$("$JQ_BIN" -n --arg s "$SITE_URL" '{siteUrl: $s}')

RESPONSE_CLAIM_TOKEN=$(echo "$RESPONSE" | "$JQ_BIN" -r '.claimToken // empty')
RESPONSE_CLAIM_URL=$(echo "$RESPONSE" | "$JQ_BIN" -r '.claimUrl // empty')
RESPONSE_EXPIRES=$(echo "$RESPONSE" | "$JQ_BIN" -r '.expiresAt // empty')

[[ -n "$RESPONSE_CLAIM_TOKEN" ]] && entry=$(echo "$entry" | "$JQ_BIN" --arg v "$RESPONSE_CLAIM_TOKEN" '.claimToken = $v')
[[ -n "$RESPONSE_CLAIM_URL" ]] && entry=$(echo "$entry" | "$JQ_BIN" --arg v "$RESPONSE_CLAIM_URL" '.claimUrl = $v')
[[ -n "$RESPONSE_EXPIRES" ]] && entry=$(echo "$entry" | "$JQ_BIN" --arg v "$RESPONSE_EXPIRES" '.expiresAt = $v')

STATE=$(echo "$STATE" | "$JQ_BIN" --arg slug "$OUT_SLUG" --argjson e "$entry" '.publishes[$slug] = $e')
echo "$STATE" | "$JQ_BIN" '.' > "$STATE_FILE"

# Output
echo "$SITE_URL"

PERSISTENCE="permanent"
if [[ "$AUTH_MODE" == "anonymous" ]]; then
  PERSISTENCE="expires_24h"
elif [[ -n "$RESPONSE_EXPIRES" ]]; then
  PERSISTENCE="expires_at"
fi

SAFE_CLAIM_URL=""
if [[ -n "$RESPONSE_CLAIM_URL" && "$RESPONSE_CLAIM_URL" == https://* ]]; then
  SAFE_CLAIM_URL="$RESPONSE_CLAIM_URL"
fi

echo "" >&2
echo "publish_result.site_url=$SITE_URL" >&2
echo "publish_result.auth_mode=$AUTH_MODE" >&2
echo "publish_result.api_key_source=$API_KEY_SOURCE" >&2
echo "publish_result.persistence=$PERSISTENCE" >&2
echo "publish_result.expires_at=$RESPONSE_EXPIRES" >&2
echo "publish_result.claim_url=$SAFE_CLAIM_URL" >&2

if [[ "$AUTH_MODE" == "authenticated" ]]; then
  echo "authenticated publish (permanent, saved to your account)" >&2
else
  echo "anonymous publish (expires in 24h)" >&2
  if [[ -n "$SAFE_CLAIM_URL" ]]; then
    echo "claim URL: $SAFE_CLAIM_URL" >&2
  fi
  if [[ -n "$RESPONSE_CLAIM_TOKEN" ]]; then
    echo "claim token saved to $STATE_FILE" >&2
  fi
fi
