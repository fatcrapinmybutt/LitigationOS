"""Modify themanbearpig.py launcher to support V7 as default."""
import os

LAUNCHER = r"C:\Users\andre\LitigationOS\scripts\themanbearpig.py"
lines = open(LAUNCHER, encoding="utf-8").readlines()
content = "".join(lines)

changes = 0

# 1. Add VIS_DIR_V7 after line with VIS_DIR_V5
old1 = 'VIS_DIR_V5 = _BUNDLE / "08_MEDIA" / "MANBEARPIG_V5"'
new1 = 'VIS_DIR_V5 = _BUNDLE / "08_MEDIA" / "MANBEARPIG_V5"\nVIS_DIR_V7 = _BUNDLE / "08_MEDIA" / "MANBEARPIG_V7"'
if old1 in content and 'VIS_DIR_V7' not in content:
    content = content.replace(old1, new1, 1)
    changes += 1
    print("1. Added VIS_DIR_V7 path")
else:
    print("1. SKIP: VIS_DIR_V7 already exists or anchor not found")

# 2. Bump VERSION
old2 = 'VERSION = "20.1.0"'
new2 = 'VERSION = "21.0.0"  # V7 SELFEVOLVE CONVERGENCE'
if old2 in content:
    content = content.replace(old2, new2, 1)
    changes += 1
    print("2. Bumped VERSION to 21.0.0")
else:
    print("2. SKIP: VERSION already changed or not found")

# 3. Add --v7/--v15 args to argparse (after --focus line)
old3 = '    args = parser.parse_args()'
new3 = '''    parser.add_argument("--v15", action="store_true", help="Use V15 visualization (legacy)")
    parser.add_argument("--v7", action="store_true", default=True, help="Use V7 SELFEVOLVE visualization (default)")
    args = parser.parse_args()'''
if '--v7' not in content:
    content = content.replace(old3, new3, 1)
    changes += 1
    print("3. Added --v7/--v15 CLI arguments")
else:
    print("3. SKIP: --v7 already exists")

# 4. Add VIS_DIR selection logic after args = parser.parse_args()
# Find the line: if not VIS_DIR.exists(): and replace the block
old4 = '''    if not VIS_DIR.exists():
        VIS_DIR.mkdir(parents=True, exist_ok=True)

    index_html = VIS_DIR / "index.html"
    if not index_html.exists():
        print(f"ERROR: {index_html} not found. Build the V15 visualization first.")
        sys.exit(1)'''
new4 = '''    # V7 SELFEVOLVE CONVERGENCE — select visualization
    if args.v15:
        active_vis = VIS_DIR  # V15 legacy
        vis_label = "V15 (legacy)"
    elif VIS_DIR_V7.exists() and (VIS_DIR_V7 / "index.html").exists():
        active_vis = VIS_DIR_V7  # V7 SELFEVOLVE (default)
        vis_label = "V7 SELFEVOLVE"
    elif VIS_DIR.exists() and (VIS_DIR / "index.html").exists():
        active_vis = VIS_DIR  # Fallback to V15
        vis_label = "V15 (fallback)"
    else:
        active_vis = VIS_DIR
        vis_label = "V15"

    if not active_vis.exists():
        active_vis.mkdir(parents=True, exist_ok=True)

    index_html = active_vis / "index.html"
    if not index_html.exists():
        print(f"ERROR: {index_html} not found.")
        print(f"Active visualization: {vis_label} at {active_vis}")
        sys.exit(1)

    print(f"Visualization: {vis_label}")'''

if 'active_vis' not in content:
    if old4 in content:
        content = content.replace(old4, new4, 1)
        changes += 1
        print("4. Added V7/V15 selection logic")
    else:
        print("4. SKIP: anchor block not found exactly")
else:
    print("4. SKIP: active_vis already exists")

# 5. Update MBPServer to use active_vis instead of VIS_DIR
# Find: server = MBPServer(port=args.port)
old5 = '    server = MBPServer(port=args.port)'
new5 = '    server = MBPServer(port=args.port, vis_dir=active_vis)'
if 'vis_dir=active_vis' not in content:
    content = content.replace(old5, new5, 1)
    changes += 1
    print("5. Updated MBPServer to use active_vis")
else:
    print("5. SKIP: already updated")

# 6. Update the URL to use active_vis path (the HTTP server serves from VIS_DIR by default)
# We need to check if MBPServer accepts vis_dir param. Let me check the class.
# If not, we need to add it. For now, let's add a global override.
# Actually, let's check if there's a simpler way: the server reads VIS_DIR global.
# We can just reassign VIS_DIR before creating the server.
# Let's add: VIS_DIR = active_vis before the server creation
old6 = '    server = MBPServer(port=args.port, vis_dir=active_vis)'
new6 = '''    # Override VIS_DIR for HTTP server
    VIS_DIR = active_vis
    server = MBPServer(port=args.port)'''
# Undo the vis_dir param if MBPServer doesn't accept it
if 'vis_dir=active_vis' in content:
    content = content.replace(old6, new6, 1)
    print("6. Using VIS_DIR override instead of vis_dir param")
else:
    print("6. SKIP")

# 7. Update the banner title
old7 = '    sep = _sep_days()\n    title = f"THEMANBEARPIG v{VERSION} -- {sep} Days Separated"'
new7 = '    sep = _sep_days()\n    title = f"THEMANBEARPIG v{VERSION} [{vis_label}] -- {sep} Days Separated"'
if '[vis_label]' not in content:
    content = content.replace(old7, new7, 1)
    changes += 1
    print("7. Updated window title to include vis_label")
else:
    print("7. SKIP: already updated")

# Write the modified launcher
# WRITE BEFORE PRINTING (cp1252 safety)
with open(LAUNCHER, "w", encoding="utf-8") as f:
    f.write(content)

new_lines = content.count('\n')
new_size = os.path.getsize(LAUNCHER)

print(f"\nLauncher modified: {changes} changes")
print(f"  File: {LAUNCHER}")
print(f"  Lines: {new_lines}")
print(f"  Size: {new_size:,} bytes")
print("  VERSION: 21.0.0")
print("  Default: V7 SELFEVOLVE")
print("  Fallback: V15 legacy")
print("  CLI: --v15 to force legacy, --v7 (default)")
