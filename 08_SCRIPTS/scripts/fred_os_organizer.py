import os
import shutil
from datetime import datetime

BASE = "F:/FRED-PRIME"
STRUCTURE = {'MODULES': ['.docx'], 'SCRIPTS': ['.py', '.ps1'], 'DATABASE': ['.db'], 'DASHBOARDS': ['.html'], 'EXHIBITS': ['.pdf', '.png', '.jpg', '.jpeg'], 'ARCHIVE': [], 'MOTIONS': ['_motion', '_pleading'], 'DECLARATIONS': ['_declaration', '_affidavit'], 'ORDERS': ['_order', 'proposed_order'], 'EVIDENCE': ['evidence', '_exhibit'], 'TRANSCRIPTS': ['transcript', '.mp3', '.wav'], 'SYSTEM': ['.zip', '.log', '.exe']}

LOGFILE = os.path.join(BASE, "system_log.txt")

def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def ensure_structure():
    for folder in STRUCTURE:
        path = os.path.join(BASE, folder)
        os.makedirs(path, exist_ok=True)

def matches_criteria(file, ext, rules):
    lower = file.lower()
    return (
        ext in rules or
        any(key in lower for key in rules if isinstance(key, str))
    )

def scan_and_sort():
    for root, dirs, files in os.walk(BASE):
        for file in files:
            if file == "system_log.txt" or "LITIGATION-OS" in file:
                continue
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            placed = False
            for folder, rules in STRUCTURE.items():
                if matches_criteria(file, ext, rules):
                    dest = os.path.join(BASE, folder, file)
                    if os.path.abspath(full_path) != os.path.abspath(dest):
                        shutil.copy2(full_path, dest)
                        log(f"Moved: {full_path} -> {dest}")
                    placed = True
                    break
            if not placed:
                dest = os.path.join(BASE, "ARCHIVE", file)
                if os.path.abspath(full_path) != os.path.abspath(dest):
                    shutil.copy2(full_path, dest)
                    log(f"Archived: {full_path} -> {dest}")

def remove_empty_dirs():
    for root, dirs, _ in os.walk(BASE, topdown=False):
        for d in dirs:
            full_path = os.path.join(root, d)
            if not os.listdir(full_path):
                os.rmdir(full_path)
                log(f"Removed empty folder: {full_path}")

def main():
    log("=== FRED-PRIME OS ORGANIZER RUNNING ===")
    ensure_structure()
    scan_and_sort()
    remove_empty_dirs()
    log("=== FRED-PRIME OS ORGANIZER COMPLETE ===\n")

if __name__ == "__main__":
    main()