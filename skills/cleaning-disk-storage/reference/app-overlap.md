# Application Overlap Analysis

Detection of redundant applications serving the same purpose. Multiple apps in the same category waste storage through both the app itself and their cached data.

## Contents

- [Detection Strategy](#detection-strategy)
- [Categories to Check](#categories-to-check) — VPNs, browsers, IDEs
- [Reporting Format](#reporting-format)
- [Cleanup](#cleanup)
- [Safety Checks](#safety-checks)
- [Typical Savings](#typical-savings)

## Detection Strategy

### Category-Based Scan
Identify installed apps by category and flag redundancies. Report the full footprint (app + Application Support + Caches) for each.

```bash
# Scan installed apps and their data footprint
echo "=== Application Footprint ==="
for app in /Applications/*.app; do
  name=$(basename "$app" .app)
  app_size=$(du -sh "$app" 2>/dev/null | cut -f1)
  # Check for Application Support data
  support=$(du -sh ~/Library/Application\ Support/*"$name"* 2>/dev/null | cut -f1)
  if [ -n "$support" ]; then
    echo "$app_size (app) + $support (data) = $name"
  else
    echo "$app_size = $name"
  fi
done | sort -rh
```

## Categories to Check

### VPN Clients
Typically only **one** is needed. Each VPN has app + data footprint.

| App | Typical App Size | Typical Data Size |
|-----|-----------------|-------------------|
| NordVPN | ~570 MB | 1-5 GB |
| Mullvad | ~560 MB | <10 MB |
| Cloudflare WARP | ~245 MB | <50 MB |
| Surfshark | ~300 MB | 200-300 MB |
| ExpressVPN | ~200 MB | 100-300 MB |

```bash
# Detect installed VPN apps
find /Applications -maxdepth 1 -iname '*vpn*' -o -iname '*nord*' -o -iname '*mullvad*' -o -iname '*surfshark*' -o -iname '*cloudflare*warp*' 2>/dev/null

# Check data footprint for each
for vpn in NordVPN Mullvad Surfshark; do
  echo "=== $vpn ==="
  du -sh ~/Library/Application\ Support/*$vpn* 2>/dev/null
  du -sh ~/Library/Caches/*$vpn* 2>/dev/null
done
```

### Browsers
Most users need **one primary** browser. Each browser stores profile data, caches, and downloaded media.

```bash
# Detect installed browsers
find /Applications -maxdepth 1 -iname '*brave*' -o -iname '*chrome*' -o -iname '*firefox*' -o -iname '*arc*' -o -iname '*edge*' 2>/dev/null

# Check browser data footprint (can be very large)
for browser in Brave Arc Chrome Firefox; do
  echo "=== $browser ==="
  du -sh ~/Library/Application\ Support/*$browser* 2>/dev/null
  du -sh ~/Library/Caches/*$browser* 2>/dev/null
done
```

### IDEs and Code Editors
Developers often try multiple editors. Active use of 1-2 is typical.

```bash
# Detect installed IDEs
find /Applications -maxdepth 1 -iname '*code*' -o -iname '*windsurf*' -o -iname '*cursor*' -o -iname '*sublime*' -o -iname '*intellij*' -o -iname '*studio*' -o -iname '*kiro*' 2>/dev/null

# Check IDE data footprint (extensions + caches can be several GB)
for ide in Code Windsurf Cursor Sublime Kiro; do
  echo "=== $ide ==="
  du -sh ~/Library/Application\ Support/*$ide* 2>/dev/null
  du -sh ~/Library/Application\ Support/$ide 2>/dev/null
  du -sh ~/Library/Caches/*$ide* 2>/dev/null
done
```

## Reporting Format

When overlap is detected, report per category:

```
### VPN Clients (3 installed — consider keeping 1)
| VPN | App | Data | Total |
|-----|-----|------|-------|
| NordVPN | 570 MB | 4.2 GB | 4.8 GB |
| Mullvad | 560 MB | 3 MB | 563 MB |
| Cloudflare WARP | 245 MB | — | 245 MB |

Potential savings: ~5 GB by removing unused VPNs
```

## Cleanup

For Homebrew-managed apps:
```bash
brew uninstall --cask {app-name}
# Then remove leftover data
trash ~/Library/Application\ Support/{app-data-dir}/
trash ~/Library/Caches/{app-cache-dir}/
```

For direct-download apps:
```bash
trash /Applications/{App}.app
trash ~/Library/Application\ Support/{app-data-dir}/
trash ~/Library/Caches/{app-cache-dir}/
trash ~/Library/Preferences/com.{vendor}.{app}.plist
```

## Safety Checks

- Verify the app is not actively running: `ps aux | grep -i {name}`
- Check for LaunchAgents: `ls ~/Library/LaunchAgents/*{name}*`
- Confirm which app in the category is the primary one before recommending removal
- Check if app syncs data to cloud (most modern apps do — safe to remove locally)

## Typical Savings

| Category | Apps Removed | Typical Savings |
|----------|-------------|-----------------|
| VPNs | 2 of 3 | 2-6 GB |
| Browsers | 1 of 2-3 | 2-15 GB |
| IDEs | 1-2 of 3-5 | 3-8 GB |
