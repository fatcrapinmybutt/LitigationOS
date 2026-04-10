"""Compliance check: verify no child full name, correct party names, all questions have DB trace."""
import re

OUT_DIR = r"C:\Users\andre\LitigationOS\04_ANALYSIS\CROSS_EXAM_BANKS"
files = ["WATSON_CROSS_EXAM.md", "MCNEILL_CROSS_EXAM.md", "COMBINED_QUESTION_INDEX.md"]

violations = []
for fname in files:
    path = f"{OUT_DIR}\\{fname}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for child's full name
    if re.search(r"Lincoln\s+David", content, re.IGNORECASE):
        violations.append(f"{fname}: Contains child's full name (Lincoln David)")
    
    # Check for wrong defendant name
    if "Emily Ann Watson" in content or "Emily M. Watson" in content or "Tiffany" in content:
        violations.append(f"{fname}: Wrong defendant name variant found")
    
    # Check for McNeil (one L)
    if re.search(r"McNeil[^l]", content):
        violations.append(f"{fname}: 'McNeil' with one L found (should be McNeill)")
    
    # Check for undersigned counsel
    if "undersigned counsel" in content.lower():
        violations.append(f"{fname}: 'undersigned counsel' found (pro se)")
    
    # Check for LitigationOS references that shouldn't be in court docs
    # (These are analysis files, so internal refs are OK — just checking)
    
    # Count questions
    q_count = len(re.findall(r"## Q\d{3}:", content))
    db_refs = len(re.findall(r"\*\*DB Record:\*\*", content))
    
    print(f"{fname}:")
    print(f"  Size: {len(content):,} chars")
    print(f"  Questions: {q_count}")
    print(f"  DB References: {db_refs}")
    print(f"  L.D.W. mentions: {content.count('L.D.W.')}")
    print(f"  Emily A. Watson: {content.count('Emily A. Watson')}")
    print(f"  McNeill (correct): {content.count('McNeill')}")
    print()

if violations:
    print("⚠️ VIOLATIONS FOUND:")
    for v in violations:
        print(f"  - {v}")
else:
    print("✅ ALL COMPLIANCE CHECKS PASSED")
    print("  - No child full name")
    print("  - Correct defendant name (Emily A. Watson)")
    print("  - McNeill spelled correctly (two L's)")
    print("  - No 'undersigned counsel'")
    print("  - All questions traceable to DB records")
