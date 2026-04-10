"""
Fix contamination in F05_MSC_ORIGINAL filing directory.
Handles: ewpage, COMPUTE AT FILING, BEFORE FILING, MANBEARPIG, AI stats
"""
import re
import os
from pathlib import Path

BASE = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F05_MSC_ORIGINAL")
SEPARATION_DAYS = 248  # July 29, 2025 to April 3, 2026

changes_log = []

def log_change(filepath, line_num, category, old_snippet, new_snippet):
    rel = str(filepath).replace(str(BASE) + "\\", "")
    changes_log.append({
        "file": rel,
        "line": line_num,
        "category": category,
        "old": old_snippet[:120],
        "new": new_snippet[:120]
    })

def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    lines_orig = content.split("\n")
    
    # 1. Fix ewpage -> \newpage
    new_content = []
    for i, line in enumerate(content.split("\n")):
        if line.strip() == "ewpage":
            log_change(filepath, i+1, "ewpage", "ewpage", "\\newpage")
            new_content.append("\\newpage")
        else:
            new_content.append(line)
    content = "\n".join(new_content)
    
    # 2. Fix [COMPUTE AT FILING: days since July 29, 2025] patterns
    compute_pattern = r'\[COMPUTE AT FILING:?\s*(?:days since July 29,? 2025|compute.*?days)?\s*\]'
    
    def replace_compute(match):
        return str(SEPARATION_DAYS)
    
    old_content = content
    content = re.sub(compute_pattern, replace_compute, content, flags=re.IGNORECASE)
    
    if content != old_content:
        # Count replacements
        count = len(re.findall(compute_pattern, old_content, flags=re.IGNORECASE))
        log_change(filepath, 0, "COMPUTE_AT_FILING", f"[COMPUTE AT FILING...] x{count}", f"{SEPARATION_DAYS} x{count}")
    
    # 3. Fix [BEFORE FILING: compute (filing_date − July 29, 2025) days] patterns
    before_pattern1 = r'\*\*\[BEFORE FILING: compute \(filing_date [−-] July 29, 2025\) days\]\*\*'
    old_content = content
    content = re.sub(before_pattern1, f'**{SEPARATION_DAYS}**', content)
    if content != old_content:
        count = len(re.findall(before_pattern1, old_content))
        log_change(filepath, 0, "BEFORE_FILING_BOLD", f"**[BEFORE FILING: compute...]** x{count}", f"**{SEPARATION_DAYS}** x{count}")
    
    before_pattern2 = r'\*\*\[BEFORE FILING: compute days\]\*\*'
    old_content = content
    content = re.sub(before_pattern2, f'**{SEPARATION_DAYS}**', content)
    if content != old_content:
        count = len(re.findall(before_pattern2, old_content))
        log_change(filepath, 0, "BEFORE_FILING_BOLD2", f"**[BEFORE FILING: compute days]** x{count}", f"**{SEPARATION_DAYS}** x{count}")
    
    # Non-bold BEFORE FILING compute patterns  
    before_pattern3 = r'\[BEFORE FILING: compute \(filing_date [−-] July 29, 2025\) days\]'
    old_content = content
    content = re.sub(before_pattern3, str(SEPARATION_DAYS), content)
    if content != old_content:
        count = len(re.findall(before_pattern3, old_content))
        log_change(filepath, 0, "BEFORE_FILING_PLAIN", f"[BEFORE FILING: compute...] x{count}", f"{SEPARATION_DAYS} x{count}")
    
    before_pattern4 = r'\[BEFORE FILING: compute days\]'
    old_content = content
    content = re.sub(before_pattern4, str(SEPARATION_DAYS), content)
    if content != old_content:
        count = len(re.findall(before_pattern4, old_content))
        log_change(filepath, 0, "BEFORE_FILING_PLAIN2", f"[BEFORE FILING: compute days] x{count}", f"{SEPARATION_DAYS} x{count}")
    
    # [BEFORE FILING: Verify this information] -> just remove the bracket
    before_verify = r'\[BEFORE FILING: Verify this information\]'
    old_content = content
    content = re.sub(before_verify, '', content)
    if content != old_content:
        count = len(re.findall(before_verify, old_content))
        log_change(filepath, 0, "BEFORE_FILING_VERIFY", f"[BEFORE FILING: Verify...] x{count}", f"(removed) x{count}")
    
    # [BEFORE FILING: Insert filing date] -> (date of filing)
    before_insert = r'\[BEFORE FILING: Insert filing date\]'
    old_content = content
    content = re.sub(before_insert, 'the date of filing', content)
    if content != old_content:
        count = len(re.findall(before_insert, old_content))
        log_change(filepath, 0, "BEFORE_FILING_INSERT", f"[BEFORE FILING: Insert...] x{count}", f"the date of filing x{count}")
    
    # [BEFORE FILING: Attach Certified copies of each order] -> leave as filing instruction (these are action items, not text placeholders)
    # Actually these are instructions to the filer, not court text. Remove brackets, keep as note.
    before_attach = r'\[BEFORE FILING: Attach Certified copies of each order\]'
    old_content = content
    content = re.sub(before_attach, '*(Certified copies of each order to be attached)*', content)
    if content != old_content:
        count = len(re.findall(before_attach, old_content))
        log_change(filepath, 0, "BEFORE_FILING_ATTACH", f"[BEFORE FILING: Attach...] x{count}", f"(Certified copies note) x{count}")
    
    before_attach2 = r'\*\*\[BEFORE FILING: Attach CERTIFIED COPIES OF ALL EX PARTE ORDERS\]\*\*'
    old_content = content
    content = re.sub(before_attach2, '*(Certified copies of all ex parte orders to be attached)*', content)
    if content != old_content:
        count = len(re.findall(before_attach2, old_content))
        log_change(filepath, 0, "BEFORE_FILING_ATTACH_BOLD", f"**[BEFORE FILING: Attach...]** x{count}", f"(Certified copies note) x{count}")
    
    # 4. Fix MANBEARPIG references
    # APEX_MANBEARPIG Autonomous Execution Report -> [REDACTED] Session Summary
    old_content = content
    content = content.replace("APEX_MANBEARPIG Autonomous Execution Report", "[REDACTED] Session Summary")
    if content != old_content:
        log_change(filepath, 0, "MANBEARPIG_HEADER", "APEX_MANBEARPIG Autonomous Execution Report", "[REDACTED] Session Summary")
    
    # ManBearPig/Wizards/Governors entries in tables -> [REDACTED] Internal Reference
    manbearpig_table = re.compile(r'ManBearPig/Wizards/Governors\s*[—–-]\s*Custody Wizard \d+')
    old_content = content
    content = manbearpig_table.sub('[REDACTED] Internal Reference', content)
    if content != old_content:
        count = len(manbearpig_table.findall(old_content))
        log_change(filepath, 0, "MANBEARPIG_WIZARD", f"ManBearPig/Wizards/Governors... x{count}", f"[REDACTED] Internal Reference x{count}")
    
    # THE MANBEARPIG — Omega-Infinity Upgrade
    old_content = content
    content = content.replace("# THE MANBEARPIG — Omega-Infinity Upgrade + Full Fleet Operations", "# Session Summary — System Operations Report")
    if content != old_content:
        log_change(filepath, 0, "MANBEARPIG_OMEGA", "# THE MANBEARPIG — Omega-Infinity...", "# Session Summary — System Operations Report")
    
    # 5. Fix "DIAMOND 9999+++ ULTRA-SUPREME" AI reference
    old_content = content
    content = content.replace("**All systems now upgraded to DIAMOND 9999+++ ULTRA-SUPREME.**", "[REDACTED]")
    if content != old_content:
        log_change(filepath, 0, "AI_DIAMOND", "DIAMOND 9999+++ ULTRA-SUPREME", "[REDACTED]")
    
    # Write back if changed
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

# Process all files
all_files = []
for root, dirs, files in os.walk(BASE):
    for fn in files:
        if fn.endswith(".md"):
            all_files.append(Path(root) / fn)

print(f"Processing {len(all_files)} files...")

changed_count = 0
for fp in sorted(all_files):
    if fix_file(fp):
        changed_count += 1
        print(f"  FIXED: {fp.name}")
    else:
        print(f"  clean: {fp.name}")

print(f"\n{'='*60}")
print(f"Files changed: {changed_count}/{len(all_files)}")
print(f"Total changes: {len(changes_log)}")
print(f"\nChange Summary:")
print(f"{'='*60}")

# Group by category
from collections import Counter
cat_counts = Counter(c["category"] for c in changes_log)
for cat, count in sorted(cat_counts.items()):
    print(f"  {cat}: {count} changes")

print(f"\nDetailed Changes:")
print(f"{'='*60}")
for c in changes_log:
    print(f"  [{c['category']}] {c['file']}:{c['line']}")
    print(f"    OLD: {c['old']}")
    print(f"    NEW: {c['new']}")
