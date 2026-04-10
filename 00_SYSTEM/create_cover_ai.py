"""
CORTEX AI-Generated Cover Image — Uses Pollinations.ai (free, no API key).
Generates a stunning product cover, then composites CORTEX branding on top with Pillow.
"""
import urllib.request
import urllib.parse
import os
import sys
import time

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

OUT_DIR = r"J:\CORTEX\gumroad_packages\covers"
os.makedirs(OUT_DIR, exist_ok=True)

# --- Step 1: Generate AI background via Pollinations.ai ---
PROMPT = (
    "dark futuristic intelligence dashboard visualization, "
    "glowing cyan and electric blue neural network graph nodes connected by luminous edges, "
    "holographic data streams flowing through a dark void, "
    "abstract technology art, deep black background with subtle purple nebula, "
    "cinematic lighting, ultra detailed, 8k render, no text no words no letters no watermarks"
)

WIDTH, HEIGHT = 1280, 720

def download_ai_image(prompt, width, height, output_path, seed=None):
    """Download AI-generated image from Pollinations.ai (free, no API key)."""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
    if seed:
        url += f"&seed={seed}"
    
    print(f"Requesting AI image generation...")
    print(f"URL length: {len(url)} chars")
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "CORTEX-CoverGen/1.0"
    })
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"  Attempt {attempt+1}/{max_retries}...")
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                with open(output_path, "wb") as f:
                    f.write(data)
                print(f"  Downloaded: {len(data):,} bytes")
                return True
        except Exception as e:
            print(f"  Error: {e}")
            if attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
    return False


def draw_glow_text(draw, pos, text, font, color, glow_radius=8):
    """Draw text with a glow effect."""
    x, y = pos
    # Glow layers (progressively more transparent)
    for offset in range(glow_radius, 0, -2):
        alpha = int(60 * (1 - offset / glow_radius))
        glow_color = (*color[:3], alpha) if len(color) == 4 else (*color, alpha)
        for dx in range(-offset, offset+1, 2):
            for dy in range(-offset, offset+1, 2):
                try:
                    draw.text((x+dx, y+dy), text, font=font, fill=glow_color)
                except:
                    pass
    # Main text
    draw.text((x, y), text, font=font, fill=color)


