#!/usr/bin/env python
"""Run _bisect.py and capture all output."""
import subprocess
import sys
import os

os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

print("Starting _bisect.py execution...", flush=True)
print("=" * 70, flush=True)

try:
    result = subprocess.run(
        [sys.executable, "tests\_bisect.py"],
        capture_output=False,
        text=True,
        timeout=700
    )
    print("=" * 70, flush=True)
    print(f"Script exit code: {result.returncode}", flush=True)
except subprocess.TimeoutExpired:
    print("TIMEOUT: Script did not complete within 700 seconds", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)

# Now try to read the output file
print("\n" + "=" * 70, flush=True)
print("Attempting to read _bisect_out.txt...", flush=True)
print("=" * 70 + "\n", flush=True)

output_file = r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_bisect_out.txt"
try:
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            print(content)
            print("\n" + "=" * 70, flush=True)
            print("END OF _bisect_out.txt", flush=True)
    else:
        print(f"FILE NOT FOUND: {output_file}", flush=True)
except Exception as e:
    print(f"ERROR reading file: {e}", flush=True)
