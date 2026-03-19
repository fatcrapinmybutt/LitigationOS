
import os
import shutil
from pathlib import Path

BASE_DIR = Path("F:/")  # Update for actual mount on your system if different
DEST_DIR = Path("F:/FRED-PRIME-SORTED")

def is_empty_folder(path):
    return path.is_dir() and not any(path.iterdir())

def organize_files():
    if not DEST_DIR.exists():
        DEST_DIR.mkdir(parents=True)

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            src = Path(root) / file
            if not src.is_file():
                continue
            extension = src.suffix.lower().replace(".", "") or "unknown"
            target_dir = DEST_DIR / extension.upper()
            target_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, target_dir / src.name)
            except Exception as e:
                print(f"⚠ Failed to move {src}: {e}")

    # Remove empty folders recursively
    for root, dirs, files in os.walk(BASE_DIR, topdown=False):
        for d in dirs:
            folder = Path(root) / d
            if is_empty_folder(folder) and folder != DEST_DIR:
                try:
                    folder.rmdir()
                except Exception as e:
                    print(f"⚠ Couldn't delete {folder}: {e}")

    print("✅ Organization complete. Sorted into:", DEST_DIR)

if __name__ == "__main__":
    organize_files()