def composite_branding(bg_path, output_path, variant="PRO"):
    """Overlay CORTEX branding onto AI-generated background."""
    img = Image.open(bg_path).convert("RGBA")
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    
    # Darken slightly for text readability
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.7)
    
    # Add dark gradient overlay at top and bottom for text areas
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    # Top gradient (for title)
    for y in range(200):
        alpha = int(180 * (1 - y / 200))
        draw_ov.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, alpha))
    
    # Bottom gradient (for features)
    for y in range(HEIGHT - 180, HEIGHT):
        alpha = int(200 * ((y - (HEIGHT - 180)) / 180))
        draw_ov.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, alpha))
    
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    def load_font(size, bold=False):
        candidates = [
            r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()
    
    title_font = load_font(72, bold=True)
    sub_font = load_font(22, bold=False)
    badge_font = load_font(18, bold=True)
    version_font = load_font(14, bold=False)
    feature_font = load_font(16, bold=True)
    
    # --- Title: "C O R T E X" with letter spacing and glow ---
    title = "C O R T E X"
    cyan = (0, 230, 255)
    
    # Measure title
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (WIDTH - tw) // 2
    ty = 45
    
    # Glow behind title
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    for r in range(20, 0, -1):
        a = int(15 * (1 - r / 20))
        for dx in range(-r, r+1, 3):
            for dy in range(-r, r+1, 3):
                glow_draw.text((tx+dx, ty+dy), title, font=title_font, fill=(0, 230, 255, a))
    img = Image.alpha_composite(img, glow_layer)
    draw = ImageDraw.Draw(img)
    
    # Main title text (white with cyan shadow)
    draw.text((tx+2, ty+2), title, font=title_font, fill=(0, 180, 220, 200))
    draw.text((tx, ty), title, font=title_font, fill=(255, 255, 255, 255))
    
    # --- Variant badge (PRO / BUNDLE) ---
    if variant == "PRO":
        badge_text = "PRO"
        badge_color = (0, 200, 255)
    else:
        badge_text = "COMPLETE BUNDLE"
        badge_color = (255, 180, 0)
    
    bbbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbbox[2] - bbbox[0]
    bx = (WIDTH + tw) // 2 + tx - (WIDTH - tw) // 2 + 15  # right of title
    bx = tx + tw + 20
    by = ty + 25
    
    # Badge background
    pad = 8
    draw.rounded_rectangle(
        [bx - pad, by - pad//2, bx + bw + pad, by + (bbbox[3]-bbbox[1]) + pad//2],
        radius=6, fill=(*badge_color, 180)
    )
    draw.text((bx, by), badge_text, font=badge_font, fill=(0, 0, 0, 255))
    
    # --- Tagline ---
    tagline = "Universal Intelligence Platform  |  55 Domain Packs  |  Autonomous Analysis"
    tag_bbox = draw.textbbox((0, 0), tagline, font=sub_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    draw.text(((WIDTH - tag_w) // 2, ty + 90), tagline, font=sub_font, fill=(180, 220, 255, 220))
    
    # --- Feature badges at bottom ---
    features = [
        ("OSINT", (0, 200, 255)),
        ("CYBER", (0, 255, 150)),
        ("FINANCIAL", (255, 200, 0)),
        ("LEGAL", (200, 150, 255)),
        ("CORPORATE", (255, 100, 100)),
        ("HEALTHCARE", (100, 255, 200)),
    ]
    
    total_width = len(features) * 140 + (len(features) - 1) * 15
    start_x = (WIDTH - total_width) // 2
    fy = HEIGHT - 65
    
    for i, (label, color) in enumerate(features):
        fx = start_x + i * 155
        # Pill background
        lbox = draw.textbbox((0, 0), label, font=feature_font)
        lw = lbox[2] - lbox[0]
        pill_w = max(lw + 30, 130)
        draw.rounded_rectangle(
            [fx, fy, fx + pill_w, fy + 32],
            radius=16, fill=(*color, 40), outline=(*color, 150), width=1
        )
        draw.text((fx + (pill_w - lw) // 2, fy + 6), label, font=feature_font, fill=(*color, 230))
    
    # --- Version tag ---
    ver = "v1.0.0"
    draw.text((WIDTH - 80, HEIGHT - 30), ver, font=version_font, fill=(120, 120, 140, 180))
    
    # --- Subtle "cortex.ai" watermark bottom-left ---
    draw.text((20, HEIGHT - 30), "cortex-intelligence.com", font=version_font, fill=(100, 100, 120, 150))
    
    # Save final
    final = img.convert("RGB")
    final.save(output_path, "PNG", quality=95)
    fsize = os.path.getsize(output_path)
    print(f"Saved: {output_path}")
    print(f"Size: {fsize:,} bytes | {WIDTH}x{HEIGHT}")
    return True


def main():
    print("=" * 60)
    print("CORTEX AI Cover Image Generator")
    print("=" * 60)
    
    raw_path = os.path.join(OUT_DIR, "ai_raw_background.png")
    pro_path = os.path.join(OUT_DIR, "cortex_pro_cover.png")
    bundle_path = os.path.join(OUT_DIR, "cortex_bundle_cover.png")
    
    # Generate 3 variants with different seeds, pick best
    best_path = None
    seeds = [42, 1337, 2026]
    
    for i, seed in enumerate(seeds):
        print(f"\n--- Generating variant {i+1}/3 (seed={seed}) ---")
        variant_path = os.path.join(OUT_DIR, f"ai_raw_variant_{i+1}.png")
        ok = download_ai_image(PROMPT, WIDTH, HEIGHT, variant_path, seed=seed)
        if ok:
            try:
                img = Image.open(variant_path)
                if img.size[0] >= 512 and img.size[1] >= 512:
                    if best_path is None:
                        best_path = variant_path
                    print(f"  Valid: {img.size[0]}x{img.size[1]}")
                else:
                    print(f"  Too small: {img.size}")
            except Exception as e:
                print(f"  Invalid image: {e}")
        time.sleep(2)
    
    if not best_path:
        print("\nERROR: All AI generation attempts failed.")
        print("Falling back to Pillow-only cover...")
        # Run the original script as fallback
        return False
    
    # Use first successful variant as background
    print(f"\nUsing background: {best_path}")
    
    # Composite PRO branding
    print("\n--- Compositing PRO cover ---")
    composite_branding(best_path, pro_path, variant="PRO")
    
    # Composite BUNDLE branding  
    print("\n--- Compositing BUNDLE cover ---")
    composite_branding(best_path, bundle_path, variant="BUNDLE")
    
    # Cleanup raw variants
    for i in range(1, 4):
        vp = os.path.join(OUT_DIR, f"ai_raw_variant_{i}.png")
        # Keep them for reference, don't delete
    
    print("\n" + "=" * 60)
    print("DONE!")
    print(f"  PRO cover:    {pro_path}")
    print(f"  BUNDLE cover: {bundle_path}")
    print("Upload these to your Gumroad listings.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    main()
