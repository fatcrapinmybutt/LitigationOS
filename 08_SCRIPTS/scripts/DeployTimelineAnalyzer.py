
import os
from pathlib import Path
from datetime import datetime
import re

# Define root directory to scan
root_dir = Path("F:/OMNILITIGATION_SYSTEM")

# Output path
output_file = Path("F:/OMNILITIGATION_SYSTEM/MiFILE_READY/Timeline_Report.txt")

# Date extraction pattern
date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})|((\d{1,2})[/-](\d{1,2})[/-](\d{2,4}))')

# Accumulator
timeline = []

# Walk all files and try to extract date references from filenames
for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        filepath = Path(dirpath) / filename
        match = date_pattern.search(filename)
        if match:
            try:
                if match.group(1):
                    date_obj = datetime.strptime(match.group(1), "%Y-%m-%d")
                else:
                    parts = match.group(2).split('/')
                    parts = [int(p) for p in parts]
                    if len(str(parts[2])) == 2:
                        parts[2] += 2000
                    date_obj = datetime(parts[2], parts[0], parts[1])
                timeline.append((date_obj, filename, str(filepath)))
            except:
                continue

# Sort chronologically
timeline.sort()

# Write to file
with open(output_file, "w") as f:
    f.write("LITIGATION TIMELINE REPORT\n")
    f.write("="*80 + "\n\n")
    for dt, fname, path in timeline:
        f.write(f"{dt.strftime('%Y-%m-%d')}: {fname} -> {path}\n")

print(f"🧠 Timeline report written to {output_file}")
