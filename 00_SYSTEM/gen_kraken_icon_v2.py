"""
PROJECT KRAKEN Icon Generator v2 — Bleeding-Edge Cyber Kraken
Generates a multi-resolution .ico with a neon tentacle vortex design.
Fixed ICO assembly for proper multi-resolution embedding.
"""
import math, os, random

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    print("ERROR: Pillow not installed")
    raise SystemExit(1)

OUT = r"C:\Users\andre\LitigationOS\08_MEDIA\project_kraken_icon.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]

# Color palette -- deep ocean cyber
BG_DARK     = (8, 10, 18)
BG_MID      = (12, 18, 35)
NEON_CYAN   = (0, 255, 220)
NEON_BLUE   = (30, 144, 255)
NEON_PURPLE = (138, 43, 226)
NEON_RED    = (255, 50, 80)
WHITE       = (255, 255, 255)


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * max(0, min(1, t))) for i in range(min(len(c1), len(c2))))


def draw_tentacle(draw, cx, cy, angle_deg, length, width, color1, color2, segments=20):
    angle = math.radians(angle_deg)
    curl = 0.04
    points = []
    for i in range(segments + 1):
        t = i / segments
        r = length * t
        a = angle + curl * t * 6
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        points.append((x, y))
    for i in range(len(points) - 1):
        t = i / max(1, len(points) - 1)
        w = max(1, int(width * (1 - t * 0.85)))
        color = lerp_color(color1, color2, t)
        draw.line([points[i], points[i + 1]], fill=color, width=w)
    for i in range(2, len(points) - 2, 3):
        t = i / max(1, len(points) - 1)
        sr = max(1, int(width * 0.3 * (1 - t)))
        px, py = points[i]
        bright = lerp_color(color2, WHITE, 0.3)
        draw.ellipse([px - sr, py - sr, px + sr, py + sr], fill=bright)


def draw_eye(draw, cx, cy, radius):
    # Dark socket
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 fill=(5, 5, 15), outline=NEON_CYAN, width=max(1, int(radius * 0.1)))
    # Iris rings
    ir = int(radius * 0.82)
    draw.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=(0, 40, 60))
    for ring in range(4):
        rr = int(ir * (0.9 - ring * 0.18))
        if rr < 1:
            break
        c = lerp_color(NEON_CYAN, NEON_BLUE, ring / 4)
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                     outline=c, width=max(1, int(radius * 0.06)))
    # Vertical slit pupil (cephalopod style)
    pw = max(1, int(radius * 0.14))
    ph = int(radius * 0.6)
    draw.ellipse([cx - pw, cy - ph, cx + pw, cy + ph], fill=(0, 0, 0))
    # Specular highlight
    hw = max(1, int(radius * 0.11))
    hx = cx - int(radius * 0.22)
    hy = cy - int(radius * 0.28)
    draw.ellipse([hx - hw, hy - hw, hx + hw, hy + hw], fill=(200, 255, 255))


