"""Scan and fix non-ASCII chars in cortex_hunt.py."""
import re, sys, os
os.environ["PYTHONUTF8"] = "1"

fp = r"J:\CORTEX\cortex_hunt.py"
with open(fp, "r", encoding="utf-8") as f:
    lines = f.readlines()

replacements = {
    "\u2192": "->",   # right arrow
    "\u2014": "--",    # em dash
    "\u2500": "-",     # box drawing
    "\u2502": "|",     # box drawing vertical
    "\u2551": "||",    # double vertical
    "\u2554": "+",     # box corner
    "\u2557": "+",     # box corner
    "\u255a": "+",     # box corner
    "\u255d": "+",     # box corner
    "\u2550": "=",     # double horizontal
    "\u250c": "+",     # light box corner
    "\u2510": "+",     # light box corner
    "\u2514": "+",     # light box corner
    "\u2518": "+",     # light box corner
    "\u2503": "|",     # heavy vertical
    "\u2501": "-",     # heavy horizontal
}

changed = 0
new_lines = []
for i, line in enumerate(lines):
    orig = line
    # Replace known non-ASCII
    for old, new in replacements.items():
        line = line.replace(old, new)
    # Strip any remaining emoji (above U+024F)
    line = re.sub(r'[\U00000250-\U0000FFFF]', '', line)
    # Strip Unicode emoji in supplementary planes
    line = re.sub(r'[\U00010000-\U0010FFFF]', '', line)
    if line != orig:
        changed += 1
        print(f"  Line {i+1}: fixed")
    new_lines.append(line)

if changed > 0:
    with open(fp, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"\nFixed {changed} lines in {fp}")
else:
    print(f"\nNo changes needed in {fp}")
