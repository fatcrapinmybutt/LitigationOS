"""Final integrity check on THEMANBEARPIG v7 APEX SELFEVOLVE."""
import re

SRC = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
content = open(SRC, "r", encoding="utf-8").read()
lines = content.split('\n')

print(f"File: {len(content):,} chars, {len(lines)} lines")

# 1. Check all class definitions exist
classes = ['GraphQualityEngine', 'BanditOptimizer', 'AnimatedTransitioner',
           'InteractionHeatmap', 'PluginManager', 'ConfigPresetManager', 'BuildVersionTracker']
for cls in classes:
    if f'class {cls}' in content:
        print(f"  [OK] class {cls}")
    else:
        print(f"  [MISSING] class {cls}")

# 2. Check all instances exist
instances = ['qualityEngine', 'banditOptimizer', 'transitioner', 'heatmap',
             'pluginManager', 'presetManager', 'buildTracker']
for inst in instances:
    pattern = rf'(const|let|var)\s+{inst}\s*='
    if re.search(pattern, content):
        print(f"  [OK] instance {inst}")
    else:
        print(f"  [MISSING] instance {inst}")

# 3. Check for any undefined references (old names that were removed)
old_names = ['forceOptimizer', 'AdaptiveForceOptimizer', 'configLearner']
for name in old_names:
    count = content.count(name)
    if count > 0:
        print(f"  [BAD] {name} appears {count}x (should be 0)")
        for i, line in enumerate(lines, 1):
            if name in line:
                print(f"    L{i}: {line.strip()[:100]}")
    else:
        print(f"  [OK] {name} = 0 refs (clean)")

# 4. Check key hooks are wired
hooks = ['_selfevolveTickHook', 'qualityEngine.measure', 'banditOptimizer.pull',
         'transitioner.apply', 'heatmap.record']
for hook in hooks:
    count = content.count(hook)
    print(f"  {'[OK]' if count > 0 else '[MISSING]'} {hook} ({count}x)")

# 5. Check keyboard handlers exist
kbd_checks = [("case 'o':", "UCB1 bandit"), ("case 'p':", "preset cycle"),
              ("case 'q':", "quality report")]
for pattern, desc in kbd_checks:
    if pattern in content.lower() or pattern in content:
        print(f"  [OK] Key {desc}")
    else:
        # Try case-insensitive
        if pattern.replace("'", '"') in content:
            print(f"  [OK] Key {desc} (double-quote)")
        else:
            print(f"  [CHECK] Key {desc} - verify manually")

# 6. Check HUD elements
hud_checks = ['qualGauge', 'qualSparkline', 'convergenceLed', 'banditStats']
for hud in hud_checks:
    count = content.count(hud)
    print(f"  {'[OK]' if count > 0 else '[MISSING]'} HUD: {hud} ({count}x)")

# 7. Verify sim tick hook is wired
if "pluginManager.emit('afterForce'); _selfevolveTickHook();" in content:
    print("  [OK] Sim tick hook wired")
elif "_selfevolveTickHook" in content:
    print("  [OK] _selfevolveTickHook exists (check wiring)")
else:
    print("  [MISSING] _selfevolveTickHook")

# 8. Check for basic JS syntax issues (unmatched braces in classes)
for cls in classes:
    match = re.search(rf'class {cls}\s*\{{', content)
    if match:
        start = match.start()
        depth = 0
        for i, c in enumerate(content[start:start+10000]):
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            if depth == 0:
                print(f"  [OK] {cls} braces balanced (len={i})")
                break
        else:
            print(f"  [BAD] {cls} braces NOT balanced in 10K chars")

print("\nIntegrity check complete.")