def draw_circuit_traces(draw, size, count=8):
    rng = random.Random(42)
    for _ in range(count):
        x = rng.randint(0, size)
        y = rng.randint(0, size)
        for _ in range(rng.randint(3, 8)):
            dx, dy = rng.choice([(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1)])
            ln = rng.randint(size // 15, size // 6)
            x2, y2 = x + dx * ln, y + dy * ln
            draw.line([(x, y), (x2, y2)], fill=(15, 40, 55), width=1)
            nr = max(1, size // 80)
            draw.ellipse([x2 - nr, y2 - nr, x2 + nr, y2 + nr], fill=(20, 60, 80))
            x, y = x2, y2


def draw_hex_grid(draw, size):
    spacing = max(8, size // 12)
    h = int(spacing * math.sqrt(3) / 2)
    for row in range(-1, size // max(1, h) + 2):
        for col in range(-1, size // max(1, spacing) + 2):
            cx_h = col * spacing + (spacing // 2 if row % 2 else 0)
            cy_h = row * h
            r = spacing // 3
            if r < 2:
                continue
            pts = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                pts.append((cx_h + r * math.cos(angle), cy_h + r * math.sin(angle)))
            draw.polygon(pts, outline=(18, 30, 48))


def generate_icon(size):
    img = Image.new("RGBA", (size, size), (*BG_DARK, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # Radial gradient background
    for r in range(size // 2, 0, -1):
        t = r / (size // 2)
        c = lerp_color(BG_MID, BG_DARK, t)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*c, 255))

    # Background details (only at sufficient resolution)
    if size >= 48:
        draw_hex_grid(draw, size)
    if size >= 32:
        draw_circuit_traces(draw, size, count=max(3, size // 30))

    # Outer glow ring
    glow_r = int(size * 0.44)
    for g in range(max(1, size // 25)):
        rr = glow_r + g
        alpha = max(5, 40 - g * 8)
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                     outline=(*NEON_CYAN[:3],), width=1)

    # 8 tentacles
    colors = [
        (NEON_CYAN, NEON_BLUE), (NEON_BLUE, NEON_PURPLE),
        (NEON_PURPLE, NEON_RED), (NEON_CYAN, NEON_PURPLE),
        (NEON_BLUE, NEON_CYAN), (NEON_PURPLE, NEON_BLUE),
        (NEON_RED, NEON_PURPLE), (NEON_CYAN, NEON_RED),
    ]
    tlen = size * 0.42
    tw = max(2, size // 18)
    for i in range(8):
        angle = (360 / 8) * i - 90
        c1, c2 = colors[i]
        draw_tentacle(draw, cx, cy, angle, tlen, tw, c1, c2,
                      segments=max(8, size // 10))

    # Central eye
    eye_r = max(3, int(size * 0.19))
    draw_eye(draw, cx, cy, eye_r)

    # Outer tech ring
    ring_r = int(size * 0.46)
    ring_w = max(1, size // 50)
    draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
                 outline=NEON_CYAN, width=ring_w)

    # Tick marks around ring (radar/sonar style)
    if size >= 48:
        for i in range(24):
            a = math.radians(i * 15)
            r1 = ring_r - max(1, size // 40)
            r2 = ring_r + max(1, size // 60)
            x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
            x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
            draw.line([(x1, y1), (x2, y2)], fill=NEON_CYAN, width=1)

    # Corner brackets
    if size >= 64:
        blen = size // 6
        bw = max(1, size // 70)
        for (bx, by), (dx, dy) in [
            ((3, 3), (1, 1)), ((size - 3, 3), (-1, 1)),
            ((3, size - 3), (1, -1)), ((size - 3, size - 3), (-1, -1))
        ]:
            draw.line([(bx, by), (bx + dx * blen, by)], fill=NEON_CYAN, width=bw)
            draw.line([(bx, by), (bx, by + dy * blen)], fill=NEON_CYAN, width=bw)

    # Apply glow blur at large sizes
    if size >= 64:
        glow = img.copy().filter(ImageFilter.GaussianBlur(radius=size // 50))
        img = Image.blend(img, glow, alpha=0.3)

    return img.convert("RGBA")


def main():
    print("=== PROJECT KRAKEN Icon Generator v2 ===")
    print("Design: Cyber Kraken -- neon tentacles, cephalopod eye, circuit traces")
    print(f"Rendering {len(SIZES)} resolutions...\n")

    frames = []
    for s in SIZES:
        print(f"  [{s:>3}x{s:<3}] ", end="")
        frame = generate_icon(s)
        frames.append(frame)
        print("OK")

    # Save .ico using the largest frame as base, with explicit size list
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    # Save the 256x256 as the base image, append all others
    base = frames[-1]  # 256x256
    others = frames[:-1]  # 16..128

    base.save(
        OUT,
        format="ICO",
        append_images=others,
        sizes=[(s, s) for s in SIZES],
    )

    fsize = os.path.getsize(OUT)
    print(f"\nIcon saved: {OUT}")
    print(f"Size: {fsize:,} bytes ({fsize / 1024:.1f} KB)")

    # Verify by reopening
    ico = Image.open(OUT)
    print(f"ICO info: {ico.size}, frames: {getattr(ico, 'n_frames', 'N/A')}")

    # Also save 256px PNG preview so user can see it
    preview = OUT.replace(".ico", "_256.png")
    frames[-1].save(preview, format="PNG")
    print(f"Preview PNG: {preview}")


if __name__ == "__main__":
    main()
