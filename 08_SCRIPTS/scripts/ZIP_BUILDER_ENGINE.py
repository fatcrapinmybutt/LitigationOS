
import zipfile
import os

def build_mifile_zip(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                zipf.write(full_path, os.path.relpath(full_path, folder_path))

if __name__ == "__main__":
    build_mifile_zip("F:/TO_BE_FILED", "F:/MIFILE_PACK.zip")
