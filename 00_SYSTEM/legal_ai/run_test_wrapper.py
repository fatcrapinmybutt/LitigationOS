#!/usr/bin/env python
"""Wrapper to run the test and ensure output is written"""
import os
import sys
import subprocess

# Set environment variables
os.environ["PYTHONUTF8"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

# Change to the legal_ai directory
os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai')

# Run the actual test script
result = subprocess.run([sys.executable, 'tests/_run_fileonly.py'])
sys.exit(result.returncode)
