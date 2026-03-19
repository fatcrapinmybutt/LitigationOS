
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from datetime import datetime

# === CONFIGURATION ===
SOURCE_DIR = Path("F:/")
LOG_PATH = Path("F:/OMNILITIGATION_SYSTEM/AIExecutionLogs/async_scan_log.json")
HASH_CACHE = {}

# === FUNCTION DEFINITIONS ===

def sha256sum(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def process_file(filepath):
    try:
        file_stat = filepath.stat()
        file_info = {
            "path": str(filepath),
            "size": file_stat.st_size,
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "hash": sha256sum(filepath),
            "ext": filepath.suffix.lower(),
        }
        return file_info
    except Exception as e:
        return {"path": str(filepath), "error": str(e)}

def scan_files(root_dir):
    all_files = [Path(dp) / f for dp, dn, filenames in os.walk(root_dir) for f in filenames]
    results = []

    with ThreadPoolExecutor(max_workers=32) as executor:
        future_to_file = {executor.submit(process_file, f): f for f in all_files}
        for future in as_completed(future_to_file):
            result = future.result()
            results.append(result)

    return results

def save_log(entries):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)

# === MAIN EXECUTION ===

def main():
    print("🔎 Starting async scan of F:/")
    results = scan_files(SOURCE_DIR)
    save_log(results)
    print(f"✅ Scan complete. {len(results)} files logged to: {LOG_PATH}")

if __name__ == "__main__":
    main()
