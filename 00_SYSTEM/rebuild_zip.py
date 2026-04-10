"""Rebuild CORTEX distribution ZIP with all current files."""
import zipfile, os, sys

DIST = r"J:\CORTEX\dist\CORTEX"
OUT = r"J:\CORTEX\CORTEX_v1.0.0_win64.zip"
README = r"J:\CORTEX\README.md"
LAUNCH = r"J:\CORTEX\LAUNCH_CORTEX.bat"
LANDING = r"J:\CORTEX\landing"

if not os.path.isdir(DIST):
    print(f"ERROR: dist folder not found: {DIST}")
    sys.exit(1)

print("Building CORTEX_v1.0.0_win64.zip ...")
count = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    # Main dist folder
    for root, dirs, files in os.walk(DIST):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.join("CORTEX", os.path.relpath(full, DIST))
            zf.write(full, arc)
            count += 1
    # README
    if os.path.exists(README):
        zf.write(README, "CORTEX/README.md")
        count += 1
    # Launcher
    if os.path.exists(LAUNCH):
        zf.write(LAUNCH, "CORTEX/LAUNCH_CORTEX.bat")
        count += 1
    # Landing page
    if os.path.isdir(LANDING):
        for root, dirs, files in os.walk(LANDING):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.join("CORTEX/landing", os.path.relpath(full, LANDING))
                zf.write(full, arc)
                count += 1

size_mb = os.path.getsize(OUT) / (1024 * 1024)
print(f"Done: {count} files, {size_mb:.1f} MB")
print(f"Output: {OUT}")
