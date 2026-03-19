# LitigationOS Desktop — Build Instructions

## Prerequisites

- **Node.js** v18+ (tested with v25.6.0)
- **npm** v9+ (tested with v11.9.0)
- **Windows 10/11** (x64)
- **~2 GB free disk space** for a lean build (without extraResources)
- **~15+ GB free disk space** for a full build with bundled system files

## Quick Build (Portable .exe)

```powershell
cd 00_SYSTEM\apps\desktop

# Install dependencies (if first time)
npm install

# Build the Next.js renderer (static export)
npx next build src/renderer

# Build portable .exe (~105 MB)
npx electron-builder --win --config.win.target=portable
```

Output: `dist/LitigationOS 1.0.0.exe`

## NSIS Installer Build

```powershell
# Build installer with desktop/start-menu shortcuts (~123 MB)
npx electron-builder --win --config.win.target=nsis
```

Output: `dist/LitigationOS Setup 1.0.0.exe`

## Full Build (Both Targets)

```powershell
# Renderer + both Windows targets
npm run build
```

Or equivalently:

```powershell
npx next build src/renderer && npx electron-builder
```

## Build Outputs

| File | Type | Size |
|------|------|------|
| `LitigationOS 1.0.0.exe` | Portable (no install needed) | ~105 MB |
| `LitigationOS Setup 1.0.0.exe` | NSIS Installer | ~123 MB |
| `dist/win-unpacked/` | Unpacked app directory | ~300 MB |

## Known Issues & Notes

### extraResources Configuration

The `package.json` build config includes an `extraResources` section that bundles
`00_SYSTEM/` files into the installer. This directory can be **11+ GB**, so the
config excludes large items (databases, ML models, caches, dist directories).

To build **without** any extraResources (lean app only):

```json
"extraResources": []
```

To customize what gets bundled, edit the `filter` array in `package.json` → `build.extraResources`.

### Icon

The `public/icon.ico` is a placeholder (solid dark blue 256×256).
Replace it with a proper branded icon before release. The icon must be at least 256×256.

### First Build Downloads

electron-builder downloads on first run:
- Electron binary (~108 MB)
- winCodeSign (~5.6 MB)
- NSIS tools (~2 MB)

These are cached in `%LOCALAPPDATA%/electron-builder/Cache/` for subsequent builds.

### Native Dependencies

`better-sqlite3` requires a prebuilt native binary. electron-builder handles this
automatically via `install prebuilt binary`. If it fails:

```powershell
npx electron-rebuild -f -w better-sqlite3
```

### Database Path

The app expects the litigation database at:
```
%USERPROFILE%\LitigationOS\litigation_context.db
```

This path is hardcoded in `src/main/main.js` and is **not** bundled with the installer.
The database must exist on the target machine at that path.

### Code Signing

The current build is **unsigned**. Windows SmartScreen will show a warning on first run.
To sign, add to `package.json`:

```json
"win": {
  "certificateFile": "path/to/cert.pfx",
  "certificatePassword": "..."
}
```

Or use environment variables: `CSC_LINK` and `CSC_KEY_PASSWORD`.
