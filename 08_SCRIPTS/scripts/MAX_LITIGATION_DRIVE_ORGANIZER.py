
import os
import shutil
from pathlib import Path
import hashlib
import json
from datetime import datetime

# === CONFIGURATION ===
SOURCE_ROOT = Path("F:/")
DEST_ROOT = Path("F:/OMNILITIGATION_SYSTEM")
LOG_PATH = DEST_ROOT / "AIExecutionLogs" / "organizer_log.json"

# === STRUCTURE MAP ===
CATEGORIES = {
    "Leases_Contracts": ["lease", "rental", "agreement"],
    "Utility_Ledgers": ["ledger", "utility", "zego", "bill"],
    "CourtOrders_Judgments": ["order", "judgment", "disposition"],
    "Photos_MetadataAnchored": [".jpg", ".png", ".jpeg"],
    "Communications_Text_Email_AppClose": ["appclose", "text", "sms", "email"],
    "Affidavits_SwornStatements": ["affidavit", "sworn", "statement"],
    "EvidenceUnclassified_AuditQueue": []
}

# === FUNCTION DEFINITIONS ===

def get_category(filename):
    name = filename.name.lower()
    for category, keywords in CATEGORIES.items():
        if any(kw in name for kw in keywords):
            return category
    return "EvidenceUnclassified_AuditQueue"

def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def log_entry(entry):
    if not LOG_PATH.parent.exists():
        LOG_PATH.parent.mkdir(parents=True)
    if LOG_PATH.exists():
        with open(LOG_PATH, "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def process_file(filepath):
    category = get_category(filepath)
    target_dir = DEST_ROOT / "EvidenceRepository" / "ByLegalType" / category
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = filepath.name
    target_file = target_dir / filename

    if not target_file.exists():
        shutil.copy2(filepath, target_file)
        hashval = hash_file(filepath)
        log_entry({
            "original_path": str(filepath),
            "copied_to": str(target_file),
            "hash": hashval,
            "timestamp": datetime.now().isoformat(),
            "category": category
        })

# === MAIN ORGANIZER ===

def main():
    print("📁 Scanning and organizing F:/")
    for root, dirs, files in os.walk(SOURCE_ROOT):
        for file in files:
            try:
                filepath = Path(root) / file
                if filepath.is_file():
                    process_file(filepath)
            except Exception as e:
                print(f"❌ Error processing {file}: {e}")

    print("✅ File organization complete. Logs saved to AIExecutionLogs.")

if __name__ == "__main__":
    main()
