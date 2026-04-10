"""Find exact locations of compliance violations."""
import re

OUT_DIR = r"C:\Users\andre\LitigationOS\04_ANALYSIS\CROSS_EXAM_BANKS"

# Check Watson file for McNeil with one L
with open(f"{OUT_DIR}\\WATSON_CROSS_EXAM.md", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if re.search(r"McNeil[^l]", line):
        print(f"WATSON line {i}: {line.strip()[:120]}")

print()

# Check McNeill file for wrong defendant name
with open(f"{OUT_DIR}\\MCNEILL_CROSS_EXAM.md", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if "Emily Ann" in line or "Emily M." in line or "Tiffany" in line:
        print(f"MCNEILL line {i}: {line.strip()[:120]}")
