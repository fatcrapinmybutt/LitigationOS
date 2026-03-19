import zipfile
import os
from pathlib import Path
import hashlib
import shutil
from datetime import datetime

# === CONFIGURATION ===
BASE_DIR = Path("/mnt/data")
DEPLOYMENT_FOLDER = BASE_DIR / "STRIKEBACK_CYCLE3_FULL_DEPLOYMENT_LOG"
ZIP_FILE = BASE_DIR / "STRIKEBACK_CYCLE3_FULL_DEPLOYMENT_LOG.zip"

# === FILES TO INCLUDE ===
INCLUDE_EXTENSIONS = {'.docx', '.pdf', '.txt', '.json', '.csv', '.log'}
HASH_LOG = DEPLOYMENT_FOLDER / "HASH_LOG_SHA256.txt"
TIMESTAMP_FILE = DEPLOYMENT_FOLDER / "DEPLOYMENT_TIMESTAMP.txt"

# === PRE-CLEANUP ===
if DEPLOYMENT_FOLDER.exists():
    shutil.rmtree(DEPLOYMENT_FOLDER)
DEPLOYMENT_FOLDER.mkdir(parents=True, exist_ok=True)

# === STEP 1: HASH AND COPY FILES ===
def hash_and_copy(file_path, target_dir):
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    hex_digest = hash_sha256.hexdigest()

    target = target_dir / file_path.name
    shutil.copy2(file_path, target)
    with open(HASH_LOG, 'a') as log:
        log.write(f"{file_path.name} — SHA256: {hex_digest}\n")

# === STEP 2: EXPORT FINAL LOGS ===
def write_timestamp():
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(f"Deployment completed at: {datetime.now().isoformat()}\n")

# === STEP 3: BUILD ZIP ARCHIVE ===
def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = Path(root) / file
                arcname = full_path.relative_to(folder_path)
                zipf.write(full_path, arcname)

# === MAIN ===
def deploy():
    print("[🔁] Starting STRIKEBACK Cycle 3 deployment...")

    # Simulated court-ready files (would be pulled from system in live mode)
    court_files = [
        "Motion_To_Pierce_Veil.docx",
        "Federal_Complaint_1983.pdf",
        "Service_Log.json",
        "Canon_Violation_Matrix.csv",
        "Cover_Letter_to_Clerk.docx",
        "Timeline_Overlay.pdf",
        "Auto_TOC_Index.txt",
        "Final_Audit_Trail.log"
    ]

    # Simulated file drop-in (in a real system, these would be pulled live)
    for file in court_files:
        dummy = DEPLOYMENT_FOLDER / file
        dummy.write_text(f"Simulated contents of {file}")
        hash_and_copy(dummy, DEPLOYMENT_FOLDER)

    write_timestamp()
    zip_folder(DEPLOYMENT_FOLDER, ZIP_FILE)

    print(f"[✅] Deployment complete. ZIP exported to:\n→ {ZIP_FILE}")

if __name__ == "__main__":
    deploy()
