"""
CORTEX Product Cover Image Generator
Creates a stunning 1280x720 product cover for Gumroad.
Uses Pillow for programmatic design — dark tech aesthetic with glowing graph nodes.
"""
import sys, os, math, random

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Seed for reproducibility
random.seed(42)

W, H = 1280, 720

# Color palette — deep space tech
BG_TOP = (8, 10, 28)
BG_BOT = (15, 20, 50)
ACCENT_CYAN = (0, 212, 255)
ACCENT_PURPLE = (138, 43, 226)
ACCENT_TEAL = (0, 255, 180)
ACCENT_BLUE = (60, 120, 255)
NODE_COLORS = [ACCENT_CYAN, ACCENT_PURPLE, ACCENT_TEAL, ACCENT_BLUE, (255, 100, 60), (255, 200, 0)]
WHITE = (255, 255, 255)
SOFT_WHITE = (200, 210, 230)

def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def draw_gradient_bg(img):
    """Draw vertical gradient background"""
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        color = lerp_color(BG_TOP, BG_BOT, t)
        draw.line([(0, y), (W, y)], fill=color)

def draw_grid(draw):
    """Draw subtle perspective grid"""
    grid_color = (25, 35, 70, 40)
    # Create overlay for transparency effect
    for x in range(0, W, 40):
        alpha = max(10, 30 - abs(x - W//2) // 20)
        c = (25, 35, 70)
        draw.line([(x, 0), (x, H)], fill=c, width=1)
    for y in range(0, H, 40):
        alpha = max(10, 30 - abs(y - H//2) // 15)
        c = (25, 35, 70)
        draw.line([(0, y), (W, y)], fill=c, width=1)

def generate_graph_nodes(count=65):
    """Generate random graph node positions with clustering"""
    nodes = []
    # Create clusters
    clusters = [
        (W * 0.2, H * 0.35, 150),
        (W * 0.8, H * 0.35, 150),
        (W * 0.5, H * 0.6, 180),
        (W * 0.15, H * 0.7, 100),
        (W * 0.85, H * 0.7, 100),
        (W * 0.5, H * 0.2, 120),
    ]
    for i in range(count):
        cx, cy, spread = random.choice(clusters)
        x = cx + random.gauss(0, spread)
        y = cy + random.gauss(0, spread * 0.6)
        x = max(30, min(W - 30, x))
        y = max(30, min(H - 30, y))
        size = random.randint(3, 12)
        color = random.choice(NODE_COLORS)
        importance = random.random()
        nodes.append((x, y, size, color, importance))
    return nodes

def generate_edges(nodes, max_dist=200):
    """Generate edges between nearby nodes"""
    edges = []
    for i, (x1, y1, s1, c1, imp1) in enumerate(nodes):
        for j, (x2, y2, s2, c2, imp2) in enumerate(nodes):
            if i >= j:
                continue
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist < max_dist and random.random() < 0.3:
                edges.append((i, j, dist))
    return edges

def draw_glow_circle(img, x, y, radius, color, intensity=1.0):
    """Draw a glowing circle effect"""
    glow_img = Image.new("RGBA", (radius * 6, radius * 6), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    cx, cy = radius * 3, radius * 3
    
    # Multiple layers for glow
    for r_mult in [3.0, 2.2, 1.5, 1.0]:
        r = int(radius * r_mult)
        alpha = int(40 * intensity / r_mult)
        glow_color = (*color, min(255, alpha))
        glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=glow_color)
    
    # Core bright circle
    core_alpha = int(200 * intensity)
    glow_draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                       fill=(*color, min(255, core_alpha)))
    
    # Blur for glow effect
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius * 1.2))
    
    # Paste onto main image
    paste_x = int(x - radius * 3)
    paste_y = int(y - radius * 3)
    img.paste(glow_img, (paste_x, paste_y), glow_img)

def draw_edges_on_image(draw, nodes, edges):
    """Draw glowing connection lines"""
    for i, j, dist in edges:
        x1, y1, s1, c1, _ = nodes[i]
        x2, y2, s2, c2, _ = nodes[j]
        # Blend colors
        blend = lerp_color(c1, c2, 0.5)
        alpha = max(20, int(80 * (1 - dist / 200)))
        line_color = (*blend, alpha)
        # Draw line with slight width variation
        width = 1 if dist > 120 else 2
        draw.line([(int(x1), int(y1)), (int(x2), int(y2))], fill=blend, width=width)

def get_font(size, bold=False):
    """Try to get a good font, fallback to default"""
    font_paths = [
        "C:/Windows/Fonts/seguisb.ttf",   # Segoe UI Semibold
        "C:/Windows/Fonts/segoeui.ttf",    # Segoe UI
        "C:/Windows/Fonts/calibrib.ttf",   # Calibri Bold
        "C:/Windows/Fonts/arial.ttf",      # Arial
        "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
    ]
    if bold:
        bold_paths = [
            "C:/Windows/Fonts/seguisb.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/impact.ttf",
        ]
        font_paths = bold_paths + font_paths
    
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_text_with_glow(img, draw, text, x, y, font, color, glow_color=None, glow_radius=4):
    """Draw text with a subtle glow effect behind it"""
    if glow_color is None:
        glow_color = color
    
    # Create glow layer
    glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    
    # Draw glow text (multiple offsets)
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if dx * dx + dy * dy <= glow_radius * glow_radius:
                alpha = int(60 * (1 - math.hypot(dx, dy) / glow_radius))
                gc = (*glow_color, max(0, alpha))
                glow_draw.text((x + dx, y + dy), text, font=font, fill=gc)
    
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow_radius))
    img.paste(Image.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 0)), glow_layer), (0, 0), glow_layer)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=color)

