"""Fix remaining contamination: 246->248, L.D.W. James Pigors, DIAMOND 9999+++"""
import os, re
from pathlib import Path

BASE = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F05_MSC_ORIGINAL")
EXHIBITS = BASE / "EXHIBITS"
changes = 0

# 1. Fix "246 days" -> "248 days" on line 11 of all exhibits
for fn in sorted(EXHIBITS.glob("EXHIBIT_*.md")):
    with open(fn, "r", encoding="utf-8") as f:
        content = f.read()
    
    old = "**Days Since Last Contact with L.D.W.:** 246 days (since July 29, 2025)"
    new = "**Days Since Last Contact with L.D.W.:** 248 days (since July 29, 2025)"
    if old in content:
        content = content.replace(old, new)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  FIXED 246->248: {fn.name}")
        changes += 1

# 2. Fix "L.D.W. James Pigors" in EXHIBIT_B
exhibit_b = EXHIBITS / "EXHIBIT_B.md"
with open(exhibit_b, "r", encoding="utf-8") as f:
    content = f.read()

count_ldw = content.count("L.D.W. James Pigors")
if count_ldw > 0:
    content = content.replace("L.D.W. James Pigors", "L.D.W.")
    print(f"  FIXED L.D.W. James Pigors -> L.D.W.: EXHIBIT_B.md ({count_ldw} instances)")
    changes += 1

# 3. Fix remaining DIAMOND 9999+++ instances
# Pattern: "DIAMOND 9999+++ MASTER RESEARCH & BUILD PROMPT — "WATSON DEFENDANTS" CIVIL COMPLAINT (MICHIGAN-LOCKED)"
diamond_pattern = 'DIAMOND 9999+++ MASTER RESEARCH & BUILD PROMPT — "WATSON DEFENDANTS" CIVIL COMPLAINT (MICHIGAN-LOCKED)'
diamond_replacement = 'Civil Complaint Research — Watson Defendants (Michigan)'

count_d = content.count(diamond_pattern)
if count_d > 0:
    content = content.replace(diamond_pattern, diamond_replacement)
    print(f"  FIXED DIAMOND 9999+++: EXHIBIT_B.md ({count_d} instances)")
    changes += 1

with open(exhibit_b, "w", encoding="utf-8") as f:
    f.write(content)

# Fix DIAMOND in EXHIBIT_E
exhibit_e = EXHIBITS / "EXHIBIT_E.md"
with open(exhibit_e, "r", encoding="utf-8") as f:
    content = f.read()

count_d = content.count(diamond_pattern)
if count_d > 0:
    content = content.replace(diamond_pattern, diamond_replacement)
    with open(exhibit_e, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  FIXED DIAMOND 9999+++: EXHIBIT_E.md ({count_d} instances)")
    changes += 1

# Fix DIAMOND in EXHIBIT_G
exhibit_g = EXHIBITS / "EXHIBIT_G.md"
with open(exhibit_g, "r", encoding="utf-8") as f:
    content = f.read()

count_d = content.count(diamond_pattern)
if count_d > 0:
    content = content.replace(diamond_pattern, diamond_replacement)
    with open(exhibit_g, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  FIXED DIAMOND 9999+++: EXHIBIT_G.md ({count_d} instances)")
    changes += 1

print(f"\nTotal additional fixes: {changes}")
