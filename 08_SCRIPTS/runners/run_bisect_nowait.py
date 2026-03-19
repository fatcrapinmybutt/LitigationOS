#!/usr/bin/env python
"""Run _bisect.py and wait for output file."""
import subprocess
import sys
import os
import time

os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

# Start the bisect process
print("Starting _bisect.py...", flush=True)
proc = subprocess.Popen(
    [sys.executable, "tests\_bisect.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for output file
outfile = r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_bisect_out.txt"
wait_start = time.time()
max_wait = 650

while True:
    elapsed = time.time() - wait_start
    if os.path.exists(outfile):
        print(f"\nOutput file found after {elapsed:.1f}s", flush=True)
        break
    
    if elapsed > max_wait:
        print(f"\nTimeout waiting for output file after {elapsed:.1f}s", flush=True)
        try:
            proc.kill()
        except:
            pass
        break
    
    print(f"Waiting... {elapsed:.0f}s", flush=True)
    time.sleep(5)

# Wait for process to finish
try:
    stdout, stderr = proc.communicate(timeout=10)
    print(f"\nProcess exited with code: {proc.returncode}", flush=True)
except subprocess.TimeoutExpired:
    print("\nProcess still running after timeout", flush=True)
    proc.kill()

# Read and print output file
time.sleep(1)
if os.path.exists(outfile):
    print("\n" + "="*70, flush=True)
    print("CONTENTS OF _bisect_out.txt:", flush=True)
    print("="*70 + "\n", flush=True)
    try:
        with open(outfile, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            print(content, flush=True)
    except Exception as e:
        print(f"ERROR reading file: {e}", flush=True)
    print("\n" + "="*70, flush=True)
else:
    print(f"\nOUTPUT FILE NOT FOUND: {outfile}", flush=True)
