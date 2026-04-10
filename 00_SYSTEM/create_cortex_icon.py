"""
CORTEX App Icon Generator
Generates a professional 256x256 .ico file for the CORTEX desktop app.
Uses Pillow to create a neural-network inspired brain icon.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw, ImageFont
import math, os

SIZES = [256, 128, 64, 48, 32, 16]

def create_icon_image(size):
    """Create a single icon frame at the given size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = int(size * 0.45)

    # Background circle - dark navy
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(10, 15, 30, 255))

    # Gradient ring (simulated with concentric circles)
    for i in range(max(3, size//20)):
        ring_r = r - i
        if ring_r < r * 0.85:
            break
        # Cyan to purple gradient
        t = i / max(1, size//20)
        red = int(0 + t * 120)
        green = int(200 - t * 100)
        blue = int(255 - t * 50)
        alpha = int(200 - t * 100)
        draw.ellipse(
            [cx-ring_r, cy-ring_r, cx+ring_r, cy+ring_r],
            outline=(red, green, blue, alpha),
            width=max(1, size//80)
        )

    # Inner glow
    inner_r = int(r * 0.82)
    draw.ellipse(
        [cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r],
        fill=(15, 20, 40, 255)
    )

    # Neural network nodes
    node_r = max(2, size // 30)
    nodes = []
    # Center node
    nodes.append((cx, cy))
    # Inner ring (6 nodes)
    for i in range(6):
        angle = math.radians(i * 60 + 30)
        nx = cx + int(r * 0.35 * math.cos(angle))
        ny = cy + int(r * 0.35 * math.sin(angle))
        nodes.append((nx, ny))
    # Outer ring (6 nodes)
    for i in range(6):
        angle = math.radians(i * 60)
        nx = cx + int(r * 0.65 * math.cos(angle))
        ny = cy + int(r * 0.65 * math.sin(angle))
        nodes.append((nx, ny))

    # Draw connections (edges)
    line_w = max(1, size // 120)
    # Center to inner
    for i in range(1, 7):
        draw.line([nodes[0], nodes[i]], fill=(0, 180, 255, 80), width=line_w)
    # Inner to outer
    for i in range(6):
        inner_idx = 1 + i
        outer_idx = 7 + i
        draw.line([nodes[inner_idx], nodes[outer_idx]], fill=(0, 180, 255, 60), width=line_w)
        # Cross connections
        outer_next = 7 + (i + 1) % 6
        draw.line([nodes[inner_idx], nodes[outer_next]], fill=(100, 50, 200, 40), width=line_w)
    # Inner ring connections
    for i in range(6):
        next_i = 1 + (i + 1) % 6
        draw.line([nodes[1 + i], nodes[next_i]], fill=(0, 150, 255, 50), width=line_w)

    # Draw nodes (dots)
    # Center - bright cyan
    draw.ellipse(
        [cx - node_r*2, cy - node_r*2, cx + node_r*2, cy + node_r*2],
        fill=(0, 220, 255, 255)
    )
    # Inner ring - cyan
    for i in range(1, 7):
        nx, ny = nodes[i]
        draw.ellipse(
            [nx - node_r, ny - node_r, nx + node_r, ny + node_r],
            fill=(0, 200, 255, 230)
        )
    # Outer ring - purple-blue
    for i in range(7, 13):
        nx, ny = nodes[i]
        draw.ellipse(
            [nx - node_r, ny - node_r, nx + node_r, ny + node_r],
            fill=(120, 80, 255, 200)
        )

    # "C" letter overlay for branding (only on larger sizes)
    if size >= 64:
        try:
            font_size = int(size * 0.28)
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", font_size)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "C", font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = cx - tw // 2
        ty = cy - th // 2 - int(size * 0.02)
        # Shadow
        draw.text((tx+1, ty+1), "C", fill=(0, 0, 0, 100), font=font)
        # Main letter
        draw.text((tx, ty), "C", fill=(255, 255, 255, 200), font=font)

    return img

def main():
    out_dir = "J:\\CORTEX"
    
    # Generate all size frames
    frames = []
    for s in SIZES:
        img = create_icon_image(s)
        frames.append(img)
        print(f"  Generated {s}x{s} frame")

    # Save as .ico (multi-resolution)
    ico_path = os.path.join(out_dir, "cortex.ico")
    frames[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:]
    )
    print(f"Icon saved: {ico_path}")

    # Also save 256px PNG for other uses
    png_path = os.path.join(out_dir, "cortex_icon_256.png")
    frames[0].save(png_path, format='PNG')
    print(f"PNG saved: {png_path}")

    # Save 512px version for store listings
    big = create_icon_image(512)
    big_path = os.path.join(out_dir, "cortex_icon_512.png")
    big.save(big_path, format='PNG')
    print(f"Large PNG saved: {big_path}")

if __name__ == "__main__":
    main()
