"""Clean F05 exhibit contamination — remove rows with DELTA/OMEGA/HYPER/EVENT_HORIZON references."""
import re
import os

EXHIBIT_DIR = r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F05_MSC_ORIGINAL\EXHIBITS"

# Patterns that indicate AI/system contamination in exhibit data rows
CONTAM_PATTERNS = [
    r'HYPER::COPILOT',
    r'EVENT_HORIZON_DELTA',
    r'OMEGA Response Warfare',
    r'Auto-Generated 2026',
    r'DELTA_COMPREHENSIVE_LEGAL_ANALYSIS',
    r'SOVEREIGN_RUNTIME',
    r'MODE=AGENTIC\|TOOLS\|MCP',
    r'APPEND_ONLY\|TRUTH',
    r'VERSION=2026.*Δ9',
    r'CYCLE 0002.*CLASSIFICATION.*EXCLUSION',
    r'EXCLUDED_HOUSING',
]

compiled = [re.compile(p, re.IGNORECASE) for p in CONTAM_PATTERNS]

def is_contaminated(line):
    return any(p.search(line) for p in compiled)

total_removed = 0
files_fixed = []

for fname in sorted(os.listdir(EXHIBIT_DIR)):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(EXHIBIT_DIR, fname)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    clean_lines = []
    removed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_contaminated(line):
            # Check if this is a table row (starts with |)
            # If so, skip to end of this table row (next line starting with |)
            if line.strip().startswith('|'):
                removed += 1
                # Multi-line table rows: skip until next row or non-table line
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('|') and lines[i].strip():
                    i += 1
                    removed += 1
                continue
            else:
                # Non-table contaminated line — remove it
                removed += 1
                i += 1
                continue
        clean_lines.append(line)
        i += 1
    
    if removed > 0:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(clean_lines)
        total_removed += removed
        files_fixed.append((fname, removed))
        print(f"  {fname}: removed {removed} contaminated lines")

print(f"\nTotal: {total_removed} contaminated lines removed from {len(files_fixed)} files")

# Verify no contamination remains
print("\n--- Verification scan ---")
remaining = 0
for fname in sorted(os.listdir(EXHIBIT_DIR)):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(EXHIBIT_DIR, fname)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if is_contaminated(line):
                print(f"  REMAINING: {fname}:{i}: {line.strip()[:80]}")
                remaining += 1

if remaining == 0:
    print("  ✅ ZERO contamination remaining in F05 exhibits")
else:
    print(f"  ⚠️ {remaining} contaminated lines still remain")
