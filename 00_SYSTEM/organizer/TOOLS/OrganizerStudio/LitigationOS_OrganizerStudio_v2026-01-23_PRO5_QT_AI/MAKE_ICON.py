#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

def main() -> int:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        print("Pillow is required: pip install pillow")
        return 1

    out = Path("assets")
    out.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (256, 256), (15, 18, 24, 255))
    d = ImageDraw.Draw(img)
    # simple "OS" mark
    d.rounded_rectangle([24, 28, 232, 228], radius=38, outline=(255,255,255,200), width=6)
    d.text((86, 92), "OS", fill=(255,255,255,235))
    # export icon sizes
    ico = out / "OrganizerStudio.ico"
    img.save(ico, sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print(str(ico))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
