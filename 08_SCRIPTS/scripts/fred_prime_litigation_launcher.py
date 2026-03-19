#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "incoming_files")
TARGET_DIRS = {
    "motion": "motions",
    "order": "proposed_orders",
    "declaration": "declarations",
    "exhibit": "exhibits",
    "service": "certificates_of_service",
    "court": "court_orders",
    "log": "evidence_logs",
    "benchbook": "benchbook_references"
}

def classify_file(filename):
    name = filename.lower()
    for key in TARGET_DIRS:
        if key in name:
            return TARGET_DIRS[key]
    return None

def move_files():
    if not os.path.exists(SOURCE_DIR):
        print(f"No 'incoming_files' folder found at {SOURCE_DIR}")
        return

    for file in os.listdir(SOURCE_DIR):
        src = os.path.join(SOURCE_DIR, file)
        if os.path.isfile(src):
            category = classify_file(file)
            if category:
                dst_folder = os.path.join(BASE_DIR, category)
                shutil.move(src, os.path.join(dst_folder, file))
                print(f"Moved '{file}' to '{category}/'")
            else:
                print(f"Unclassified file: {file}")

if __name__ == "__main__":
    print("Launching FRED PRIME Litigation File Organizer...")
    move_files()
    print("All files processed.")
