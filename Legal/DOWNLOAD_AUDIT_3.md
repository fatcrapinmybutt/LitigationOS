# DOWNLOAD_AUDIT

Bundle: MBP_PORTAL_PERMANENT_BRIDGE_INSTALLER_v4_20260109
Built (UTC): 2026-01-10T04:25:53Z

Integrity Gates:
- ZIP testzip(): PASS
- ZIP size bytes: 14178
- ZIP sha256: acf8fd88502ddb76b2548bfe49cc8a0e0853fb6fbb3f612cb88c683f91179777

Contents:
- manifest.json (per-file sha256)
- manifest.csv
- docs/DOWNLOAD_LINK_RELIABILITY.md

Notes:
- Windows scheduled task uses cmd.exe /c to support '&&'.
- Single-run worker invocation is: `mbp-portal worker` (no --once flag).
