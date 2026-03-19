#!/usr/bin/env python3
"""Simple test runner to diagnose test execution."""
import sys
import subprocess
import os

os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

# Test 1: Python diagnostic
print("=" * 70)
print("1. PYTHON DIAGNOSTIC")
print("=" * 70)
print(f"Executable: {sys.executable}")
print(f"Version: {sys.version}")
print()

# Test 2: Run a single test
print("=" * 70)
print("2. RUNNING SINGLE TEST")
print("=" * 70)
cmd = [
    sys.executable, "-m", "pytest",
    "tests/test_new_modules.py::TestOpinionParser::test_parse_empty_text_returns_warning",
    "-v", "--tb=short", "-x", "-q", "--timeout=60"
]
print(f"Command: {' '.join(cmd)}")
print()

try:
    result = subprocess.run(cmd, capture_output=False, text=True, timeout=120)
    print(f"\nExit code: {result.returncode}")
except subprocess.TimeoutExpired:
    print("\nERROR: Test timed out after 120 seconds")
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
