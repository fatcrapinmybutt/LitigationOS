import subprocess, sys, os

img = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\Screenshot_20260218_212004_One UI Home.jpg"

if not os.path.exists(img):
    print(f"IMAGE NOT FOUND: {img}")
    # Search for it
    import glob
    for f in glob.glob(r"C:\Users\andre\Desktop\**\*VanDam*", recursive=True):
        print(f"Found: {f}")
    for f in glob.glob(r"C:\Users\andre\Desktop\**\*20260218*", recursive=True):
        print(f"Found: {f}")
    for f in glob.glob(r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\*.jpg"):
        print(f"SHADY jpg: {f}")
    sys.exit(1)

# Try pytesseract first
try:
    import pytesseract
    from PIL import Image
    img_obj = Image.open(img)
    text = pytesseract.image_to_string(img_obj)
    print("pytesseract SUCCESS:")
    print(text)
except Exception as e:
    print(f"pytesseract failed: {e}")
    # Try paddleocr
    try:
        from paddleocr import PaddleOCR
        print("Initializing PaddleOCR...")
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        print("Running OCR...")
        result = ocr.ocr(img, cls=True)
        lines = []
        if result:
            for line in result:
                if line:
                    for word_info in line:
                        if word_info and len(word_info) >= 2:
                            lines.append(str(word_info[1][0]))
        text = '\n'.join(lines)
        print("PaddleOCR SUCCESS:")
        print(text)
    except Exception as e2:
        print(f"PaddleOCR also failed: {e2}")
        import traceback
        traceback.print_exc()
