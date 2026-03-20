"""Generate LitigationOS app icon programmatically.

Creates a 256x256 ICO file with the scales-of-justice motif
in the LitigationOS color scheme (dark blue bg, red accent).
"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

def generate_icon(output_path: Path = None) -> Path:
    """Generate the LitigationOS icon."""
    output_path = output_path or Path(__file__).parent / "icon.ico"
    
    if Image is None:
        print("Pillow not installed. Run: pip install Pillow")
        return output_path
    
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        img = Image.new("RGBA", (size, size), (26, 26, 46, 255))  # #1a1a2e
        draw = ImageDraw.Draw(img)
        
        # Draw scales of justice icon (simplified)
        cx, cy = size // 2, size // 2
        
        # Red accent circle
        margin = size // 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            outline=(233, 69, 96, 255),  # #e94560
            width=max(1, size // 16),
        )
        
        # Balance beam (horizontal line)
        beam_y = cy - size // 6
        draw.line(
            [(cx - size // 3, beam_y), (cx + size // 3, beam_y)],
            fill=(233, 69, 96, 255),
            width=max(1, size // 20),
        )
        
        # Center post
        draw.line(
            [(cx, beam_y - size // 10), (cx, cy + size // 4)],
            fill=(223, 230, 233, 255),  # #dfe6e9
            width=max(1, size // 20),
        )
        
        # Left pan
        lx = cx - size // 3
        draw.arc(
            [lx - size // 8, beam_y, lx + size // 8, beam_y + size // 4],
            0, 180,
            fill=(0, 184, 148, 255),  # #00b894 green
            width=max(1, size // 24),
        )
        
        # Right pan
        rx = cx + size // 3
        draw.arc(
            [rx - size // 8, beam_y, rx + size // 8, beam_y + size // 4],
            0, 180,
            fill=(0, 184, 148, 255),
            width=max(1, size // 24),
        )
        
        # Base
        draw.line(
            [(cx - size // 6, cy + size // 4), (cx + size // 6, cy + size // 4)],
            fill=(223, 230, 233, 255),
            width=max(1, size // 16),
        )
        
        images.append(img)
    
    # Save as ICO with all sizes
    images[-1].save(str(output_path), format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Icon saved: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_icon()
