
import os
import shutil
import asyncio
import concurrent.futures
from pathlib import Path
import hashlib
import json

# Configuration
ROOT_DIR = "F:/"
DEST_DIR = "F:/Organized"
CHECKPOINT_FILE = "F:/organizer_checkpoint.json"
IGNORED_EXTENSIONS = {'.tmp', '.log', '.ini', '.ds_store', '.sys'}

# Async-safe hash function
def sha256_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read(4096)).hexdigest()
    except:
        return None

# Load progress
def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {}

# Save progress
def save_checkpoint(data):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f)

# Classify and move file
def classify_and_move_file(path, processed):
    ext = Path(path).suffix.lower()
    if ext in IGNORED_EXTENSIONS or path in processed:
        return

    if not os.path.isfile(path):
        return

    category = ext[1:].upper() if ext else "UNKNOWN"
    dest_folder = os.path.join(DEST_DIR, category)
    os.makedirs(dest_folder, exist_ok=True)
    filename = os.path.basename(path)
    dest_path = os.path.join(dest_folder, filename)

    if not os.path.exists(dest_path):
        try:
            shutil.copy2(path, dest_path)
            processed[path] = sha256_file(path)
        except Exception as e:
            print(f"Failed to process {path}: {e}")

# Async walk and process files
async def organize_files():
    processed = load_checkpoint()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        for root, dirs, files in os.walk(ROOT_DIR):
            tasks = []
            for name in files:
                full_path = os.path.join(root, name)
                tasks.append(loop.run_in_executor(executor, classify_and_move_file, full_path, processed))
            await asyncio.gather(*tasks)
            save_checkpoint(processed)

if __name__ == "__main__":
    asyncio.run(organize_files())
