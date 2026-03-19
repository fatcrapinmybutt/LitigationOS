import os
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# === CONFIGURATION ===
ARCHIVE_DIRS = [
    Path("D:/SCRIPTS/_ARCHIVE_ALL_PY"),
    Path("F:/")
]
OUTPUT_JSON = Path("D:/SCRIPTS/_ARCHIVE_ALL_PY/script_index.json")
ALLOWED_EXTENSIONS = [".py"]

# === ENSURE TARGET DIRECTORY EXISTS ===
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

# === ROLE + CATEGORY HEURISTICS ===
def infer_tags(filename: str):
    fname = filename.lower()
    if "gui" in fname or "dashboard" in fname:
        return "interface", "ui"
    elif "sync" in fname or "f_drive" in fname:
        return "sync_tool", "filesystem"
    elif "scan" in fname or "ocr" in fname:
        return "scanner", "evidence"
    elif "build" in fname or "zip" in fname:
        return "builder", "compiler"
    elif "log" in fname or "audit" in fname:
        return "auditor", "logging"
    elif "motion" in fname or "affidavit" in fname:
        return "litigation", "legal_doc"
    else:
        return "misc", "general"

# === RECURSIVE SCAN FUNCTION ===
def scan_scripts(directories):
    all_scripts = []
    for base_dir in directories:
        if base_dir.exists():
            all_scripts.extend(list(base_dir.rglob("*")))
    return [f for f in all_scripts if f.suffix.lower() in ALLOWED_EXTENSIONS]

# === BUILD INDEX ===
def build_script_index(files):
    index = []
    for f in tqdm(files, desc="🔍 Indexing Scripts"):
        try:
            role, category = infer_tags(f.name)
            stat = f.stat()
            index.append({
                "filename": f.name,
                "path": str(f.resolve()),
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "role": role,
                "category": category,
                "status": "indexed"
            })
        except Exception as e:
            print(f"⚠️ Error processing {f}: {e}")
    return index

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print(f"\n📦 Starting SUPRA Script Indexing into {OUTPUT_JSON}")
    script_files = scan_scripts(ARCHIVE_DIRS)
    index = build_script_index(script_files)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"\n✅ Completed. {len(index)} scripts indexed.\n📄 Output: {OUTPUT_JSON}")
