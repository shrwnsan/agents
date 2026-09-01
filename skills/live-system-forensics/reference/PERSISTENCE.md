# Persistence Analysis Reference

## Startup Locations (Priority Order)

### 1. User LaunchAgents
```bash
ls -la ~/Library/LaunchAgents/
```
Path: `~/Library/LaunchAgents/`

### 2. System-wide LaunchAgents
```bash
ls -la /Library/LaunchAgents/
```
Path: `/Library/LaunchAgents/`

### 3. LaunchDaemons (System, requires root)
```bash
ls -la /Library/LaunchDaemons/
```
Path: `/Library/LaunchDaemons/`

### 4. Cron Jobs
```bash
crontab -l                    # User crontab
sudo ls /var/at/tabs/         # At jobs
```

### 5. Login Items
```bash
ls -la ~/Library/Application\ Support/LoginItems/
```

### 6. Reusable Items (macOS 13+)
```bash
defaults read com.apple.loginwindow.plist 2>/dev/null || plutil -p ~/Library/Preferences/com.apple.loginwindow.plist 2>/dev/null
```

### 7. Configuration Profiles (MDM or attacker-installed)
```bash
profiles list            # user-level
sudo profiles show       # full profile inventory — investigate any profile you didn't install
```

### 8. Disk-less launchd persistence (CRITICAL evasion technique)
Agents can be bootstrapped into a running launchd session without a plist on disk (`launchctl bootstrap`). Static `ls` scans miss these — see the `launchctl dumpstate` check in SKILL.md Phase 3.

## Analyzing Plist Files

### View Plist Contents
```bash
plutil -p ~/Library/LaunchAgents/com.example.plist
cat ~/Library/LaunchAgents/com.example.plist
```

### Check for Executable Paths
```bash
grep -r "ProgramArguments" ~/Library/LaunchAgents/
grep -r "Program" ~/Library/LaunchAgents/
```

## Classifying Persistence Items

Known-good persistence labels are **host-specific** — see the per-host `ALLOWLIST.md` in this directory. An item not in the allowlist and not recognizably from an installed vendor's installer = `unknown` → inspect its plist (`plutil -p`) and target binary before trusting it.

## Red Flags

- Unknown LaunchAgents in user's ~/Library
- Items with paths to ~/Library/Application Support
- Newly created plist files
- Items pointing to shell scripts in /tmp or Downloads
- Items with network-related ProgramArguments
- Items with suspicious domain names in labels

## Quick Audit Script

```bash
echo "=== User LaunchAgents ==="
ls -la ~/Library/LaunchAgents/

echo "=== System LaunchAgents ==="
ls -la /Library/LaunchAgents/

echo "=== LaunchDaemons ==="
ls -la /Library/LaunchDaemons/

echo "=== Cron Jobs ==="
crontab -l 2>/dev/null || echo "None"
```
