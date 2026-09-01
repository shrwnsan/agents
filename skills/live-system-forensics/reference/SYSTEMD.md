# Systemd Persistence Reference

## Linux/WSL Systemd Locations

### User Services
```bash
~/.config/systemd/user/
```

### System Services (requires root)
```bash
/etc/systemd/system/
/lib/systemd/system/   # often a symlink to /usr/lib/systemd/system/ on modern distros
```

## Essential Commands

### List User Services
```bash
systemctl --user list-units --type=service --all
systemctl --user list-timers
```

### List System Services
```bash
systemctl list-units --type=service --all
systemctl list-timers
systemctl list-dependencies
```

### Check Service Status
```bash
systemctl --user status <service-name>
systemctl status <service-name>
```

### View Service File
```bash
systemctl --user cat <service-name>
```

## Analyzing Service Files

### Look for Suspicious Elements
```bash
# Find all service files
find /etc/systemd/system -name "*.service" -type f
find ~/.config/systemd/user -name "*.service" -type f

# Check ExecStart entries
grep -r "ExecStart=" /etc/systemd/system/
grep -r "ExecStart=" ~/.config/systemd/user/
```

## Classifying Services

Known-good units are **host-specific** — see the per-host `ALLOWLIST.md` in this directory. A unit in `/etc/systemd/system/` (admin territory) that isn't allowlisted and doesn't come from an installed package (`dpkg -S <file>` / `rpm -qf <file>`) = `unknown` → investigate.

## Red Flags

- Services in ~/.config/systemd/user/ pointing to unusual paths
- Services with network-related ExecStart
- Services with shell script execution
- Newly created services
- Services pointing to /tmp or /var/tmp
