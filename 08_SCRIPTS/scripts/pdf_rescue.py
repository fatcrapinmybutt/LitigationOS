import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

WATCH_PATH = "F:/"
OUTPUT_DIR = "F:/LOCAL_FRED/processed_files/pdf_rescue"
LOG_FILE = "F:/FRED_file_watch.log"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()} - {msg}\n")

def convert_pdf_to_images(pdf_path, image_folder):
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            pix = doc[page_num].get_pixmap(dpi=300)
            output_image_path = os.path.join(image_folder, f"page_{page_num + 1}.png")
            pix.save(output_image_path)
        log(f"🖼 Converted PDF to images: {pdf_path}")
        return True
    except Exception as e:
        log(f"❌ Failed to convert PDF to images: {pdf_path} | {str(e)}")
        return False

def ocr_images_from_folder(folder_path, output_text_path):
    try:
        text = ""
        for image_file in sorted(os.listdir(folder_path)):
            if image_file.lower().endswith(".png"):
                image_path = os.path.join(folder_path, image_file)
                img = Image.open(image_path)
                text += pytesseract.image_to_string(img) + "\n"
        with open(output_text_path, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"✅ OCR completed for images in folder: {folder_path}")
    except Exception as e:
        log(f"❌ OCR failed in folder: {folder_path} | {str(e)}")

def rescue_pdf(pdf_path):
    try:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        image_folder = os.path.join(OUTPUT_DIR, base_name)
        os.makedirs(image_folder, exist_ok=True)
        success = convert_pdf_to_images(pdf_path, image_folder)
        if success:
            output_text_path = os.path.join(OUTPUT_DIR, base_name + "_rescued.txt")
            ocr_images_from_folder(image_folder, output_text_path)
    except Exception as e:
        log(f"❌ Unexpected failure rescuing PDF: {pdf_path} | {str(e)}")

def scan_for_broken_pdfs(path):
    log("===== PDF RESCUE SCAN STARTED =====")
    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                rescue_pdf(full_path)
    log("===== PDF RESCUE SCAN COMPLETE =====")

if __name__ == "__main__":
    scan_for_broken_pdfs(WATCH_PATH)