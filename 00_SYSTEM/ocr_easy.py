import os, sys

img = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\Screenshot_20260218_212004_One UI Home.jpg"

if not os.path.exists(img):
    print(f"IMAGE NOT FOUND: {img}")
    sys.exit(1)

print(f"Image found: {img}")
print(f"File size: {os.path.getsize(img)} bytes")

# Try EasyOCR
try:
    import easyocr
    print("Initializing EasyOCR reader...")
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("Running OCR...")
    result = reader.readtext(img, detail=0)  # detail=0 returns only text
    text = '\n'.join(result)
    print("=== OCR EXTRACTED TEXT ===")
    print(text)
except Exception as e:
    print(f"EasyOCR failed: {e}")
    import traceback
    traceback.print_exc()
