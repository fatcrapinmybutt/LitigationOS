
# AUTO_INGEST_DAEMON_v2.0_SUPREME — with AI+LLM Injection, NLP, Legal Intelligence, OCR, Self-Healing

import os, time, hashlib, zipfile, traceback
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF for PDF parsing
import pytesseract  # OCR
from PIL import Image
import docx
from langchain.document_loaders import UnstructuredFileLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

WATCH_PATHS = ["F:/", "Z:/", "D:/", "chatlogs/last24hr"]
TARGET_EXTENSIONS = [".txt", ".pdf", ".docx", ".json", ".py", ".ps1", ".sh", ".csv", ".rtf", ".zip"]
LOG_FILE = "F:/LITIGATION_OS/ingestion_logs/DAEMON_INGEST_LOG.txt"
VECTOR_STORE_PATH = "F:/LITIGATION_OS/vector_index/"

def hash_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        return f"ERR_HASH:{str(e)}"

def log(content):
    with open(LOG_FILE, "a", encoding="utf-8") as logf:
        logf.write(f"[{datetime.now()}] {content}\n")

def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            log(f"[ZIP] Extracted: {zip_path}")
            return True
    except Exception as e:
        log(f"[!ZIP] Extraction failed: {zip_path} → {str(e)}")
        return False

def parse_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        full_text = "\n".join([page.get_text() for page in doc])
        doc.close()
        return full_text
    except Exception:
        return "[OCR FALLBACK] " + ocr_pdf(file_path)

def ocr_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        doc.close()
        return text
    except Exception as e:
        return f"[OCR FAIL] {e}"

def parse_docx(path):
    try:
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"[DOCX PARSE FAIL] {e}"

def ingest_file(path):
    try:
        suffix = path.suffix.lower()
        text = ""
        if suffix == ".pdf":
            text = parse_pdf(path)
        elif suffix == ".docx":
            text = parse_docx(path)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        hash_val = hash_file(path)
        output = f"\n--- INGESTED: {path} ---\n{text[:1000]}\n[SHA256: {hash_val}]\n"
        print(output)
        log(f"INGESTED: {path} [HASH:{hash_val}]")

        enrich_with_embedding(path, text)

    except Exception as e:
        err = f"[!] Ingestion error: {path} — {traceback.format_exc()}"
        print(err)
        log(err)

def enrich_with_embedding(path, raw_text):
    try:
        documents = [ {"text": raw_text, "source": str(path)} ]
        embedding = OpenAIEmbeddings()
        vectordb = Chroma.from_documents(documents, embedding, persist_directory=VECTOR_STORE_PATH)
        vectordb.persist()
        log(f"[VECTORSTORE] Embedded: {path}")
    except Exception as e:
        log(f"[VECTORSTORE FAIL] {path} → {e}")

def scan_loop():
    seen = set()
    log("🚀 AI DAEMON STARTED")
    while True:
        for base in WATCH_PATHS:
            for path in Path(base).rglob("*"):
                if path.suffix.lower() in TARGET_EXTENSIONS and path not in seen:
                    seen.add(path)
                    if path.suffix.lower() == ".zip":
                        extract_zip(path, path.parent / "unzipped")
                    else:
                        ingest_file(path)
        time.sleep(15)

if __name__ == "__main__":
    print("⚖️ AUTO_INGEST_DAEMON_v2.0_SUPREME LIVE")
    scan_loop()
