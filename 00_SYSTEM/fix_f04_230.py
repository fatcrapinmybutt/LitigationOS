"""Fix stale 230+ day counts in F04 Federal §1983 Complaint → 248+"""
import re
from pathlib import Path

f04 = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F04_FEDERAL_1983\04_FEDERAL_1983_COMPLAINT.md")
text = f04.read_text(encoding="utf-8")
count = text.count("230+")
text_new = text.replace("230+", "248+")
f04.write_text(text_new, encoding="utf-8")
print(f"F04: replaced {count} instances of '230+' → '248+'")

# Also check other F04 files
for md in Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F04_FEDERAL_1983").glob("*.md"):
    if md.name == "04_FEDERAL_1983_COMPLAINT.md":
        continue
    t = md.read_text(encoding="utf-8")
    c = t.count("230+")
    if c > 0:
        t2 = t.replace("230+", "248+")
        md.write_text(t2, encoding="utf-8")
        print(f"  {md.name}: replaced {c} instances")
    else:
        print(f"  {md.name}: clean")
