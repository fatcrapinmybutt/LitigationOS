import logging
import zipfile
from pathlib import Path
from datetime import datetime

def archive_system_state():
    try:
        dt = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"F:/LITIGATION_DRIVE/ARCHIVES/system_snapshot_{dt}.zip"
        base_dir = Path("F:/SYSTEM/FLAGS")
        logs_dir = Path("F:/LITIGATION_DRIVE/LEGAL_RESULTS")

        with zipfile.ZipFile(zip_name, "w") as z:
            for f in base_dir.glob("*.done"):
                z.write(f, arcname=f"FLAGS/{f.name}")
            for f in logs_dir.glob("log_*.txt"):
                z.write(f, arcname=f"LOGS/{f.name}")

        logging.basicConfig(filename="F:/LITIGATION_DRIVE/LEGAL_RESULTS/log_auto_archive.txt", level=logging.INFO)
        logging.info(f"System archived to {zip_name}")
        Path("F:/SYSTEM/FLAGS/auto_archive_engine.done").touch()
    except Exception as e:
        logging.error(f"Archival failed: {e}")

if __name__ == "__main__":
    archive_system_state()
