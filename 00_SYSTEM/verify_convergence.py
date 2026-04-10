"""Final verification of Full Convergence integration."""
import os

# 1. V7 HTML with bridge
v7_src = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
v7_exe = r"C:\Users\andre\LitigationOS\08_MEDIA\MANBEARPIG_V7\index.html"

src_text = open(v7_src, encoding="utf-8").read()
exe_text = open(v7_exe, encoding="utf-8").read()

checks = []

# V7 SELFEVOLVE classes
for cls in ['GraphQualityEngine', 'BanditOptimizer', 'AnimatedTransitioner',
            'InteractionHeatmap', 'PluginManager', 'ConfigPresetManager', 'BuildVersionTracker']:
    found = f'class {cls}' in src_text
    checks.append(('V7 SELFEVOLVE: ' + cls, found))

# Bridge code
for term in ['MBP.Backend', 'MBP.Palette', 'MBP.Results', 'MBP.StatusBar',
             'window.pywebview', 'Ctrl+K', 'mbp-command-palette', 'mbp-results-panel',
             'mbp-status-bar', 'MBP.call']:
    found = term in src_text
    checks.append(('Bridge: ' + term, found))

# EXE copy matches source
checks.append(('EXE copy matches source', src_text == exe_text))

# 2. Launcher changes
launcher = open(r"C:\Users\andre\LitigationOS\scripts\themanbearpig.py", encoding="utf-8").read()
for term in ['VIS_DIR_V7', 'VERSION = "21.0.0"', '--v15', '--v7', 'active_vis', 'vis_label']:
    checks.append(('Launcher: ' + term, term in launcher))

# 3. Build script
build = open(r"C:\Users\andre\LitigationOS\scripts\mbp_build.py", encoding="utf-8").read()
for term in ['MANBEARPIG_V7', 'V7 SELFEVOLVE visualization']:
    checks.append(('Build: ' + term, term in build))

# 4. File sizes
files = {
    'V7 HTML (source)': v7_src,
    'V7 HTML (EXE copy)': v7_exe,
    'Launcher': r"C:\Users\andre\LitigationOS\scripts\themanbearpig.py",
    'Build script': r"C:\Users\andre\LitigationOS\scripts\mbp_build.py",
}

# Print results
print("FULL CONVERGENCE VERIFICATION")
print("=" * 55)
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
for label, ok in checks:
    status = "OK" if ok else "FAIL"
    print(f"  [{status:4s}] {label}")

print(f"\n  {passed}/{total} checks passed")

print("\nFile Sizes:")
for label, path in files.items():
    sz = os.path.getsize(path)
    print(f"  {label}: {sz:,} bytes ({sz/1024:.0f} KB)")

# Count bridge features
api_count = src_text.count("MBP.Backend.")
cmd_count = src_text.count("'cmd':")
print(f"\nBridge Statistics:")
print(f"  MBP.Backend.* calls: {api_count}")
print(f"  Command palette commands: {cmd_count}")
print(f"  Graceful degradation: {'YES' if 'window.pywebview' in src_text else 'NO'}")
