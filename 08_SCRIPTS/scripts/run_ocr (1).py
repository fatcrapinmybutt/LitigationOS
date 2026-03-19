import os
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from datetime import datetime

# ===== CONFIGURATION =====
DEBUG_MODE = True
DRY_RUN = False
OVERWRITE = False
TESSERACT_PATH = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Change if needed

# ===== PATHS =====
INPUT_DIR = "F:/FRED-PRIME/OCR_Input"
OUTPUT_DIR = "F:/FRED-PRIME/EvidenceMatrix"
LOG_PATH = os.path.join(OUTPUT_DIR, f"ocr_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

# ===== SETUP =====
os.makedirs(OUTPUT_DIR, exist_ok=True)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def log(message):
    if DEBUG_MODE:
        print(message)
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")

def extract_from_image(file_path):
    log(f"Extracting from image: {file_path}")
    img = Image.open(file_path)
    return pytesseract.image_to_string(img).strip()

def extract_from_pdf(file_path):
    log(f"Extracting from PDF: {file_path}")
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc]).strip()

def save_text(name, content):
    txt_path = os.path.join(OUTPUT_DIR, f"{name}.txt")
    if not OVERWRITE and os.path.exists(txt_path):
        log(f"Skipping {txt_path} (already exists)")
        return
    if not DRY_RUN:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)
        log(f"Saved extracted text to {txt_path}")

# ===== MAIN PROCESS =====
log("Starting OCR Scan...")
for file in os.listdir(INPUT_DIR):
    try:
        path = os.path.join(INPUT_DIR, file)
        name, ext = os.path.splitext(file)
        ext = ext.lower()
        text = ""
        if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tif"]:
            text = extract_from_image(path)
        elif ext == ".pdf":
            text = extract_from_pdf(path)
        else:
            log(f"Unsupported file type: {file}")
            continue
        if text:
            save_text(name, text)
        else:
            log(f"WARNING: No text found in {file}")
    except Exception as e:
        log(f"ERROR processing {file}: {e}")

log("OCR Scan Complete.")
