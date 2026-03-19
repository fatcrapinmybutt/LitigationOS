#!/usr/bin/env python3
"""Minimal test to verify pytest works."""
import subprocess
import sys
import os

os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

# Set environment
os.environ["PYTHONUTF8"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

output_path = r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_minimal_test_out.txt"

# Try running ONE test
cmd = [
    sys.executable, "-m", "pytest",
    "tests/test_new_modules.py::TestOpinionParser::test_parse_empty_text_returns_warning",
    "-xvs", "--tb=short", "--timeout=60"
]

try:
    print(f"Running: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
    
    # Write to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"MINIMAL TEST RUN\n")
        f.write(f"=" * 70 + "\n\n")
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"Exit Code: {result.returncode}\n\n")
        f.write(f"STDOUT:\n")
        f.write(result.stdout)
        f.write(f"\n\nSTDERR:\n")
        f.write(result.stderr)
        f.write(f"\n\nDONE\n")
    
    print(f"Output written to: {output_path}", flush=True)
    print(f"File size: {os.path.getsize(output_path)} bytes", flush=True)
    
    # Print content
    with open(output_path, "r", encoding="utf-8") as f:
        print("\n" + f.read(), flush=True)
        
except subprocess.TimeoutExpired:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("TEST TIMED OUT AFTER 120 SECONDS\n")
    print("TEST TIMED OUT", flush=True)
except Exception as e:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"ERROR: {type(e).__name__}: {e}\n")
    print(f"ERROR: {e}", flush=True)
