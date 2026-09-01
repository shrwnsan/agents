# Network Analysis Reference

## Essential Commands

### List All Connections
Always use `-n` (skip reverse DNS — faster, and avoids generating DNS queries that reveal you're inspecting):
```bash
lsof -i -P -n
lsof -i -P -n | grep -E "(LISTEN|ESTABLISHED)"
```

### Find Process by Port
```bash
lsof -i :<PORT>
lsof -i :443
lsof -i :8080
```

### Find Ports by Process
```bash
lsof -i -a -p <PID>
```

### Established Connections Only
```bash
lsof -i -P -n | grep ESTABLISHED
```

Note: filtering with `grep ESTABLISHED` excludes TIME_WAIT/CLOSE_WAIT by definition (they're separate states). To see those dying sockets explicitly — a pile of CLOSE_WAIT on one process can indicate a stalled or beaconing service:
```bash
lsof -i -P -n | grep -E "(TIME_WAIT|CLOSE_WAIT)" | awk '{print $1}' | sort | uniq -c
```

### Outbound Connections
```bash
lsof -i -P -n | grep -v LISTEN
```

## Classifying Connections

- Map every connection/listener to its owning process first; unexplained owners are the finding, not the destination.
- Check destinations against the per-host `ALLOWLIST.md` in this directory (VPN endpoints, messaging DCs, sync hosts, etc.).
- Not allowlisted → `unknown` → investigate the process, not just the IP.

## Suspicious Indicators

- Connections to unknown/unusual domains
- Processes with no associated app making network calls
- Unusual ports (above 49152 are dynamic, but check for well-known ports)
- Connections to known malicious IPs/domains
- Processes listening on all interfaces (0.0.0.0) unexpectedly

## Quick Check Script

```bash
echo "=== Network Connections ==="
lsof -i -P -n | grep -E "(LISTEN|ESTABLISHED)" | head -30

echo "=== Suspicious Ports ==="
lsof -i -P -n | grep -v -E "(localhost|127.0.0.1|::1)"
```
