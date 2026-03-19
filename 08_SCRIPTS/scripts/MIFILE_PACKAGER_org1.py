import os, zipfile, logging
from pathlib import Path

logging.basicConfig(filename="F:/LITIGATION_DRIVE/LEGAL_RESULTS/log_mifile_packager.txt", level=logging.INFO)

def build_zip_package():
    try:
        src_dir = Path("F:/LITIGATION_DRIVE/OUTPUTS")
        zip_out = Path("F:/LITIGATION_DRIVE/ZIPS/mifile_package.zip")
        with zipfile.ZipFile(zip_out, 'w') as zipf:
            for file in src_dir.glob("*"):
                zipf.write(file, arcname=file.name)
        logging.info(f"[✓] MIFILE Package created: {zip_out}")
        Path("F:/SYSTEM/FLAGS/mifile_packager.done").touch()
    except Exception as e:
        logging.error(f"[!] MIFILE Package failed: {e}")

if __name__ == "__main__":
    build_zip_package()
