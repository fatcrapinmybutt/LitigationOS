import os
import shutil
import hashlib
import json
from datetime import datetime

# === GLOBAL CONFIG ===
SOURCE_DIR = "F:/"
DEST_DIR = os.path.join(SOURCE_DIR, "Litigation_Organized_SUPRA")
INDEX_LOG = os.path.join(SOURCE_DIR, "SystemModules", "F_SCAN_INDEX.json")

os.makedirs(DEST_DIR, exist_ok=True)
os.makedirs(os.path.dirname(INDEX_LOG), exist_ok=True)

# === HEURISTIC ROUTING ENGINE ===
def classify_file(path):
    name = path.lower()
    if "pp0" in name or "show_cause" in name:
        return "By_Case/PPO_2023-5907-PP"
    elif "custody" in name or "1507-dc" in name:
        return "By_Case/CUSTODY_1507-DC"
    elif "lt" in name or "lease" in name or "shady" in name:
        return "By_Case/HOUSING_25061626LT"
    elif "usps" in name or "termination" in name:
        return "By_Case/EMPLOYMENT_USPS"
    elif "motion" in name:
        return "By_Type/Motions"
    elif "order" in name:
        return "By_Type/Orders"
    elif "affidavit" in name:
        return "By_Type/Affidavits"
    elif "recommendation" in name:
        return "By_Type/Recommendations"
    elif "appclose" in name:
        return "By_Type/Communications/AppClose"
    elif "facebook" in name:
        return "By_Type/Communications/Facebook"
    elif "email" in name or "@":
        return "By_Type/Communications/Email"
    elif "transcript" in name:
        return "By_Type/Transcripts"
    elif "perjury" in name:
        return "By_Tactic/Perjury_Trails"
    elif "canon" in name:
        return "By_Tactic/Canon_Violations"
    elif "due_process" in name or "violation" in name:
        return "By_Tactic/Due_Process_Defenses"
    elif "contradiction" in name:
        return "By_Tactic/Contradictions"
    elif "1983" in name:
        return "By_Tactic/§1983_Prep"
    elif "binder" in name or "bundle" in name:
        return "By_Tactic/Strategic_Bundles"
    elif "police" in name:
        return "By_Type/Police_Reports"
    else:
        return "Unsorted"

# === HASH FUNCTION ===
def hash_file(filepath):
    try:
        with open(filepath, "rb") as f:
            sha256 = hashlib.sha256()
            while chunk := f.read(8192):
                sha256.update(chunk)
            return sha256.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"

# === MAIN FILE SCANNER ===
def route_files():
    index = []
    for root, _, files in os.walk(SOURCE_DIR):
        if root.startswith(DEST_DIR) or "SystemModules" in root:
            continue
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, SOURCE_DIR)
            try:
                routed_folder = classify_file(rel_path)
                routed_path = os.path.join(DEST_DIR, routed_folder)
                os.makedirs(routed_path, exist_ok=True)
                new_file_path = os.path.join(routed_path, file)

                # Avoid overwrite
                if not os.path.exists(new_file_path):
                    shutil.copy2(abs_path, new_file_path)

                stat = os.stat(abs_path)
                entry = {
                    "original": rel_path,
                    "classified_to": routed_folder,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "hash": hash_file(abs_path),
                    "routed_to": os.path.relpath(new_file_path, SOURCE_DIR)
                }
                index.append(entry)
                print(f"✅ Routed: {rel_path} ➜ {routed_folder}")
            except Exception as e:
                print(f"❌ Error processing {rel_path}: {e}")

    with open(INDEX_LOG, "w", encoding="utf-8") as log_file:
        json.dump(index, log_file, indent=2)
    print(f"\n🧾 Index log written to: {INDEX_LOG}")
    print(f"📦 Total files routed: {len(index)}")

# === EXECUTION ENTRY POINT ===
if __name__ == "__main__":
    print("🔍 FRED_SUPRA_FILE_ROUTER starting...\n")
    route_files()
    print("\n✅ SUPRA file routing complete.")
