#!/usr/bin/env python3
"""uptime-kuma-ops — Kuma automation entry point.

Fleet-agnostic: no config = per-invocation flags; config = ~/.agents/uptime-kuma.json
(names secret sources; never contains secrets itself).
"""
import argparse, base64, json, os, secrets, sys, time, urllib.request, urllib.error

CONFIG_PATH = os.path.expanduser("~/.agents/uptime-kuma.json")
PINNED_DEP = "python-socketio==5.13.0"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH) as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        sys.exit(f"malformed JSON in {CONFIG_PATH}: {e}")
    except OSError as e:
        sys.exit(f"cannot read {CONFIG_PATH}: {e.strerror}")

def resolve(cfg, args):
    base = args.base_url or cfg.get("base_url")
    env_file = args.env_file or cfg.get("auth_env_file")
    env = {}
    if env_file:
        p = os.path.expanduser(env_file)
        if not os.path.isabs(p):
            p = os.path.join(os.path.expanduser("~"), p)
        if not os.path.exists(p):
            sys.exit(f"env file not found: {p}")
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    def ek(name, default):
        return args.__dict__.get(name) or env.get(cfg.get(default, "")) or cfg.get(default)
    user = args.username or env.get(cfg.get("username_key", ""), "")
    pw = args.password or env.get(cfg.get("password_key", ""), "")
    key = args.api_key or env.get(cfg.get("api_key_key", ""), "")
    if not base:
        sys.exit("no base_url: pass --base-url or create ~/.agents/uptime-kuma.json (see: kuma.py init --help)")
    return base.rstrip("/"), user, pw, key

def cmd_metrics(a, cfg):
    base, _, _, key = resolve(cfg, a)
    if not key:
        sys.exit("no API key: --api-key, or api_key_key in config")
    req = urllib.request.Request(base + "/metrics",
        headers={"Authorization": "Basic " + base64.b64encode((":" + key).encode()).decode()})
    try:
        body = urllib.request.urlopen(req, timeout=15).read().decode()
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach {base}/metrics: {e.reason} (check base_url / VPN)")
    if a.grep:
        body = "\n".join(l for l in body.splitlines() if a.grep in l)
    print(body)

def connect(base, user, pw):
    try:
        import socketio
    except ImportError:
        sys.exit(f"missing dependencies: pip install '{PINNED_DEP}' 'websocket-client>=0.58' (venv or --user)")
    sio = socketio.Client()
    state = {"ml": None}
    @sio.on("monitorList")
    def on_ml(d): state["ml"] = d
    try:
        sio.connect(base, transports=["websocket"], wait_timeout=10)
    except Exception as e:
        sys.exit(f"cannot connect to {base}: {type(e).__name__}: {e}")
    # login emit MUST carry an ack callback; ack arrival is not guaranteed —
    # the monitorList push event is the auth proof.
    sio.emit("login", dict(username=user, password=pw, token=""), callback=lambda *a: None)
    t = time.time() + 15
    while state["ml"] is None and time.time() < t:
        time.sleep(0.3)
    if state["ml"] is None:
        sio.disconnect(); sys.exit("login failed: no monitorList within 15s (check credentials)")
    return sio, state

def cmd_monitors(a, cfg):
    base, user, pw, _ = resolve(cfg, a)
    sio, state = connect(base, user, pw)
    for m in sorted(state["ml"].values(), key=lambda x: x.get("id") or 0):
        print(f"{m.get('id')}\t{m.get('type')}\t{'UP' if m.get('active') else 'down/paused'}\t{m.get('name')}"
              + ("\t[pushToken set]" if m.get("pushToken") else ""))
    sio.disconnect()

def base_monitor(name, interval):
    # 2.5.x-exact field set: snake_case accepted_statuscodes; no group/path/pathName/tags/retries.
    return dict(type="push", name=name, interval=interval, retryInterval=60, maxretries=2,
                expiryNotification=False, ignoreTls=True, upsideDown=False, maxredirects=10,
                accepted_statuscodes=["200-299"], timeout=48, conditions=[],
                notificationIDList={"notificationIDs": []}, httpBodyEncoding="json",
                description=f"Push dead-man switch (created by uptime-kuma-ops, {time.strftime('%Y-%m-%d')})")

