"""Update mbp_build.py to include V7 visualization files."""
import os

BUILD = r"C:\Users\andre\LitigationOS\scripts\mbp_build.py"
content = open(BUILD, encoding="utf-8").read()

changes = 0

# 1. Add V7 to VIS_DIR search order (prefer V7 > V15 > V9 > V5)
old1 = 'for ver in ("MANBEARPIG_V15", "MANBEARPIG_V9", "MANBEARPIG_V5"):'
new1 = 'for ver in ("MANBEARPIG_V7", "MANBEARPIG_V15", "MANBEARPIG_V9", "MANBEARPIG_V5"):'
if 'MANBEARPIG_V7' not in content:
    content = content.replace(old1, new1, 1)
    changes += 1
    print("1. Added V7 to VIS_DIR search order (V7 first)")
else:
    print("1. SKIP: V7 already in search")

# 2. Add V7 data collection alongside primary VIS_DIR
# After the VIS_DIR files block, add V7 collection
old2 = '''    # Brain database'''
new2 = '''    # V7 SELFEVOLVE visualization (always include alongside primary)
    v7_dir = REPO_ROOT / "08_MEDIA" / "MANBEARPIG_V7"
    if v7_dir.exists() and str(v7_dir) != str(VIS_DIR):
        for f in v7_dir.iterdir():
            if f.is_file():
                datas.append((str(f), "MANBEARPIG_V7"))
        print(f"  V7 SELFEVOLVE: {sum(1 for f in v7_dir.iterdir() if f.is_file())} files from {v7_dir}")

    # Brain database'''

if 'V7 SELFEVOLVE visualization' not in content:
    content = content.replace(old2, new2, 1)
    changes += 1
    print("2. Added V7 data collection to _collect_data_files()")
else:
    print("2. SKIP: V7 collection already exists")

# Write
with open(BUILD, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nBuild script modified: {changes} changes")
print(f"  File: {BUILD}")
print(f"  Size: {os.path.getsize(BUILD):,} bytes")
print("  V7 is now primary VIS_DIR (V15 fallback)")
print("  Both V7 + V15 bundled when both exist")
