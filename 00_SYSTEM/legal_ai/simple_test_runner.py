#!/usr/bin/env python3
import sys
import os

# Add the directory to path
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai')

# Set environment variables
os.environ["PYTHONUTF8"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# Change directory
os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai')

# Import and run the test script
print("Starting test execution...", flush=True)
sys.stdout.flush()

try:
    # Import the test module
    from tests import _run_fileonly
    print("Test module imported successfully", flush=True)
except ImportError as e:
    print(f"Import error: {e}", flush=True)
    # Try direct execution
    exec(open(r'C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_run_fileonly.py').read())
