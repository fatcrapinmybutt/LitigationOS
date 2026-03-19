#!/usr/bin/env python3
"""Direct test runner with guaranteed file output"""
import sys
import os
import time
import subprocess

# Set environment variables
os.environ["PYTHONUTF8"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# Ensure output directory exists
script_dir = os.path.dirname(os.path.abspath(__file__))
legal_ai_dir = os.path.dirname(script_dir)
tests_dir = os.path.join(legal_ai_dir, 'tests')
os.makedirs(tests_dir, exist_ok=True)

out_path = os.path.join(tests_dir, "_all_results.txt")

# Run the test script via subprocess
test_script = os.path.join(tests_dir, "_run_fileonly.py")

try:
    print(f"Running test from {legal_ai_dir}", file=sys.stderr, flush=True)
    print(f"Test script: {test_script}", file=sys.stderr, flush=True)
    
    result = subprocess.run(
        [sys.executable, test_script],
        cwd=legal_ai_dir,
        capture_output=False,
        text=True,
        env=os.environ
    )
    
    print(f"Test completed with exit code: {result.returncode}", file=sys.stderr, flush=True)
    
    # Try to read and display the results
    if os.path.exists(out_path):
        print(f"\nResults file found at: {out_path}", file=sys.stderr, flush=True)
        with open(out_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(content)
    else:
        print(f"Results file not found at: {out_path}", file=sys.stderr, flush=True)
        print("Listing directory contents:", file=sys.stderr, flush=True)
        for item in os.listdir(tests_dir):
            filepath = os.path.join(tests_dir, item)
            print(f"  {item} ({'dir' if os.path.isdir(filepath) else 'file'})", file=sys.stderr, flush=True)
            
except Exception as e:
    print(f"Error: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
