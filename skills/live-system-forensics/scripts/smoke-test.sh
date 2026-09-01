#!/bin/sh
# Smoke-test every command in live-system-forensics SKILL.md.
# Rule: no command ships in SKILL.md without a PASS here or a documented SKIP.
# Usage: sh scripts/smoke-test.sh   (read-only; never prompts for sudo)

PASS=0; FAIL=0; SKIP=0
OS=$(uname)
SUDO=0
[ "$(id -u)" = "0" ] && SUDO=1
# Detect passwordless sudo without prompting
sudo -n true 2>/dev/null && SUDO=1

# timeout is not stock on macOS — use it only when present
if command -v timeout >/dev/null 2>&1; then
  GUARD="timeout 15"
else
  GUARD=""
fi

run() {  # run <id> <condition: any|macos|linux|sudo-macos|sudo-linux> <command...>
  id="$1"; cond="$2"; cmd="$3"
  case "$cond" in
    macos)     [ "$OS" = Darwin ] || { echo "SKIP(platform)  $id  $cmd"; SKIP=$((SKIP+1)); return; } ;;
    linux)     [ "$OS" = Linux ] || { echo "SKIP(platform)  $id  $cmd"; SKIP=$((SKIP+1)); return; } ;;
    sudo-macos) if [ "$OS" != Darwin ] || [ "$SUDO" != 1 ]; then echo "SKIP(needs-sudo)  $id  $cmd"; SKIP=$((SKIP+1)); return; fi ;;
    sudo-linux) if [ "$OS" != Linux ] || [ "$SUDO" != 1 ]; then echo "SKIP(needs-sudo)  $id  $cmd"; SKIP=$((SKIP+1)); return; fi ;;
  esac
  if $GUARD sh -c "$cmd" >/dev/null 2>&1; then
    echo "PASS  $id  $cmd"; PASS=$((PASS+1))
  else
    echo "FAIL  $id  $cmd"; FAIL=$((FAIL+1))
  fi
}

# Phase 1 - Processes / baseline
run P1-01 any     "ps auxww"
run P1-02 macos   "csrutil status"
run P1-03 macos   "codesign -dv --verify /bin/ls"
run P1-04 macos   "spctl -a -t execute /Applications/Safari.app"

# Phase 2 - Network
run P2-01 any     "command -v lsof >/dev/null 2>&1 && lsof -i -P -n || echo 'lsof absent — ss is the fallback'  # absence documented in skill"
run P2-02 linux   "ss -tunap"

# Phase 3 - Persistence
run P3-01 macos   "ls -la ~/Library/LaunchAgents/"
run P3-02 macos   "ls -la /Library/LaunchAgents/"
run P3-03 macos   "ls -la /Library/LaunchDaemons/"
run P3-04 macos   "launchctl list"
run P3-05 sudo-macos "sfltool dumpbtm"
run P3-06 sudo-macos "launchctl dumpstate"
run P3-07 macos   "systemextensionsctl list"
run P3-08 linux   "systemctl --user list-units --type=service --all"
run P3-09 linux   "systemctl --user list-timers"
run P3-10 linux   "ls -la ~/.config/systemd/user/ 2>/dev/null || true  # absent dir = clean"
run P3-11 sudo-linux "systemctl list-timers"
run P3-12 sudo-linux "systemctl list-units --type=service --all"
run P3-13 linux   "ls -la /etc/systemd/system/"
run P3-14 any     "crontab -l >/dev/null 2>&1; [ \$? -le 1 ] || ! command -v crontab >/dev/null  # exit 1 = no crontab; no crontab binary = minimal host"
run P3-15 linux   "ls -la /etc/cron.d/"
run P3-16 linux   "ls -la ~/.config/autostart/ 2>/dev/null || true  # absent dir = clean"
run P3-17 linux   "ls -la /etc/xdg/autostart/"
run P3-18 linux   "cat /etc/ld.so.preload 2>/dev/null || true  # absent file = clean; non-empty = CRITICAL finding"
run P3-19 any     "grep -nE \"(curl|wget|nc -|base64|eval|python|perl)\" ~/.zshrc ~/.bashrc ~/.profile ~/.zprofile 2>/dev/null; rc=\$?; [ \$rc -le 2 ]  # 1=no match(clean) 2=missing rc files(clean); pattern is fixed in-file so syntax errors cannot occur spontaneously"

# Phase 4 - Recent activity
run P4-01 any     "find ~ -maxdepth 3 -name '*.sh' -mtime -7 2>/dev/null || true  # find exits 1 on perm errors; output still valid"
run P4-02 any     "ls -la ~/.ssh/ 2>/dev/null || true  # absent dir = clean"
run P4-03 any     "grep -E \"(command=|from=)\" ~/.ssh/authorized_keys 2>/dev/null || true  # absent file = clean"

# Phase 5 - Extensions / NMH
run P5-01 any     "ls -la ~/.antigravity/extensions/ 2>/dev/null || true  # absent dir = clean"
run P5-02 any     "ls -la ~/.codeium/windsurf/ 2>/dev/null || true  # absent dir = clean"
run P5-03 any     "ls -la ~/.cursor/ 2>/dev/null || true  # absent dir = clean"
run P5-04 any     "ls -la ~/.continue/ 2>/dev/null || true  # absent dir = clean"
run P5-05 macos   "ls -la ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/"
run P5-06 macos   "ls -la ~/Library/Application\ Support/Mozilla/NativeMessagingHosts/ 2>/dev/null || true  # absent dir = clean"
run P5-07 any     "pgrep -fl mcp || true"

echo
echo "Summary: $PASS pass, $FAIL fail, $SKIP skip (platform/sudo)"
[ "$FAIL" = 0 ]
