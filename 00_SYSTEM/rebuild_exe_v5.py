"""
THEMANBEARPIG v5 EXE Rebuild Script
Downloads D3.js, inlines it, creates pywebview launcher, generates icon, runs PyInstaller.
"""
import os, sys, subprocess, hashlib, struct, zlib

BUILD_DIR = r"D:\LitigationOS_tmp\blueprint_build"
HTML_PATH = os.path.join(BUILD_DIR, "blueprint.html")
LAUNCHER_PATH = os.path.join(BUILD_DIR, "adversary_blueprint.py")
ICON_PATH = os.path.join(BUILD_DIR, "blueprint.ico")
SPEC_PATH = os.path.join(BUILD_DIR, "THEMANBEARPIG.spec")
DESKTOP = os.path.expanduser(r"~\Desktop")
EXE_OUT = os.path.join(DESKTOP, "THEMANBEARPIG.exe")

# ─── Step 1: Download D3.js and inline it ───
print("[1/5] Inlining D3.js for offline use...")
import urllib.request
d3_urls = [
    "https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
    "https://unpkg.com/d3@7/dist/d3.min.js",
]
d3_cache = os.path.join(BUILD_DIR, "d3.v7.min.js")
if not os.path.exists(d3_cache) or os.path.getsize(d3_cache) < 100000:
    for url in d3_urls:
        try:
            print(f"      Trying {url.split('/')[2]}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                open(d3_cache, "wb").write(data)
                print(f"      Downloaded: {len(data):,} bytes")
                break
        except Exception as e:
            print(f"      Failed: {e}")
    else:
        print("      ❌ All CDN sources failed")
        sys.exit(1)
else:
    print(f"      Using cached D3.js: {os.path.getsize(d3_cache):,} bytes")

d3_code = open(d3_cache, "r", encoding="utf-8").read()

# Read HTML and replace CDN script tag with inline
html = open(HTML_PATH, "r", encoding="utf-8").read()
cdn_tag = '<script src="https://d3js.org/d3.v7.min.js"></script>'
if cdn_tag in html:
    inline_tag = f'<script>{d3_code}</script>'
    html = html.replace(cdn_tag, inline_tag)
    open(HTML_PATH, "w", encoding="utf-8").write(html)
    print(f"      Inlined D3.js ({len(d3_code):,} chars) into HTML")
else:
    print("      D3.js already inlined or tag not found")

print(f"      Final HTML size: {os.path.getsize(HTML_PATH):,} bytes")

# ─── Step 2: Create pywebview launcher ───
print("[2/5] Creating pywebview launcher...")
launcher_code = '''"""THEMANBEARPIG v5 — Adversary Intelligence Blueprint"""
import webview, sys, os

def get_html_path():
    if getattr(sys, '_MEIPASS', None):
        return os.path.join(sys._MEIPASS, 'blueprint.html')
    return os.path.join(os.path.dirname(__file__), 'blueprint.html')

if __name__ == '__main__':
    html_path = get_html_path()
    if not os.path.exists(html_path):
        print(f"ERROR: {html_path} not found")
        sys.exit(1)
    window = webview.create_window(
        'THEMANBEARPIG v5 — Adversary Intelligence Blueprint',
        html_path,
        width=1600,
        height=1000,
        resizable=True,
        min_size=(800, 600),
        background_color='#0a0a1a',
        text_select=True,
    )
    webview.start(gui='edgechromium', debug=False)
'''
open(LAUNCHER_PATH, "w", encoding="utf-8").write(launcher_code)
print("      ✓ adversary_blueprint.py created")

# ─── Step 3: Generate .ico file ───
print("[3/5] Generating blueprint.ico...")

def create_ico(path, size=64):
    """Create a simple 64x64 ICO with MBP colors (cyan/magenta gradient)."""
    w = h = size
    pixels = []
    for y in range(h):
        row = []
        for x in range(w):
            cx, cy = x - w//2, y - h//2
            dist = (cx*cx + cy*cy) ** 0.5
            max_r = w // 2
            if dist < max_r - 2:
                t = dist / max_r
                r = int(0 + 255 * t)
                g = int(255 * (1 - t) * 0.8)
                b = int(255 * (1 - t * 0.3))
                a = 255
            elif dist < max_r:
                r, g, b, a = 0, 255, 255, 200
            else:
                r, g, b, a = 0, 0, 0, 0
            row.append((b, g, r, a))
        pixels.append(row)

    # Build BMP data (BGRA, bottom-up)
    bmp_data = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            b, g, r, a = pixels[y][x]
            bmp_data.extend([b, g, r, a])

    # AND mask (1-bit, all zeros = fully visible)
    and_row_bytes = (w + 31) // 32 * 4
    and_mask = bytearray(and_row_bytes * h)

    # BITMAPINFOHEADER (40 bytes)
    bih = struct.pack('<IiiHHIIiiII',
        40,         # biSize
        w,          # biWidth
        h * 2,      # biHeight (XOR + AND)
        1,          # biPlanes
        32,         # biBitCount
        0,          # biCompression
        len(bmp_data) + len(and_mask),
        0, 0, 0, 0
    )
    image_data = bih + bytes(bmp_data) + bytes(and_mask)

    # ICO header
    ico_header = struct.pack('<HHH', 0, 1, 1)  # reserved, type=1(ICO), count=1
    entry = struct.pack('<BBBBHHII',
        w if w < 256 else 0,
        h if h < 256 else 0,
        0, 0,   # palette, reserved
        1,      # planes
        32,     # bpp
        len(image_data),
        22      # offset (6 header + 16 entry)
    )

    with open(path, 'wb') as f:
        f.write(ico_header + entry + image_data)

create_ico(ICON_PATH)
print(f"      ✓ blueprint.ico created ({os.path.getsize(ICON_PATH):,} bytes)")

# ─── Step 4: Run PyInstaller ───
print("[4/5] Running PyInstaller (this takes 30-60 seconds)...")
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "THEMANBEARPIG",
    "--icon", ICON_PATH,
    "--add-data", f"{HTML_PATH};.",
    "--distpath", DESKTOP,
    "--workpath", os.path.join(BUILD_DIR, "build"),
    "--specpath", BUILD_DIR,
    "--clean",
    "-y",
    LAUNCHER_PATH,
]
result = subprocess.run(cmd, capture_output=True, text=True, cwd=BUILD_DIR, timeout=300)
if result.returncode != 0:
    print("      ❌ PyInstaller FAILED")
    # Show last 30 lines of stderr
    lines = result.stderr.strip().split('\n')
    for line in lines[-30:]:
        print(f"      {line}")
    sys.exit(1)

# ─── Step 5: Verify ───
print("[5/5] Verifying output...")
if os.path.exists(EXE_OUT):
    size_mb = os.path.getsize(EXE_OUT) / (1024 * 1024)
    print(f"""
══════════════════════════════════════════════════
  ✅ THEMANBEARPIG v5 EXE BUILT SUCCESSFULLY
  📁 {EXE_OUT}
  📊 Size: {size_mb:.1f} MB
  🚀 Double-click to launch!
══════════════════════════════════════════════════""")
else:
    print("      ❌ EXE not found at expected location")
    # Check if it's in dist/ instead
    dist_exe = os.path.join(BUILD_DIR, "dist", "THEMANBEARPIG.exe")
    if os.path.exists(dist_exe):
        import shutil
        shutil.copy2(dist_exe, EXE_OUT)
        size_mb = os.path.getsize(EXE_OUT) / (1024 * 1024)
        print(f"      Found in dist/, copied to Desktop: {size_mb:.1f} MB")
