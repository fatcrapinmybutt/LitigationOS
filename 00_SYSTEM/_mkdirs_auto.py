"""Run this once to create AUTONOMOS directories. Usage: python _mkdirs_auto.py"""
import os
dirs = [
    r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\.inbox",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\.outbox",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"  [OK] {d}")

# Create __init__.py files
for sub in ["", "sentinel", "inquisitor", "shared"]:
    init = os.path.join(r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos", sub, "__init__.py")
    if not os.path.exists(init):
        with open(init, "w") as f:
            f.write(f'"""AUTONOMOS — {sub or "root"} package."""\n')
        print(f"  [OK] {init}")

print("\nDone! All AUTONOMOS directories created.")
