"""Deep check — what are the actual method/ID names used."""
SRC = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
content = open(SRC, "r", encoding="utf-8").read()
lines = content.split('\n')

# Check bandit optimizer methods
print("=== BanditOptimizer methods ===")
for i, l in enumerate(lines, 1):
    if 'banditOptimizer.' in l:
        print(f"  L{i}: {l.strip()[:120]}")

# Check transitioner methods  
print("\n=== AnimatedTransitioner methods ===")
for i, l in enumerate(lines, 1):
    if 'transitioner.' in l:
        print(f"  L{i}: {l.strip()[:120]}")

# Check keyboard handler section (look for keydown)
print("\n=== Keyboard handlers (O/P/Q) ===")
for i, l in enumerate(lines, 1):
    ls = l.strip().lower()
    if "'o'" in ls or "'p'" in ls or "'q'" in ls:
        if 'key' in ls or 'case' in ls or '===' in ls:
            print(f"  L{i}: {l.strip()[:120]}")

# Check canvas/HUD element IDs
print("\n=== HUD canvas elements ===")
for i, l in enumerate(lines, 1):
    if 'canvas' in l.lower() and ('id=' in l.lower() or 'getElementById' in l.lower()):
        print(f"  L{i}: {l.strip()[:120]}")

# Check for quality/gauge/sparkline/LED references  
print("\n=== Quality HUD refs ===")
for i, l in enumerate(lines, 1):
    ls = l.lower()
    if any(k in ls for k in ['gauge', 'sparkline', 'convergence', 'banditstats', 'quality-']):
        print(f"  L{i}: {l.strip()[:120]}")

# Check _selfevolveTickHook content
print("\n=== _selfevolveTickHook ===")
in_hook = False
for i, l in enumerate(lines, 1):
    if '_selfevolveTickHook' in l:
        in_hook = True
        print(f"  L{i}: {l.strip()[:120]}")
    elif in_hook and l.strip():
        print(f"  L{i}: {l.strip()[:120]}")
        if l.strip().startswith('}') and not l.strip().startswith('});'):
            in_hook = False
