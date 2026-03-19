
import os
import time
import zipfile
import subprocess

# Install and import required libraries
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
except ImportError:
    subprocess.check_call(["pip", "install", "pytesseract", "pillow", "PyMuPDF"])
    import pytesseract
    from PIL import Image
    import fitz

WATCH_PATH = "F:\\"
PROCESSED_DIR = "F:\\LOCAL_FRED\\processed_files"
LOG_FILE = "F:\\FRED_file_watch.log"
EXTRACTED_ZIPS_DIR = os.path.join(PROCESSED_DIR, "archives")
PDF_RESCUE_SCRIPT = "F:\\pdf_rescue.py"  # <<<<<< FIXED PATH

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(EXTRACTED_ZIPS_DIR, exist_ok=True)

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} - {msg}\n")

def process_pdf(file_path, out_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for i, page in enumerate(doc):
            try:
                text += page.get_text()
            except Exception as e:
                log(f"⚠️ Page {i+1} failed in {file_path}: {str(e)}")
        if not text.strip():
            raise ValueError("Empty content extracted from PDF.")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"✅ Processed PDF: {file_path}")
    except Exception as e:
        log(f"❌ Error processing PDF {file_path}: {str(e)}")
        # Auto-trigger PDF rescue
        try:
            subprocess.Popen(["python", PDF_RESCUE_SCRIPT])
            log(f"🚨 Triggered PDF rescue for: {file_path}")
        except Exception as se:
            log(f"❌ Failed to trigger PDF rescue: {str(se)}")

def process_image(file_path, out_path):
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"✅ Processed image: {file_path}")
    except Exception as e:
        log(f"❌ Error processing image {file_path}: {str(e)}")

def process_zip(file_path):
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            extract_path = os.path.join(EXTRACTED_ZIPS_DIR, os.path.basename(file_path).replace('.zip', ''))
            os.makedirs(extract_path, exist_ok=True)
            zip_ref.extractall(extract_path)
            log(f"📦 Extracted archive: {file_path}")
            process_all_files(extract_path)
    except Exception as e:
        log(f"❌ Error extracting zip {file_path}: {str(e)}")

def process_all_files(start_path):
    seen_files = set()
    for root, _, files in os.walk(start_path):
        for file in files:
            full_path = os.path.join(root, file)
            if full_path in seen_files:
                continue
            seen_files.add(full_path)
            log(f"📄 Found file: {full_path}")
            lower = file.lower()
            out_file = os.path.join(PROCESSED_DIR, os.path.basename(file) + ".txt")
            if lower.endswith(".pdf"):
                process_pdf(full_path, out_file)
            elif lower.endswith((".png", ".jpg", ".jpeg")):
                process_image(full_path, out_file)
            elif lower.endswith(".zip"):
                process_zip(full_path)
            else:
                log(f"⏩ Skipped unsupported file type: {file}")

def full_scan_and_process():
    log("===== FULL SCAN + ANALYSIS STARTED =====")
    process_all_files(WATCH_PATH)
    log("===== FULL SCAN + ANALYSIS COMPLETE =====")

if __name__ == "__main__":
    print("📂 Starting full scan of F:\\ drive...")
    full_scan_and_process()
    print("✅ Done. Log written to F:\\FRED_file_watch.log")
