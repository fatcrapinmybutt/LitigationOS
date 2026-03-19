
"""
FRED PRIME – MHLOP DRIVE INTELLIGENT ORGANIZER
Version: 4.0 (Refined)
"""

import os
import hashlib
import re
import fitz  # PyMuPDF
import shutil
import datetime
import pandas as pd

SOURCE_DIR = r'F:\__Organized\Scripts'
TARGET_DIR = r'F:\__Organized\FRED_RENAMED'
DUPLICATE_DIR = r'F:\__Organized\Duplicates'
LOG_FILE = r'F:\__Organized\OrganizeLog.csv'

def get_file_hash(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def extract_pdf_text(filepath):
    try:
        doc = fitz.open(filepath)
        return " ".join([page.get_text() for page in doc[:3]]).strip()
    except:
        return ""

def extract_code_text(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        block = ''.join(lines[:100])
        docstring = re.findall(r'"""(.*?)"""|\'\'\'(.*?)\'\'\'', block, re.DOTALL)
        comment_lines = [line for line in lines if line.strip().startswith(("#", "//"))]
        flattened_doc = " ".join([" ".join(pair) for pair in docstring])
        return f"{flattened_doc} {' '.join(comment_lines)}"
    except:
        return ""

def classify(content, ext, basename):
    cl = content.lower()
    base = basename.lower()
    now = datetime.datetime.now().strftime('%Y-%m-%d')

    match_map = [
        ('Legal__PPO_Evidence', ['ppo', 'personal protection order']),
        ('Legal__CustodyMotion', ['custody', 'parenting time']),
        ('Legal__SupportMotion', ['motion', 'support']),
        ('Legal__ContemptAllegation', ['contempt']),
        ('Model__YOLO_ObjectDetection', ['yolo', 'object detection']),
        ('Model__AudioClassifier', ['audio', 'classif']),
        ('Module__Quantization', ['quantizer']),
        ('Test__AutoTestCase', ['test', 'unit test']),
        ('Evidence__AppCloseTranscript', ['appclose']),
        ('Model__TrainingConfig', ['training arguments', 'trainer']),
        ('Model__ImageSegmentation', ['segmentation']),
        ('Model__ImageClassifier', ['image', 'classification']),
        ('Backend__PythonWebApp', ['flask', 'django']),
        ('Script__ExecutableCore', ['import os', 'def main']),
        ('Module__WebProxy', ['proxy']),
        ('Frontend__JavaScriptModule', ['.js']),
        ('Legal__CourtMotionPDF', ['pdf', 'motion', 'court']),
    ]

    for label, keywords in match_map:
        if all(keyword in cl or keyword in base for keyword in keywords):
            return f"{label}__{now}{ext}"
    return f"Unsorted__Unclassified__{now}{ext}"

def organize_files():
    os.makedirs(TARGET_DIR, exist_ok=True)
    os.makedirs(DUPLICATE_DIR, exist_ok=True)
    logs = []
    seen_hashes = {}

    for root, _, files in os.walk(SOURCE_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1]
            if not ext:
                continue

            hash_val = get_file_hash(fpath)
            if not hash_val:
                continue
            if hash_val in seen_hashes:
                try:
                    shutil.move(fpath, os.path.join(DUPLICATE_DIR, fname))
                except:
                    continue
                continue

            seen_hashes[hash_val] = fpath
            content = extract_pdf_text(fpath) if ext.lower() == '.pdf' else extract_code_text(fpath)
            new_name = classify(content, ext, fname)
            new_path = os.path.join(TARGET_DIR, new_name)

            base_name, ext_ = os.path.splitext(new_name)
            count = 1
            while os.path.exists(new_path):
                new_path = os.path.join(TARGET_DIR, f"{base_name}__v{count}{ext_}")
                count += 1

            try:
                shutil.move(fpath, new_path)
            except:
                continue

            logs.append({
                "Original Name": fname,
                "New Name": os.path.basename(new_path),
                "SHA256": hash_val,
                "Source Path": fpath,
                "Destination Path": new_path,
                "Content Snippet": content[:500].replace('\n', ' ')
            })

    pd.DataFrame(logs).to_csv(LOG_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    organize_files()
