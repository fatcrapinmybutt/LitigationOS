"""
FRED-PRIME | Exhibit Intake Engine
Master control script to ingest, log, and route exhibits for legal processing.
"""

import os
import json
from categorization_core import categorize_file
from trigger_mapper import map_triggers
from manifest_writer import update_manifest
from quality_checker import perform_quality_check
from error_logger import log_error

INPUT_DIR = "F:/FRED-LITIGATION-OS/Exhibit Intake/Ingest"
MANIFEST_PATH = "F:/FRED-LITIGATION-OS/Exhibit Intake/manifest.json"

def main():
    try:
        exhibits = os.listdir(INPUT_DIR)
        for exhibit in exhibits:
            full_path = os.path.join(INPUT_DIR, exhibit)
            if not os.path.isfile(full_path):
                continue

            category = categorize_file(full_path)
            triggers = map_triggers(full_path)
            update_manifest(MANIFEST_PATH, exhibit, category, triggers)
            perform_quality_check(full_path)

    except Exception as e:
        log_error(str(e))

if __name__ == "__main__":
    main()