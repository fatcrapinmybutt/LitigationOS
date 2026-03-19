import os
import shutil
from difflib import get_close_matches

ROOT_DIR = "F:\\"
LOG_FILE = os.path.join(ROOT_DIR, "move_log.txt")
existing_folders = [f for f in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, f))]

ext_folder_map = {
    '.docx': ['docs', 'documents', 'word'],
    '.pdf': ['pdf', 'documents'],
    '.xlsx': ['excel', 'sheets'],
    '.jpg': ['images', 'pictures', 'photos'],
    '.png': ['images', 'pictures', 'photos'],
    '.mp4': ['videos'],
    '.zip': ['zips', 'archives'],
    '.py': ['scripts', 'python'],
    '.ps1': ['powershell', 'scripts'],
    '.txt': ['text', 'logs'],
}

def log_move(src, dst):
    with open(LOG_FILE, 'a') as f:
        f.write(f"MOVED: {src} --> {dst}\n")

for item in os.listdir(ROOT_DIR):
    full_path = os.path.join(ROOT_DIR, item)
    if os.path.isfile(full_path):
        file_ext = os.path.splitext(item)[1].lower()
        base_name = os.path.splitext(item)[0]
        candidates = []
        if file_ext in ext_folder_map:
            for keyword in ext_folder_map[file_ext]:
                matches = get_close_matches(keyword, existing_folders, cutoff=0.6)
                candidates.extend(matches)
        matches = get_close_matches(base_name.lower(), existing_folders, n=1, cutoff=0.7)
        candidates.extend(matches)
        candidates = list(set(candidates))
        if candidates:
            target_folder = os.path.join(ROOT_DIR, candidates[0])
            target_path = os.path.join(target_folder, item)
            try:
                shutil.move(full_path, target_path)
                log_move(full_path, target_path)
                print(f"Moved: {item} -> {target_folder}")
            except Exception as e:
                print(f"Error moving {item}: {e}")
        else:
            print(f"Skipped: {item} (no matching folder)")
