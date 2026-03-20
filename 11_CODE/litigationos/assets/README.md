# LitigationOS Assets

Place the following files in this directory:

| File | Format | Purpose |
|------|--------|---------|
| `icon.ico` | ICO (256×256, 128, 64, 48, 32, 16) | Windows executable and taskbar icon |
| `icon.png` | PNG (512×512) | Source icon for other platforms |
| `splash.png` | PNG (600×400) | Optional splash screen image |

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
