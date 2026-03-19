"""
AUTONOMOS Directory & __init__.py Creator
Run: python _mkdirs_autonomos.py
Creates: autonomos/{sentinel,inquisitor,shared,db,tests} + 4 __init__.py files
"""
import os, sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

base = r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos"
dirs = ["sentinel", "inquisitor", "shared", "db", "tests"]

# Create all directories
for d in dirs:
    p = os.path.join(base, d)
    os.makedirs(p, exist_ok=True)
    print(f"Created dir: {p}")

# Create __init__.py files with proper docstrings
init_packages = {
    "": "autonomos",
    "sentinel": "sentinel",
    "inquisitor": "inquisitor",
    "shared": "shared",
}
for subdir, name in init_packages.items():
    init_file = os.path.join(base, subdir, "__init__.py")
    with open(init_file, "w", encoding="utf-8") as f:
        f.write(f'"""AUTONOMOS \u2014 {name} package."""\n')
    print(f"Created file: {init_file}")

# Verification
print("\n--- Verification ---")
all_ok = True
for d in [""] + dirs:
    p = os.path.join(base, d) if d else base
    exists = os.path.isdir(p)
    init_exists = os.path.isfile(os.path.join(p, "__init__.py"))
    label = d if d else "autonomos"
    init_str = " + __init__.py" if init_exists else ""
    status = "OK" if exists else "MISSING"
    if not exists:
        all_ok = False
    print(f"  {status}: {label}/{init_str}")

print(f"\n{'ALL GOOD' if all_ok else 'ISSUES FOUND'} - DONE")
