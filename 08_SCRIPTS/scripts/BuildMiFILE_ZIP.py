
from zipfile import ZipFile
from pathlib import Path
import datetime

folders = [
    "F:/OMNILITIGATION_SYSTEM/AffidavitDrafts/",
    "F:/OMNILITIGATION_SYSTEM/VerifiedComplaints/",
    "F:/OMNILITIGATION_SYSTEM/ProposedOrders/",
    "F:/OMNILITIGATION_SYSTEM/MotionsToShowCause/"
]

output_zip = f"F:/OMNILITIGATION_SYSTEM/MiFILE_READY/MiFILE_BUNDLE_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

def build_zip():
    zipf = ZipFile(output_zip, 'w')
    for folder in folders:
        folder_path = Path(folder)
        if folder_path.exists():
            for file in folder_path.glob("*.*"):
                zipf.write(file, arcname=file.name)
    zipf.close()
    print(f"📦 MiFILE bundle created at: {output_zip}")

if __name__ == "__main__":
    build_zip()
