"""Create AUTONOMOS directory structure."""
import os
base = r"C:\Users\andre\LitigationOS\00_SYSTEM\autonomos"
dirs = ["sentinel", "inquisitor", "shared", "db", "tests"]
for d in dirs:
    p = os.path.join(base, d)
    os.makedirs(p, exist_ok=True)
    print(f"Created: {p}")
# Create __init__.py files
for d in ["", "sentinel", "inquisitor", "shared"]:
    p = os.path.join(base, d, "__init__.py")
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write(f'"""AUTONOMOS — {d or "root"} package."""\n')
        print(f"Created: {p}")
print("DONE")
