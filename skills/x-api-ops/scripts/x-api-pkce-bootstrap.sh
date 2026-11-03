#!/usr/bin/env bash
# OAuth 2.0 PKCE token bootstrap for the X API v2.
#
# Starts a local callback listener, generates the PKCE pair, opens the
# authorize URL, waits for the consent redirect, exchanges the code, and
# saves the token set. Battle-tested against three real failure modes:
#   - favicon.ico requests overwriting the captured callback (empty-query guard)
#   - authorization codes expiring before pickup (atomic write + fast exchange)
#   - CSRF (state parameter verified before the token exchange)
#
# Usage: x-api-pkce-bootstrap.sh [--port 3000] [--timeout 300] [--no-open]
# Env:
#   X_API_CONFIG_DIR   default ~/.config/x-api  (reads client-id, client-secret;
#                      writes token.json)
#   X_API_SCOPES       default "users.read list.read list.write offline.access"
#   X_API_CALLBACK_HOST default localhost
#   X_API_OPEN         set to 0 to only print the authorize URL
#
# Deps: curl, python3, lsof. Secrets are read from files and never printed.
set -euo pipefail

PORT=3000; TIMEOUT=300; OPEN=${X_API_OPEN:-1}
if [ "$OPEN" = "0" ]; then OPEN=0; else OPEN=1; fi
while [ $# -gt 0 ]; do
  case $1 in
    --port) PORT=$2; shift 2 ;;
    --timeout) TIMEOUT=$2; shift 2 ;;
    --no-open) OPEN=0; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

CONFIG_DIR=${X_API_CONFIG_DIR:-$HOME/.config/x-api}
SCOPES=${X_API_SCOPES:-"users.read list.read list.write offline.access"}
CALLBACK_HOST=${X_API_CALLBACK_HOST:-localhost}
CALLBACK_URI="http://${CALLBACK_HOST}:${PORT}/callback"

if [ ! -s "$CONFIG_DIR/client-id" ] || [ ! -s "$CONFIG_DIR/client-secret" ]; then
  echo "missing client-id/client-secret in $CONFIG_DIR" >&2
  exit 2
fi
CID=$(cat "$CONFIG_DIR/client-id")
CSEC=$(cat "$CONFIG_DIR/client-secret")

# free the port from stale listeners
lsof -ti ":$PORT" | xargs kill 2>/dev/null || true
sleep 1

CBFILE=$(mktemp)
rm -f "$CBFILE"

python3 - "$PORT" "$CBFILE" <<'PYEOF' &
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse, os, tempfile
port, cbfile = int(sys.argv[1]), sys.argv[2]
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        if not q:  # favicon and other noise never overwrite a real capture
            self.send_response(404); self.end_headers(); return
        fd, tmp = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f: f.write(q)
        os.replace(tmp, cbfile)
        self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.end_headers()
        self.wfile.write(b'Callback captured. You can close this tab.')
    def log_message(self, *a): pass
HTTPServer(('127.0.0.1', port), H).serve_forever()
PYEOF
LISTENER_PID=$!
sleep 1

python3 - "$PORT" <<'PYEOF'
import secrets, hashlib, base64, os, sys, tempfile
port = sys.argv[1]
d = tempfile.mkdtemp(prefix='x-api-pkce-')
v = secrets.token_urlsafe(48)
c = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b'=').decode()
s = secrets.token_urlsafe(16)
open(os.path.join(d, 'verifier'), 'w').write(v)
open(os.path.join(d, 'challenge'), 'w').write(c)
open(os.path.join(d, 'state'), 'w').write(s)
open(os.path.join(d, 'port'), 'w').write(port)
print(d)
PYEOF
PKCE_DIR=$(python3 - "$PORT" <<'PYEOF'
import os, sys, tempfile
# the PKCE writer used its own mkdtemp; find the newest one
cands = sorted((os.path.join(tempfile.gettempdir(), p) for p in os.listdir(tempfile.gettempdir())
                if p.startswith('x-api-pkce-')), key=os.path.getmtime)
print(cands[-1])
PYEOF
)
# the verifier is sensitive: remove it on every exit path, not just success
trap 'rm -rf "$PKCE_DIR" /tmp/x-api-code' EXIT

SCOPES_ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$SCOPES")
URL="https://x.com/i/oauth2/authorize?response_type=code&client_id=${CID}&redirect_uri=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${CALLBACK_URI}', safe=''))")&scope=${SCOPES_ENC}&state=$(cat "$PKCE_DIR/state")&code_challenge=$(cat "$PKCE_DIR/challenge")&code_challenge_method=S256"

echo "Open this URL and approve access (tick the trust checkbox first):"
echo "$URL"
if [ "$OPEN" = 1 ]; then
  open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null || true
fi

WAITED=0
while [ ! -s "$CBFILE" ] && [ "$WAITED" -lt "$TIMEOUT" ]; do
  sleep 3; WAITED=$((WAITED + 3))
done
[ -s "$CBFILE" ] || { echo "TIMEOUT: no callback after ${TIMEOUT}s" >&2; kill "$LISTENER_PID" 2>/dev/null || true; exit 1; }

python3 - "$CBFILE" "$PKCE_DIR/state" <<'PYEOF'
import urllib.parse, sys
q = dict(urllib.parse.parse_qsl(open(sys.argv[1]).read()))
expected = open(sys.argv[2]).read()
assert q.get('state') == expected, 'STATE MISMATCH (possible CSRF) - aborting'
assert 'code' in q, 'no authorization code in callback'
assert 'error' not in q, 'authorize error: ' + q.get('error_description', q['error'])
open('/tmp/x-api-code', 'w').write(q['code'])
print('state OK, code captured')
PYEOF

CODE=$(cat /tmp/x-api-code)
curl -s -X POST https://api.x.com/2/oauth2/token \
  -u "$CID:$CSEC" \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "code=$CODE" \
  --data-urlencode "redirect_uri=$CALLBACK_URI" \
  --data-urlencode "client_id=$CID" \
  --data-urlencode "code_verifier=$(cat "$PKCE_DIR/verifier")" \
  -o /tmp/x-api-token-response.json

python3 - "$CONFIG_DIR/token.json" <<'PYEOF'
import json, os, sys, time
d = json.load(open('/tmp/x-api-token-response.json'))
if 'access_token' not in d:
    print('EXCHANGE FAILED: ' + json.dumps(d)[:300], file=sys.stderr); sys.exit(1)
tok = {'access_token': d['access_token'], 'refresh_token': d.get('refresh_token'),
       'expires_in': d.get('expires_in'), 'scope': d.get('scope'),
       'obtained_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
p = sys.argv[1]
open(p, 'w').write(json.dumps(tok, indent=1)); os.chmod(p, 0o600)
print('TOKEN SAVED | expires_in: %s s | scope: %s | refresh_token: %s' %
      (d.get('expires_in'), d.get('scope'), bool(d.get('refresh_token'))))
PYEOF

kill "$LISTENER_PID" 2>/dev/null || true
rm -f "$CBFILE" /tmp/x-api-code /tmp/x-api-token-response.json
rm -rf "$PKCE_DIR"
