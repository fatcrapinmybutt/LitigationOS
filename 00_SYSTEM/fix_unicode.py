"""Replace all non-cp1252-safe Unicode in consolidate_drives.py with ASCII equivalents."""
import re

path = r"D:\LitigationOS_tmp\consolidate_drives.py"

REPLACEMENTS = {
    "\u2713": "[OK]",    # ✓
    "\u2717": "[FAIL]",  # ✗
    "\u2500": "-",       # ─ (box drawing)
    "\u2502": "|",       # │
    "\u250c": "+",       # ┌
    "\u2510": "+",       # ┐
    "\u2514": "+",       # └
    "\u2518": "+",       # ┘
    "\u251c": "+",       # ├
    "\u2524": "+",       # ┤
    "\u252c": "+",       # ┬
    "\u2534": "+",       # ┴
    "\u253c": "+",       # ┼
    "\u2014": "--",      # — (em dash)
    "\u2013": "-",       # – (en dash)
    "\u00d7": "x",       # × (multiplication sign)
    "\u2192": "->",      # →
    "\u2190": "<-",      # ←
    "\u2026": "...",     # …
    "\u2022": "*",       # •
    "\u25cf": "*",       # ●
    "\u25a0": "#",       # ■
    "\u2588": "#",       # █
    "\u2591": ".",       # ░
    "\u2592": "=",       # ▒
    "\u2593": "#",       # ▓
}

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

original = content
count = 0
for old, new in REPLACEMENTS.items():
    n = content.count(old)
    if n > 0:
        content = content.replace(old, new)
        count += n
        print(f"  Replaced {repr(old)} -> {repr(new)}  ({n} occurrences)")

# Catch any remaining non-ASCII that cp1252 can't handle
remaining = []
for i, ch in enumerate(content):
    if ord(ch) > 127:
        try:
            ch.encode("cp1252")
        except UnicodeEncodeError:
            remaining.append((i, ch, hex(ord(ch))))

if remaining:
    print(f"\n  WARNING: {len(remaining)} remaining non-cp1252 chars:")
    for idx, ch, code in remaining[:20]:
        line = content[:idx].count("\n") + 1
        print(f"    Line {line}: {code} {repr(ch)}")
    # Replace remaining with '?'
    chars = list(content)
    for idx, ch, code in remaining:
        chars[idx] = "?"
    content = "".join(chars)
    count += len(remaining)
    print(f"  Replaced {len(remaining)} remaining chars with '?'")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nDone: {count} total replacements")
