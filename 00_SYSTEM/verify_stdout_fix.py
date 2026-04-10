"""Verify ALL stdout contamination is fixed across engine files.

Checks for:
1. Module-level sys.stdout = open(...) — DANGEROUS (corrupts on import)
2. Bare sys.stdout.reconfigure(...) without try/except
3. main()-block sys.stdout = open(...) without try/except
"""
import re
from pathlib import Path

ENGINES = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines")

# Pattern A: sys.stdout = open(sys.stdout.fileno(), ...)
PAT_OPEN = re.compile(r'sys\.stdout\s*=\s*open\(sys\.stdout\.fileno\(\)')
# Pattern B: sys.stdout.reconfigure(encoding=...)
PAT_RECONF = re.compile(r'sys\.stdout\.reconfigure\(')

issues = []
safe = 0

for py_file in sorted(ENGINES.rglob("*.py")):
    text = py_file.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check Pattern A: sys.stdout = open(...)
        if PAT_OPEN.search(stripped):
            # Check if it's inside a try block (look at preceding lines)
            in_try = False
            for j in range(max(0, i-4), i-1):
                if "try:" in lines[j]:
                    in_try = True
                    break
            if not in_try:
                # Check if it's at module level (no indentation) 
                indent = len(line) - len(line.lstrip())
                level = "MODULE-LEVEL" if indent == 0 else f"indent={indent}"
                issues.append((py_file.relative_to(ENGINES), i, level, "sys.stdout = open(...)"))
            else:
                safe += 1
                
        # Check Pattern B: sys.stdout.reconfigure(...)
        if PAT_RECONF.search(stripped):
            in_try = False
            for j in range(max(0, i-4), i-1):
                if "try:" in lines[j]:
                    in_try = True
                    break
            if not in_try:
                indent = len(line) - len(line.lstrip())
                level = "MODULE-LEVEL" if indent == 0 else f"indent={indent}"
                issues.append((py_file.relative_to(ENGINES), i, level, "sys.stdout.reconfigure(...)"))
            else:
                safe += 1

print(f"=== STDOUT CONTAMINATION AUDIT ===")
print(f"Files scanned: {len(list(ENGINES.rglob('*.py')))}")
print(f"Safe (wrapped in try/except): {safe}")
print(f"ISSUES FOUND: {len(issues)}")
print()

if issues:
    for path, line, level, pattern in issues:
        severity = "🔴 CRITICAL" if level == "MODULE-LEVEL" else "🟡 WARNING"
        print(f"  {severity} {path}:{line} [{level}] — {pattern}")
else:
    print("  ✅ ALL CLEAR — Zero unprotected stdout contamination!")
