"""Scan ALL cortex .py files for non-ASCII chars."""
import re, os
os.environ["PYTHONUTF8"] = "1"

replacements = {
    "\u2192": "->", "\u2014": "--", "\u2500": "-", "\u2502": "|",
    "\u2551": "||", "\u2554": "+", "\u2557": "+", "\u255a": "+",
    "\u255d": "+", "\u2550": "=", "\u250c": "+", "\u2510": "+",
    "\u2514": "+", "\u2518": "+", "\u2503": "|", "\u2501": "-",
}

for fname in ["cortex_schema.py", "cortex_brain.py"]:
    fp = os.path.join(r"J:\CORTEX", fname)
    if not os.path.exists(fp):
        continue
    with open(fp, "r", encoding="utf-8") as f:
        lines = f.readlines()
    changed = 0
    new_lines = []
    for i, line in enumerate(lines):
        orig = line
        for old, new in replacements.items():
            line = line.replace(old, new)
        line = re.sub(r'[\U00000250-\U0000FFFF]', '', line)
        line = re.sub(r'[\U00010000-\U0010FFFF]', '', line)
        if line != orig:
            changed += 1
            print(f"  {fname} line {i+1}: fixed")
        new_lines.append(line)
    if changed:
        with open(fp, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Fixed {changed} lines in {fname}\n")
    else:
        print(f"No changes: {fname}")
