"""Fix DIAMOND 9999+++ with proper Unicode character matching"""
import re
from pathlib import Path

EXHIBITS = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F05_MSC_ORIGINAL\EXHIBITS")

# Match DIAMOND 9999+++ with any type of quotes around WATSON DEFENDANTS
diamond_re = re.compile(r'DIAMOND 9999\+\+\+ MASTER RESEARCH & BUILD PROMPT [—–-] .?WATSON DEFENDANTS.? CIVIL COMPLAINT \(MICHIGAN-LOCKED\)')
replacement = 'Civil Complaint Research — Watson Defendants (Michigan)'

for fn in ["EXHIBIT_B.md", "EXHIBIT_E.md", "EXHIBIT_G.md"]:
    fp = EXHIBITS / fn
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    matches = diamond_re.findall(content)
    if matches:
        content = diamond_re.sub(replacement, content)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  FIXED DIAMOND 9999+++: {fn} ({len(matches)} instances)")
        for m in matches:
            print(f"    Matched: {m[:80]}...")
    else:
        print(f"  No DIAMOND matches in {fn}")

# Verify
for fn in ["EXHIBIT_B.md", "EXHIBIT_E.md", "EXHIBIT_G.md"]:
    fp = EXHIBITS / fn
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    remaining = diamond_re.findall(content)
    raw_remaining = content.count("DIAMOND 9999")
    print(f"  {fn}: regex matches={len(remaining)}, 'DIAMOND 9999' raw count={raw_remaining}")
