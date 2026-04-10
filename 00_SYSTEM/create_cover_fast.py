"""
CORTEX AI Cover — Single fast request to Pollinations.ai, then Pillow composite.
"""
import urllib.request, urllib.parse, os, sys, time

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
except ImportError:
    print("ERROR: pip install Pillow"); sys.exit(1)

OUT = r"J:\CORTEX\gumroad_packages\covers"
os.makedirs(OUT, exist_ok=True)

PROMPT = (
    "dark futuristic holographic neural network visualization, "
    "glowing cyan blue nodes connected by light beams, "
    "deep black background, cinematic, 8k, no text no words"
)

def main():
    raw = os.path.join(OUT, "ai_bg.png")
    encoded = urllib.parse.quote(PROMPT)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed=42"
    
    print("Downloading AI background (1 attempt, 90s timeout)...")
    req = urllib.request.Request(url, headers={"User-Agent": "CORTEX/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
            with open(raw, "wb") as f:
                f.write(data)
            print(f"Got {len(data):,} bytes")
    except Exception as e:
        print(f"API failed: {e}")
        print("Using gradient fallback...")
        # Generate gradient background instead
        img = Image.new("RGB", (1280, 720))
        draw = ImageDraw.Draw(img)
        for y in range(720):
            r = int(5 + 15 * (y/720))
            g = int(5 + 25 * (y/720))
            b = int(30 + 50 * (y/720))
            draw.line([(0,y),(1280,y)], fill=(r,g,b))
        img.save(raw)
        print("Gradient background generated")

    # Now composite branding
    img = Image.open(raw).convert("RGBA").resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.65)
    
    # Dark overlays for text
    ov = Image.new("RGBA", (1280, 720), (0,0,0,0))
    d = ImageDraw.Draw(ov)
    for y in range(220):
        d.line([(0,y),(1280,y)], fill=(0,0,0, int(200*(1-y/220))))
    for y in range(540, 720):
        d.line([(0,y),(1280,y)], fill=(0,0,0, int(220*((y-540)/180))))
    img = Image.alpha_composite(img, ov)
    draw = ImageDraw.Draw(img)

    def font(sz, bold=False):
        for p in ([r"C:\Windows\Fonts\segoeuib.ttf"] if bold else [r"C:\Windows\Fonts\segoeui.ttf",r"C:\Windows\Fonts\arial.ttf"]):
            if os.path.exists(p): return ImageFont.truetype(p, sz)
        return ImageFont.load_default()

    tf = font(72, True)
    sf = font(22)
    bf = font(18, True)
    ff = font(16, True)
    vf = font(14)

    title = "C O R T E X"
    bb = draw.textbbox((0,0), title, font=tf)
    tw = bb[2]-bb[0]
    tx, ty = (1280-tw)//2, 50

    # Glow
    gl = Image.new("RGBA",(1280,720),(0,0,0,0))
    gd = ImageDraw.Draw(gl)
    for r in range(15,0,-2):
        a = int(12*(1-r/15))
        for dx in range(-r,r+1,3):
            for dy in range(-r,r+1,3):
                gd.text((tx+dx,ty+dy), title, font=tf, fill=(0,230,255,a))
    img = Image.alpha_composite(img, gl)
    draw = ImageDraw.Draw(img)
    draw.text((tx+2,ty+2), title, font=tf, fill=(0,180,220,200))
    draw.text((tx,ty), title, font=tf, fill=(255,255,255,255))

    # PRO badge
    bx, by = tx+tw+20, ty+25
    draw.rounded_rectangle([bx-8,by-4,bx+50,by+22], radius=6, fill=(0,200,255,180))
    draw.text((bx,by), "PRO", font=bf, fill=(0,0,0,255))

    # Tagline
    tag = "Universal Intelligence Platform  |  55 Domain Packs  |  Autonomous Analysis"
    tb = draw.textbbox((0,0),tag,font=sf)
    draw.text(((1280-(tb[2]-tb[0]))//2, ty+95), tag, font=sf, fill=(180,220,255,220))

    # Feature pills
    feats = [("OSINT",(0,200,255)),("CYBER",(0,255,150)),("FINANCIAL",(255,200,0)),
             ("LEGAL",(200,150,255)),("CORPORATE",(255,100,100)),("HEALTHCARE",(100,255,200))]
    sx = (1280 - len(feats)*155 + 15)//2
    for i,(lab,c) in enumerate(feats):
        fx = sx + i*155
        fy = 655
        lb = draw.textbbox((0,0),lab,font=ff)
        lw = lb[2]-lb[0]
        pw = max(lw+30,130)
        draw.rounded_rectangle([fx,fy,fx+pw,fy+32], radius=16, fill=(*c,40), outline=(*c,150), width=1)
        draw.text((fx+(pw-lw)//2, fy+6), lab, font=ff, fill=(*c,230))

    draw.text((1200,692), "v1.0.0", font=vf, fill=(120,120,140,180))

    pro = os.path.join(OUT, "cortex_pro_cover_ai.png")
    img.convert("RGB").save(pro, "PNG", quality=95)
    sz = os.path.getsize(pro)
    print(f"\nSaved: {pro}")
    print(f"Size: {sz:,} bytes (1280x720)")
    print("Upload this to your Gumroad listing!")

if __name__ == "__main__":
    main()
