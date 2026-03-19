
#!/usr/bin/env python3
# FRED_OMNIORGANIZER_SUPRA.py
# SUPRA-MAX AI Drive Organizer for Litigation System

import os, hashlib, json, shutil, subprocess, sys
from datetime import datetime

# Dependency check and install
REQUIRED_PACKAGES = ['python-docx', 'PyMuPDF', 'pdfminer.six', 'extract-msg', 'spacy']

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Failed to install {package}: {e}")

for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg.replace('-', '_').split('.')[0])
    except ImportError:
        print(f"Installing missing package: {pkg}")
        install_package(pkg)

from docx import Document
import csv

# CONFIGURABLES
ROOT_DRIVES = ["F:/", "D:/"]
OUTPUT_ROOT = "F:/Litigation_Organized_SUPRA/"
BACKUP_ROOT = "F:/_ORIGINAL_UNTOUCHED/"
LOG_DIR = os.path.join(OUTPUT_ROOT, "Logs/")
SYSTEM_DIR = os.path.join(OUTPUT_ROOT, "By_System_Build/")
SUPPORTED_EXTENSIONS = [".docx", ".pdf", ".txt", ".msg", ".eml", ".py", ".json", ".ps1", ".bat", ".spec"]

# Ensure folders exist
for path in [OUTPUT_ROOT, BACKUP_ROOT, LOG_DIR, SYSTEM_DIR]:
    os.makedirs(path, exist_ok=True)

# Helper: SHA256 file hash
def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as file:
        while chunk := file.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Helper: Extract text from docx
def extract_docx_text(filepath):
    try:
        doc = Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

# Rule matching engine
def rule_matches(text):
    matches = []
    if "served less than 7 days" in text or "short notice" in text:
        matches.append("MCR_3.708")
    if "denied parenting time" in text:
        matches.append("MCL_600.2950")
    if "no criminal findings" in text and "police" in text:
        matches.append("Benchbook_3.5")
    return matches

# Weaponization score (0–10)
def score_text(text):
    score = 0
    triggers = [
        "denied access", "coercion", "false police report", "PPO", "parenting time",
        "contempt", "no evidence", "threat", "emergency motion", "served improperly"
    ]
    for t in triggers:
        if t in text.lower():
            score += 1
    return min(score, 10)

# Determine destination folder(s)
def get_destinations(file_path, matches, score):
    dests = []
    filename = os.path.basename(file_path)
    if "PPO" in filename:
        dests.append(os.path.join(OUTPUT_ROOT, "By_Case/PPO_2023-5907-PP/"))
    if "custody" in filename.lower():
        dests.append(os.path.join(OUTPUT_ROOT, "By_Case/CUSTODY_2024-1507-DC/"))
    if "shady" in filename.lower() or "rent" in filename.lower():
        dests.append(os.path.join(OUTPUT_ROOT, "By_Case/HOUSING_2025-25061626LT/"))
    if score >= 8:
        dests.append(os.path.join(OUTPUT_ROOT, f"By_Weaponization_Level/Level_{score}/"))
    for match in matches:
        if match.startswith("MCR"):
            dests.append(os.path.join(OUTPUT_ROOT, "By_Legal_Violation/MCR/", match + "/"))
        elif match.startswith("MCL"):
            dests.append(os.path.join(OUTPUT_ROOT, "By_Legal_Violation/MCL/", match + "/"))
    return dests if dests else [os.path.join(OUTPUT_ROOT, "Unsorted/")]

# Main scan loop
def scan_and_organize():
    chain_log = []
    for root_drive in ROOT_DRIVES:
        for dirpath, _, files in os.walk(root_drive):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                full_path = os.path.join(dirpath, file)
                file_hash = hash_file(full_path)
                timestamp = datetime.now().isoformat()

                # Backup original
                backup_path = os.path.join(BACKUP_ROOT, file)
                if not os.path.exists(backup_path):
                    shutil.copy2(full_path, backup_path)

                # Determine if system file
                if ext in [".py", ".json", ".ps1", ".bat", ".spec"]:
                    subdir = "Python" if ext == ".py" else "JSON" if ext == ".json" else "PowerShell"
                    sys_dest = os.path.join(SYSTEM_DIR, subdir)
                    os.makedirs(sys_dest, exist_ok=True)
                    shutil.move(full_path, os.path.join(sys_dest, file))
                    continue

                # Analyze content
                text = extract_docx_text(full_path) if ext == ".docx" else ""
                matches = rule_matches(text)
                score = score_text(text)
                dests = get_destinations(full_path, matches, score)

                for dest in dests:
                    os.makedirs(dest, exist_ok=True)
                    shutil.copy2(full_path, os.path.join(dest, file))

                chain_log.append({
                    "filename": file,
                    "hash": file_hash,
                    "origin": full_path,
                    "timestamp": timestamp,
                    "destinations": dests,
                    "score": score,
                    "rule_matches": matches
                })

    # Save logs
    with open(os.path.join(LOG_DIR, "CHAIN_LOG.csv"), "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=chain_log[0].keys())
        writer.writeheader()
        writer.writerows(chain_log)
    with open(os.path.join(LOG_DIR, "MASTER_INDEX.json"), "w") as jf:
        json.dump(chain_log, jf, indent=2)

if __name__ == "__main__":
    scan_and_organize()
