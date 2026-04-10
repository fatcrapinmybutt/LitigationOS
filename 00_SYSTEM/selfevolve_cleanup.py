"""Cleanup: Replace remaining forceOptimizer refs with heatmap."""
import re

SRC = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
content = open(SRC, "r", encoding="utf-8").read()

# Find and show the exact lines for verification
lines = content.split('\n')
for i in [1130, 1131, 1132, 1193, 1194, 1450, 1451]:
    if i < len(lines):
        print(f"L{i+1}: {lines[i].strip()[:120]}")

# Replace all remaining forceOptimizer references
fixes = [
    # Zoom in recording
    (r"forceOptimizer\.recordInteraction\('zoom_in'[^)]+\);",
     "heatmap.record(W/2, H/2, 'zoom_in', 1);"),
    # Zoom out recording
    (r"forceOptimizer\.recordInteraction\('zoom_out'[^)]+\);",
     "heatmap.record(W/2, H/2, 'zoom_out', 1);"),
    # Click recording
    (r"forceOptimizer\.recordInteraction\('click'[^)]+\);",
     "heatmap.record(W/2, H/2, 'click', 2);"),
    # Drag end recording
    (r"forceOptimizer\.recordInteraction\('drag_end'[^)]+\);",
     "heatmap.record(W/2, H/2, 'drag_end', 1.5);"),
    # Drag start recording
    (r"forceOptimizer\.recordInteraction\('drag_start'[^)]+\);",
     "heatmap.record(W/2, H/2, 'drag_start', 1.5);"),
    # Layer toggle recording
    (r"forceOptimizer\.recordInteraction\('layer_toggle'[^)]+\);",
     "heatmap.record(W/2, H/2, 'layer_toggle', 1);"),
]

fixed = 0
for pattern, replacement in fixes:
    matches = re.findall(pattern, content)
    if matches:
        print(f"\nFixing {len(matches)}x: {pattern[:60]}")
        for m in matches:
            print(f"  was: {m[:90]}")
        content = re.sub(pattern, replacement, content)
        fixed += len(matches)

# Verify no remaining forceOptimizer refs
remaining = []
for i, line in enumerate(content.split('\n'), 1):
    if "forceOptimizer" in line:
        remaining.append(f"  L{i}: {line.strip()[:100]}")

if remaining:
    print(f"\nSTILL remaining: {len(remaining)}")
    for r in remaining:
        print(r)
else:
    print(f"\n✓ Clean: Zero forceOptimizer references remain")

print(f"\nFixed {fixed} references")

with open(SRC, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Written: {len(content):,} chars")
