import pytesseract
from PIL import Image
import os
import fitz  # PyMuPDF

# Ensure Tesseract is installed and in your PATH or explicitly set here:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

input_dir = "F:/FRED-PRIME/OCR_Input"
output_dir = "F:/FRED-PRIME/EvidenceMatrix"
log_file = os.path.join(output_dir, "ocr_extraction_log.txt")

os.makedirs(output_dir, exist_ok=True)
ocr_log = []

def extract_from_image(file_path):
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text.strip()

def extract_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def save_text(filename, content):
    txt_path = os.path.join(output_dir, f"{filename}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

for file in os.listdir(input_dir):
    path = os.path.join(input_dir, file)
    name, ext = os.path.splitext(file)
    extracted = ""
    try:
        if ext.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tif"]:
            extracted = extract_from_image(path)
        elif ext.lower() == ".pdf":
            extracted = extract_from_pdf(path)
        if extracted:
            save_text(name, extracted)
            ocr_log.append(f"SUCCESS: {file} extracted.")
        else:
            ocr_log.append(f"WARNING: No text extracted from {file}.")
    except Exception as e:
        ocr_log.append(f"ERROR: Failed to process {file}: {str(e)}")

# Write log file
with open(log_file, "w", encoding="utf-8") as log:
    log.write("\n".join(ocr_log))

print("OCR scan complete. Results saved to EvidenceMatrix folder.")