def write_push_env(cfg, name, token):
    """Write PUSH_<NAME> to the configured push env file (the documented home of tokens)."""
    path = cfg.get("push_env_file")
    if not path:
        sys.exit("push_env_file not configured — refusing to print token to stdout; set push_env_file in config")
        return
    p = os.path.expanduser(path)
    key = "PUSH_" + name.upper().replace("-", "_")
    lines = []
    if os.path.exists(p):
        lines = [l for l in open(p).read().splitlines() if l and not l.startswith(key + "=")]
    lines.append(f"{key}={token}")
    with open(p, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    os.chmod(p, 0o600)
    print(f"push token written to {p} as {key}")

def cmd_add_push(a, cfg):
    base, user, pw, _ = resolve(cfg, a)
    sio, state = connect(base, user, pw)
    if any(m.get("name") == a.name for m in state["ml"].values()):
        sys.exit(f"monitor already exists: {a.name}")
    token = secrets.token_hex(16)  # client-generated: 2.5.x does not mint push tokens server-side
    mon = base_monitor(a.name, a.interval)
    mon["pushToken"] = token
    res = sio.call("add", mon, timeout=15)
    if isinstance(res, dict) and res.get("ok") is False:
        # post-store notification-link failures are harmless; column/SQL errors are not
        if "monitor_notification" in str(res.get("msg", "")):
            print(f"created (notification-link warning ignored): {a.name}")
        else:
            sys.exit(f"add failed: {res.get('msg')}")
    else:
        print(f"created: {a.name}")
    write_push_env(cfg, a.name, token)
    sio.disconnect()

def cmd_set_token(a, cfg):
    base, user, pw, _ = resolve(cfg, a)
    sio, state = connect(base, user, pw)
    m = next((m for m in state["ml"].values() if m.get("name") == a.name), None)
    if not m: sys.exit(f"no such monitor: {a.name}")
    token = a.token or secrets.token_hex(16)
    mon = base_monitor(a.name, m.get("interval") or 360)
    mon["id"] = m["id"]; mon["pushToken"] = token
    res = sio.call("editMonitor", mon, timeout=15)
    if isinstance(res, dict) and res.get("ok") is False and "monitor_notification" not in str(res.get("msg", "")):
        sys.exit(f"edit failed: {res.get('msg')}")
    print(f"token set for {a.name}")
    write_push_env(cfg, a.name, token)
    sio.disconnect()

def cmd_push(a, cfg):
    base, _, _, _ = resolve(cfg, a)
    env_file = cfg.get("push_env_file")
    env = {}
    if env_file:
        for line in open(os.path.expanduser(env_file)):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("="); env[k.strip()] = v.strip()
    key = "PUSH_" + a.name.upper().replace("-", "_")
    token = env.get(key)
    if not token: sys.exit(f"no {key} in push env file")
    r = urllib.request.urlopen(f"{base}/api/push/{token}?status=up&msg=&ping=", timeout=10)
    print(f"{a.name}: HTTP {r.status}")

def cmd_init(a, cfg=None):
    print(json.dumps({
        "base_url": "https://kuma.internal",
        "auth_env_file": "~/.config/kuma.env",
        "username_key": "KUMA_ADMIN_USER",
        "password_key": "KUMA_ADMIN_PASSWORD",
        "api_key_key": "KUMA_API_KEY",
        "push_env_file": "~/.config/kuma-monitor.env",
        "ping_script": None,
    }, indent=2) + "\n# save as ~/.agents/uptime-kuma.json (chmod 600). Secrets live in auth_env_file, not here.")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url"); p.add_argument("--env-file")
    p.add_argument("--username"); p.add_argument("--password"); p.add_argument("--api-key")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("metrics"); s.add_argument("--grep", default=None)
    sub.add_parser("monitors")
    s = sub.add_parser("add-push"); s.add_argument("name"); s.add_argument("--interval", type=int, default=360)
    s = sub.add_parser("set-token"); s.add_argument("name"); s.add_argument("--token")
    s = sub.add_parser("push"); s.add_argument("name")
    sub.add_parser("init")
    a = p.parse_args()
    cfg = load_config()
    {"metrics": cmd_metrics, "monitors": cmd_monitors, "add-push": cmd_add_push,
     "set-token": cmd_set_token, "push": cmd_push, "init": cmd_init}[a.cmd](a, cfg)

if __name__ == "__main__":
    main()