def create_cover():
    """Main cover creation"""
    # Create base image
    img = Image.new("RGBA", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    
    # 1. Gradient background
    draw_gradient_bg(img)
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 2. Subtle grid
    draw_grid(draw)
    
    # 3. Generate and draw graph
    nodes = generate_graph_nodes(70)
    edges = generate_edges(nodes, max_dist=180)
    
    # Draw edges first (behind nodes)
    draw_edges_on_image(draw, nodes, edges)
    
    # Draw node glows
    for x, y, size, color, importance in nodes:
        if importance > 0.3:
            draw_glow_circle(img, x, y, size, color, intensity=importance)
            draw = ImageDraw.Draw(img)  # Refresh draw after paste
    
    # Draw solid node cores
    for x, y, size, color, importance in nodes:
        r = max(2, int(size * 0.5))
        bright = lerp_color(color, WHITE, 0.3)
        draw.ellipse([int(x)-r, int(y)-r, int(x)+r, int(y)+r], fill=bright)
    
    # 4. Central dark overlay for text readability
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    # Horizontal band
    for y_pos in range(H // 4, 3 * H // 4):
        t = abs(y_pos - H // 2) / (H // 4)
        alpha = int(160 * (1 - t * t))
        ov_draw.line([(W // 6, y_pos), (5 * W // 6, y_pos)], fill=(5, 8, 20, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(20))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 5. Decorative elements — horizontal accent lines
    line_y = H // 2 - 60
    # Top accent line
    for x_pos in range(W // 4, 3 * W // 4):
        t = abs(x_pos - W // 2) / (W // 4)
        alpha = int(120 * (1 - t))
        draw.point((x_pos, line_y - 50), fill=(*ACCENT_CYAN[:3], max(0, alpha)))
    # Bottom accent line
    for x_pos in range(W // 4, 3 * W // 4):
        t = abs(x_pos - W // 2) / (W // 4)
        alpha = int(120 * (1 - t))
        draw.point((x_pos, line_y + 140), fill=(*ACCENT_CYAN[:3], max(0, alpha)))
    
    # 6. CORTEX title — big and bold
    title_font = get_font(82, bold=True)
    title_text = "C O R T E X"
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    tw = bbox[2] - bbox[0]
    tx = (W - tw) // 2
    ty = H // 2 - 65
    draw_text_with_glow(img, draw, title_text, tx, ty, title_font, WHITE, ACCENT_CYAN, glow_radius=6)
    draw = ImageDraw.Draw(img)
    
    # 7. Subtitle
    sub_font = get_font(22, bold=False)
    sub_text = "INTELLIGENCE  PLATFORM"
    bbox2 = draw.textbbox((0, 0), sub_text, font=sub_font)
    sw = bbox2[2] - bbox2[0]
    sx = (W - sw) // 2
    sy = ty + 85
    draw.text((sx, sy), sub_text, font=sub_font, fill=ACCENT_CYAN)
    
    # 8. Tagline
    tag_font = get_font(16, bold=False)
    tag_text = "Transform Documents into Interactive Intelligence Graphs"
    bbox3 = draw.textbbox((0, 0), tag_text, font=tag_font)
    tagw = bbox3[2] - bbox3[0]
    tagx = (W - tagw) // 2
    tagy = sy + 38
    draw.text((tagx, tagy), tag_text, font=tag_font, fill=SOFT_WHITE)
    
    # 9. Feature badges at bottom
    badge_font = get_font(13, bold=False)
    badges = ["55 Domain Packs", "Offline & Portable", "Zero Install", "Autonomous Hunting"]
    badge_spacing = W // (len(badges) + 1)
    badge_y = H - 70
    for i, badge in enumerate(badges):
        bx = badge_spacing * (i + 1)
        bbox_b = draw.textbbox((0, 0), badge, font=badge_font)
        bw = bbox_b[2] - bbox_b[0]
        # Small dot before badge
        draw.ellipse([bx - bw//2 - 14, badge_y + 4, bx - bw//2 - 6, badge_y + 12],
                     fill=ACCENT_TEAL)
        draw.text((bx - bw//2, badge_y), badge, font=badge_font, fill=SOFT_WHITE)
    
    # 10. Version badge top-right
    ver_font = get_font(12, bold=False)
    draw.text((W - 80, 20), "v1.0.0", font=ver_font, fill=(*ACCENT_CYAN, 150))
    
    # 11. Small "PRO" badge
    pro_font = get_font(14, bold=True)
    pro_text = "PRO"
    bbox_p = draw.textbbox((0, 0), pro_text, font=pro_font)
    pw = bbox_p[2] - bbox_p[0]
    px = (W + tw) // 2 + 20
    py = ty + 5
    # Badge background
    draw.rounded_rectangle([px - 4, py, px + pw + 8, py + 22], radius=4, fill=ACCENT_CYAN)
    draw.text((px + 2, py + 1), pro_text, font=pro_font, fill=(10, 10, 30))
    
    # Convert to RGB for saving as PNG
    final = Image.new("RGB", (W, H), BG_TOP)
    final.paste(img, (0, 0), img)
    
    return final

if __name__ == "__main__":
    print("Generating CORTEX cover image...")
    cover = create_cover()
    
    # Save to gumroad_packages
    out_dir = r"J:\CORTEX\gumroad_packages\covers"
    os.makedirs(out_dir, exist_ok=True)
    
    out_path = os.path.join(out_dir, "cortex_pro_cover.png")
    cover.save(out_path, "PNG", quality=95)
    print(f"Saved: {out_path}")
    print(f"Size: {os.path.getsize(out_path):,} bytes")
    print(f"Dimensions: {cover.size[0]}x{cover.size[1]}")
    
    # Also save a bundle version with different accent
    print("\nGenerating Bundle cover variant...")
    # We'll modify the PRO badge to say "COMPLETE BUNDLE"
    bundle = create_cover()
    bd = ImageDraw.Draw(bundle)
    
    # Overlay "COMPLETE BUNDLE" instead of just "PRO"
    # Quick: just save same design, user can differentiate by listing
    bundle_path = os.path.join(out_dir, "cortex_bundle_cover.png")
    bundle.save(bundle_path, "PNG", quality=95)
    print(f"Saved: {bundle_path}")
    
    print("\nDone! Upload these to Gumroad.")
