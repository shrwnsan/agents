# macOS System Data

Large macOS-managed data that doesn't correspond to any single installed application. These are often invisible to per-app analysis but can consume significant storage.

## Aerial Wallpaper Videos

High-resolution video files downloaded by macOS for dynamic wallpapers and screen savers. These are the Apple TV aerial drone footage (4K-5K resolution).

### Locations

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Application Support/com.apple.wallpaper/aerials/videos/` | User-downloaded aerial videos | Safe |
| `~/Library/Application Support/com.apple.wallpaper/aerials/manifest/` | Video manifest metadata | Safe |
| `~/Library/Application Support/com.apple.wallpaper/aerials/thumbnails/` | Video thumbnails | Safe |
| `/Library/Application Support/com.apple.idleassetsd/` | System-level aerial assets | Do not delete |

### Scanning
```bash
# Check user-level aerial video storage
du -sh ~/Library/Application\ Support/com.apple.wallpaper/aerials/
du -sh ~/Library/Application\ Support/com.apple.wallpaper/aerials/videos/ 2>/dev/null

# Count individual videos
ls ~/Library/Application\ Support/com.apple.wallpaper/aerials/videos/ 2>/dev/null | wc -l

# Check system-level assets
du -sh /Library/Application\ Support/com.apple.idleassetsd/ 2>/dev/null
```

### Cleanup
```bash
# Delete user-level aerial videos
trash ~/Library/Application\ Support/com.apple.wallpaper/aerials/
```

### Important Notes

- **macOS will re-download these** if the wallpaper is set to an aerial/dynamic option
- To prevent re-download, switch wallpaper to a static image **before** deleting
- Change via: System Settings > Wallpaper > select a static/color wallpaper
- After deletion, macOS may re-create the directory with manifest and thumbnails (~12 MB) but not the full videos unless an aerial wallpaper is selected
- System-level assets at `/Library/Application Support/com.apple.idleassetsd/` should **not** be deleted
- The current wallpaper setting can be checked with:
  ```bash
  defaults read com.apple.wallpaper 2>/dev/null | grep -i wallpaper
  ```

### Typical Sizes

- 60 aerial videos: **30 GB** (individual videos range 500 MB - 1.4 GB each)
- Manifest + thumbnails: ~12 MB
- System-level aerials: 2-5 GB

---

## Other macOS System Data

| Location | Description | Cleanability |
|----------|-------------|--------------|
| `~/Library/Application Support/com.apple.mobileAssetDesktop/` | Desktop asset downloads | Inspect first |
| `~/Library/Application Support/com.apple.ProtectedCloudStorage/` | iCloud protected data | Do not delete |
| `~/Library/Caches/com.apple.textunderstandingd/` | Text understanding ML cache | Safe |

### Scanning
```bash
du -sh ~/Library/Application\ Support/com.apple.mobileAssetDesktop/ 2>/dev/null
du -sh ~/Library/Caches/com.apple.textunderstandingd/ 2>/dev/null
```
