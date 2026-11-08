# Process Analysis Reference

## Essential Commands

### List All Processes
```bash
ps auxww
```

### Find Process by Name
```bash
ps auxww | grep -i "suspicious"
ps auxww | grep -v grep | grep "process_name"
```

### Find Process by Path
```bash
ps auxww | grep "/Users/.*/Library"
ps auxww | grep "/Users/.*/.antigravity"
```

### Process Details
```bash
# Get PID info
ps -p <PID> -o pid,ppid,user,%cpu,%mem,comm

# Find process parent
ps -o ppid= -p <PID>
```

### High Resource Processes
```bash
# Top CPU (macOS BSD ps has no --sort; it sorts with -r, procps with --sort)
ps auxwwr | head -20               # macOS
ps auxww --sort=-%cpu | head -20   # Linux

# Top Memory
ps auxwwm | head -20               # macOS
ps auxww --sort=-%mem | head -20   # Linux
```

## Classifying Processes

- Anything on the sealed system volume (`/System`, `/bin`, `/sbin`, `/usr`) is Apple-stock (`known-apple`); codesign-verify when unsure.
- Everything else: check against the per-host `ALLOWLIST.md` in this directory.
- Not allowlisted and not Apple-stock → `unknown` → investigate (codesign check on macOS).

## Red Flags

- Processes from `~/.antigravity/` (unless user installed)
- Processes from `~/Library/Application Support/` (unusual)
- Processes with no associated .app
- Zombie processes
- Processes with root privileges that shouldn't
