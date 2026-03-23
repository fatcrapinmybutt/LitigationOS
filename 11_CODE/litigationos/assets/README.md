# LitigationOS Assets

## Logo Placement

Place brand logos and icons in this directory. The app resolves assets via
`branding.py` constants `ICON_PATH` and `LOGO_PATH`, which point to the
**package-level** `src/litigationos/assets/` directory at runtime.

This top-level `assets/` directory holds the icon generator and build-time
source files. At install time, copy final artifacts into the package assets.

### Required Files

| File | Format | Purpose | Placement |
|------|--------|---------|-----------|
| `mbp_pig_logo.ico` | ICO (256×256 multi-res) | MBP LLC pig logo — window/taskbar icon | `src/litigationos/assets/` |
| `mbp_pig_logo.png` | PNG (512×512) | MBP LLC pig logo — splash/about screen | `src/litigationos/assets/` |
| `icon.ico` | ICO (256×256 multi-res) | Fallback scales-of-justice icon | This directory |
| `icon.png` | PNG (512×512) | Source icon for other platforms | This directory |
| `splash.png` | PNG (600×400) | Optional splash screen image | This directory |

### Runtime Resolution

```python
from litigationos.branding import ICON_PATH, LOGO_PATH

# These resolve to absolute paths under src/litigationos/assets/
# e.g., C:\...\src\litigationos\assets\mbp_pig_logo.ico
```

### Theme-Aware Assets

Themes defined in `branding.THEMES` can reference different logo variants.
The `"default"` theme uses the scales-of-justice icon; the `"mbp"` theme
uses the pig logo.

## Generating `icon.ico`

From a 512×512 PNG source:

```bash
pip install Pillow
python -c "
from PIL import Image
img = Image.open('icon.png')
img.save('icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
"
```

Or use the programmatic generator:

```bash
python icon.py
```
