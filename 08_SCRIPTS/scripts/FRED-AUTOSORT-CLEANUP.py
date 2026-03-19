import os
import shutil
import zipfile
from pathlib import Path

# ========== CONFIG ==========
TARGET_DRIVE = "F:\\"
BASE_FOLDER = os.path.join(TARGET_DRIVE, "FRED-PRIME")
EMPTY_ARCHIVE = os.path.join(BASE_FOLDER, "Z_EMPTY_ARCHIVE")
MAX_FOLDERS = 100
MIN_FOLDERS = 50
SUBFOLDERS_PER_MAIN = 5
MAX_DEPTH = 3
# ============================

# Rule-based keyword mappings for categories
CATEGORY_KEYWORDS = {
    "Medical": ["vaccination", "pediatrics", "dentist", "medical"],
    "Police": ["police", "report", "sheriff", "incident"],
    "Custody": ["custody", "visitation", "parenting_time"],
    "PPO": ["ppo", "protection", "restraining"],
    "Financial": ["paystub", "insurance", "support", "bank", "income"],
    "Contempt": ["violation", "compliance", "contempt"],
    "LT": ["rent", "landlord", "eviction", "shady", "hoa"],
    "Witness": ["statement", "affidavit", "recommendation", "letter"],
    "AppClose": ["appclose", "communication", "co-parenting"],
    "Timeline": ["log", "timeline", "date"],
    "Photos": [".jpg", ".jpeg", ".png"],
    "Video": [".mp4", ".mov", ".avi"],
    "LegalDocs": [".pdf", ".docx", ".txt"],
    "FalseAllegations": ["false", "accusation", "perjury"],
    "JudicialBias": ["judge", "bias", "disqualify", "muted"],
    "Discovery": ["discovery", "subpoena", "interrogatories"],
    "Surveillance": ["camera", "footage", "surveil"],
    "Emails": ["email", "gmail", "outlook"],
}

def get_category(filename):
    name = filename.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return category
    return "Uncategorized"

def unpack_zips(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".zip"):
                zip_path = os.path.join(root, file)
                extract_to = os.path.join(root, Path(file).stem)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_to)
                    os.remove(zip_path)
                except Exception as e:
                    print(f"❌ Failed to extract {zip_path}: {e}")

def create_directory_tree():
    categories = list(CATEGORY_KEYWORDS.keys()) + ["Uncategorized"]
    folders_needed = max(MIN_FOLDERS, min(len(categories) * SUBFOLDERS_PER_MAIN, MAX_FOLDERS))

    created_paths = []
    for cat in categories:
        cat_folder = os.path.join(BASE_FOLDER, f"FRED-MODULE_{cat}")
        os.makedirs(cat_folder, exist_ok=True)
        created_paths.append(cat_folder)
        for i in range(1, SUBFOLDERS_PER_MAIN + 1):
            sub = os.path.join(cat_folder, f"Section-{i}")
            os.makedirs(sub, exist_ok=True)
            created_paths.append(sub)
    return created_paths

def organize_files():
    for root, _, files in os.walk(TARGET_DRIVE):
        if BASE_FOLDER.lower() in root.lower():
            continue
        for file in files:
            file_path = os.path.join(root, file)
            cat = get_category(file)
            dest_dir = os.path.join(BASE_FOLDER, f"FRED-MODULE_{cat}", "Section-1")
            os.makedirs(dest_dir, exist_ok=True)
            try:
                shutil.move(file_path, os.path.join(dest_dir, file))
            except Exception as e:
                print(f"❌ Couldn't move {file_path}: {e}")

def archive_empty_dirs():
    os.makedirs(EMPTY_ARCHIVE, exist_ok=True)
    for root, dirs, _ in os.walk(BASE_FOLDER, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                try:
                    dest = os.path.join(EMPTY_ARCHIVE, os.path.basename(dir_path))
                    shutil.move(dir_path, dest)
                except Exception as e:
                    print(f"❌ Couldn't move empty folder {dir_path}: {e}")

# ========== MAIN EXECUTION ==========
print("🧠 Unpacking ZIPs...")
unpack_zips(TARGET_DRIVE)

print("🧱 Building folder structure...")
create_directory_tree()

print("📂 Organizing files...")
organize_files()

print("🧹 Archiving empty folders...")
archive_empty_dirs()

print("✅ COMPLETED: All files organized. Empty folders moved to Z_EMPTY_ARCHIVE.")
