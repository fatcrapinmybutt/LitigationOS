#!/data/data/com.termux/files/usr/bin/bash
# install_bin_fix_watcher_termux.sh (v32)
# Starts a foreground watcher for /sdcard/Download to auto-rename .bin downloads to .zip by magic bytes.
# Requirements: termux + python installed.
set -euo pipefail
WATCH_DIR="${1:-/sdcard/Download}"
INTERVAL="${2:-3}"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
python "${SCRIPT_DIR}/tools/bin_fix_watcher.py" --dir "${WATCH_DIR}" --interval "${INTERVAL}" --verify
