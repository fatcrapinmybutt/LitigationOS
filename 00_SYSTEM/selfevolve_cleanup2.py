"""Cleanup: Replace remaining forceOptimizer refs with heatmap."""
import re

SRC = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
content = open(SRC, "r", encoding="utf-8").read()

fixes = [
    (r"forceOptimizer\.recordInteraction\('zoom_in'[^)]+\);",
     "heatmap.record(W/2, H/2, 'zoom_in', 1);"),
    (r"forceOptimizer\.recordInteraction\('zoom_out'[^)]+\);",
     "heatmap.record(W/2, H/2, 'zoom_out', 1);"),
    (r"forceOptimizer\.recordInteraction\('click'[^)]+\);",
     "heatmap.record(W/2, H/2, 'click', 2);"),
    (r"forceOptimizer\.recordInteraction\('drag_end'[^)]+\);",
     "heatmap.record(W/2, H/2, 'drag_end', 1.5);"),
    (r"forceOptimizer\.recordInteraction\('drag_start'[^)]+\);",
     "heatmap.record(W/2, H/2, 'drag_start', 1.5);"),
    (r"forceOptimizer\.recordInteraction\('layer_toggle'[^)]+\);",
     "heatmap.record(W/2, H/2, 'layer_toggle', 1);"),
]

fixed = 0
for pattern, replacement in fixes:
    matches = re.findall(pattern, content)
    if matches:
        print(f"Fixing {len(matches)}x: {pattern[:50]}...")
        content = re.sub(pattern, replacement, content)
        fixed += len(matches)

# Write FIRST
with open(SRC, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Written: {len(content):,} chars, fixed {fixed} refs")

# Verify
remaining = [f"  L{i}: {l.strip()[:100]}" for i, l in enumerate(content.split('\n'), 1) if "forceOptimizer" in l]
if remaining:
    print(f"STILL remaining: {len(remaining)}")
    for r in remaining:
        print(r)
else:
    print("CLEAN: Zero forceOptimizer references remain")
