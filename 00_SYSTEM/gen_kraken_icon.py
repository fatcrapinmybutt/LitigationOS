"""
PROJECT KRAKEN Icon Generator — Bleeding-Edge Cyber Kraken
Generates a multi-resolution .ico with a neon tentacle vortex design.
"""
import math, struct, io, os

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    print("ERROR: Pillow not installed")
    raise SystemExit(1)

OUT = r"C:\Users\andre\LitigationOS\08_MEDIA\project_kraken_icon.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]

# Color palette — deep ocean cyber
BG_DARK    = (8, 10, 18)        # near-black deep ocean
BG_MID     = (12, 18, 35)       # midnight blue
NEON_CYAN  = (0, 255, 220)      # electric cyan
NEON_BLUE  = (30, 144, 255)     # dodger blue
NEON_PURPLE= (138, 43, 226)     # blue-violet
NEON_RED   = (255, 50, 80)      # crimson accent
GLOW_CYAN  = (0, 200, 180, 80)  # translucent glow
WHITE      = (255, 255, 255)
GOLD       = (255, 200, 50)


def lerp_color(c1, c2, t):
    """Linear interpolate between two RGB colors."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_tentacle(draw, cx, cy, angle_deg, length, width, color1, color2, segments=20):
    """Draw a curved tentacle from center outward with gradient and suckers."""
    angle = math.radians(angle_deg)
    # Tentacle curves outward with a spiral component
    curl = 0.04  # curl factor
    points = []
    for i in range(segments + 1):
        t = i / segments
        r = length * t
        a = angle + curl * t * 6  # spiraling outward
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        points.append((x, y))
    
    # Draw tentacle body (thick to thin)
    for i in range(len(points) - 1):
        t = i / len(points)
        w = max(1, int(width * (1 - t * 0.85)))
        color = lerp_color(color1, color2, t)
        draw.line([points[i], points[i+1]], fill=color, width=w)
    
    # Sucker dots along tentacle
    for i in range(2, len(points) - 2, 3):
        t = i / len(points)
        sr = max(1, int(width * 0.3 * (1 - t)))
        px, py = points[i]
        if sr >= 1:
            draw.ellipse([px-sr, py-sr, px+sr, py+sr], fill=lerp_color(color2, WHITE, 0.3))


def draw_eye(draw, cx, cy, radius, glow_layer=None):
    """Draw the central kraken eye — menacing, glowing."""
    # Outer glow ring
    for r in range(int(radius * 1.8), int(radius), -1):
        alpha = int(60 * (1 - (r - radius) / (radius * 0.8)))
        alpha = max(0, min(255, alpha))
        c = (*NEON_CYAN[:3], alpha)
        if glow_layer:
            gldraw = ImageDraw.Draw(glow_layer)
            gldraw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c)
    
    # Eye socket (dark)
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=(5, 5, 15))
    
    # Iris ring
    ir = int(radius * 0.85)
    draw.ellipse([cx-ir, cy-ir, cx+ir, cy+ir], fill=(0, 40, 60), outline=NEON_CYAN, width=max(1, int(radius*0.08)))
    
    # Iris gradient rings
    for ring in range(3):
        rr = int(ir * (0.8 - ring * 0.2))
        c = lerp_color(NEON_CYAN, NEON_BLUE, ring / 3)
        draw.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], outline=c, width=max(1, int(radius*0.05)))
    
    # Pupil — vertical slit (like a real kraken/cephalopod)
    pw = max(1, int(radius * 0.15))
    ph = int(radius * 0.65)
    draw.ellipse([cx-pw, cy-ph, cx+pw, cy+ph], fill=(0, 0, 0))
    
    # Pupil highlight (tiny bright dot)
    hw = max(1, int(radius * 0.12))
    hx, hy = cx - int(radius * 0.2), cy - int(radius * 0.25)
    draw.ellipse([hx-hw, hy-hw, hx+hw, hy+hw], fill=(200, 255, 255))


def draw_circuit_traces(draw, size, count=8):
    """Draw subtle circuit-board traces in background."""
    import random
    random.seed(42)  # deterministic
    for _ in range(count):
        x = random.randint(0, size)
        y = random.randint(0, size)
        for seg in range(random.randint(3, 8)):
            direction = random.choice([(1,0), (0,1), (-1,0), (0,-1), (1,1), (-1,-1)])
            length = random.randint(size//15, size//6)
            x2 = x + direction[0] * length
            y2 = y + direction[1] * length
            alpha = random.randint(15, 40)
            draw.line([(x, y), (x2, y2)], fill=(*NEON_CYAN[:3],), width=1)
            x, y = x2, y2
            # Node dot at joints
            nr = max(1, size // 80)
            draw.ellipse([x-nr, y-nr, x+nr, y+nr], fill=lerp_color(NEON_BLUE, NEON_CYAN, 0.5))


def draw_hex_grid(draw, size, spacing=None):
    """Draw subtle hexagonal grid overlay."""
    if spacing is None:
        spacing = max(8, size // 12)
    h = int(spacing * math.sqrt(3) / 2)
    for row in range(-1, size // h + 2):
        for col in range(-1, size // spacing + 2):
            cx = col * spacing + (spacing // 2 if row % 2 else 0)
            cy = row * h
            r = spacing // 3
            if r < 2:
                continue
            # Draw hex outline very faintly
            pts = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            draw.polygon(pts, outline=(20, 35, 55))


def generate_icon(size):
    """Generate one icon frame at given size."""
    img = Image.new("RGBA", (size, size), (*BG_DARK, 255))
    draw = ImageDraw.Draw(img)
    glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    cx, cy = size // 2, size // 2
    
    # Background: radial gradient
    for r in range(size // 2, 0, -1):
        t = r / (size // 2)
        c = lerp_color(BG_MID, BG_DARK, t)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)
    
    if size >= 48:
        draw_hex_grid(draw, size)
    
    if size >= 32:
        draw_circuit_traces(draw, size, count=max(3, size // 30))
    
    # 8 tentacles radiating from center
    num_tentacles = 8
    tentacle_length = size * 0.42
    tentacle_width = max(2, size // 20)
    
    color_pairs = [
        (NEON_CYAN, NEON_BLUE),
        (NEON_BLUE, NEON_PURPLE),
        (NEON_PURPLE, NEON_RED),
        (NEON_CYAN, NEON_PURPLE),
        (NEON_BLUE, NEON_CYAN),
        (NEON_PURPLE, NEON_BLUE),
        (NEON_RED, NEON_PURPLE),
        (NEON_CYAN, NEON_RED),
    ]
    
    for i in range(num_tentacles):
        angle = (360 / num_tentacles) * i - 90  # start from top
        c1, c2 = color_pairs[i % len(color_pairs)]
        draw_tentacle(draw, cx, cy, angle, tentacle_length, tentacle_width, c1, c2,
                      segments=max(8, size // 10))
    
    # Central eye
    eye_radius = max(3, int(size * 0.18))
    draw_eye(draw, cx, cy, eye_radius, glow_layer)
    
    # Composite glow layer
    if size >= 64:
        glow_blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=size // 40))
        img = Image.alpha_composite(img, glow_blurred)
        draw = ImageDraw.Draw(img)
    
    # Outer ring (tech border)
    ring_r = int(size * 0.46)
    ring_w = max(1, size // 60)
    draw.ellipse([cx-ring_r, cy-ring_r, cx+ring_r, cy+ring_r],
                 outline=(*NEON_CYAN[:3], 100), width=ring_w)
    
    # Corner tech brackets (only at larger sizes)
    if size >= 64:
        blen = size // 6
        bw = max(1, size // 80)
        corners = [(2, 2), (size-2, 2), (2, size-2), (size-2, size-2)]
        dirs = [(1,1), (-1,1), (1,-1), (-1,-1)]
        for (x, y), (dx, dy) in zip(corners, dirs):
            draw.line([(x, y), (x + dx*blen, y)], fill=NEON_CYAN, width=bw)
            draw.line([(x, y), (x, y + dy*blen)], fill=NEON_CYAN, width=bw)
    
    # "K" letter watermark at small sizes for recognizability
    if size <= 32 and size >= 16:
        try:
            font = ImageFont.load_default()
            tw = size // 2
            draw.text((cx - tw//3, cy - tw//2), "K", fill=NEON_CYAN, font=font)
        except Exception:
            pass
    
    return img.convert("RGBA")


def main():
    print("=== PROJECT KRAKEN Icon Generator ===")
    print(f"Generating {len(SIZES)} resolutions: {SIZES}")
    
    frames = []
    for s in SIZES:
        print(f"  [{s}x{s}] rendering...", end=" ")
        frame = generate_icon(s)
        frames.append(frame)
        print("done")
    
    # Save as .ico with all resolutions
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    
    # Pillow's ICO save
    frames[0].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:]
    )
    
    fsize = os.path.getsize(OUT)
    print(f"\nIcon saved: {OUT}")
    print(f"Size: {fsize:,} bytes ({fsize/1024:.1f} KB)")
    print(f"Resolutions: {', '.join(f'{s}x{s}' for s in SIZES)}")
    
    # Also save a 256x256 PNG preview
    preview = OUT.replace(".ico", "_preview.png")
    frames[-1].save(preview, format="PNG")
    print(f"Preview: {preview}")


if __name__ == "__main__":
    main()
