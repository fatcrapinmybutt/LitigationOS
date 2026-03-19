
import os
import zipfile
from pathlib import Path

def scan_f_drive():
    target_extensions = ['.pdf', '.docx', '.txt', '.zip']
    scan_results = []

    for root, dirs, files in os.walk("F:/"):
        for file in files:
            if any(file.lower().endswith(ext) for ext in target_extensions):
                full_path = os.path.join(root, file)
                scan_results.append(full_path)

    results_file = Path("scan_results.txt")
    with results_file.open("w", encoding="utf-8") as f:
        for line in scan_results:
            f.write(f"{line}
")

    print(f"Scan complete. {len(scan_results)} files found.")

if __name__ == "__main__":
    scan_f_drive()
