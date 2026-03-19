"""
Updates the master manifest JSON with metadata about exhibits.
"""

import json
import os

def update_manifest(manifest_path, filename, category, triggers):
    if not os.path.exists(manifest_path):
        with open(manifest_path, 'w') as f:
            json.dump([], f)

    with open(manifest_path, 'r') as f:
        data = json.load(f)

    record = {
        "filename": filename,
        "category": category,
        "triggers": triggers
    }
    data.append(record)

    with open(manifest_path, 'w') as f:
        json.dump(data, f, indent=2)