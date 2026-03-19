#!/usr/bin/env python3
"""
Ultra-simple test runner - no subprocess, direct pytest call with output capture.
"""
import os
import sys
import io

# Set environment
os.environ["PYTHONUTF8"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Change to correct directory
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

# Output file
out_file = r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\test_results_output.txt"

# Open file and redirect stdout/stderr
with open(out_file, "w", encoding="utf-8", errors="replace") as f:
    f.write("=" * 70 + "\n")
    f.write("TEST RUN STARTING\n")
    f.write("=" * 70 + "\n")
    f.write(f"CWD: {os.getcwd()}\n")
    f.write(f"Python: {sys.version}\n\n")
    
    # Flush
    f.flush()
    
    # Capture stdout/stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    try:
        sys.stdout = f
        sys.stderr = f
        
        import pytest
        
        f.write(f"pytest version: {pytest.__version__}\n\n")
        f.flush()
        
        # Run tests
        exit_code = pytest.main([
            "tests/test_new_modules.py::TestOpinionParser",
            "tests/test_new_modules.py::TestBrainEvolver",
            "tests/test_new_modules.py::TestCrossBrainOptimizer",
            "tests/test_new_modules.py::TestLegalRAGEngine",
            "tests/test_new_modules.py::TestLegalReranker",
            "tests/test_new_modules.py::TestRAGEvaluator",
            "-v",
            "--tb=short",
        ])
        
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        f.write(f"\n{'=' * 70}\n")
        f.write(f"Exit code: {exit_code}\n")
        f.write(f"Test run completed\n")
        f.write(f"{'=' * 70}\n")
        
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        f.write(f"\nERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())

print(f"Test results written to: {out_file}")
print("Done!")
