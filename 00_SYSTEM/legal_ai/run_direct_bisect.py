#!/usr/bin/env python3
"""Direct test execution and file writing."""
import sys
import os
import subprocess
import time

os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai")

output_file = os.path.join(os.getcwd(), "tests", "_bisect_direct_out.txt")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("DIRECT BISECT RUN\n")
    f.write("=" * 70 + "\n\n")
    
    classes = [
        "TestOpinionParser",
        "TestBrainEvolver",
        "TestCrossBrainOptimizer",
        "TestLegalRAGEngine",
        "TestLegalReranker",
        "TestRAGEvaluator",
    ]
    
    for cls in classes:
        f.write(f"\n{'='*60}\nRUNNING: {cls}\n{'='*60}\n")
        f.flush()
        
        t0 = time.time()
        try:
            # Set environment variables
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["TRANSFORMERS_OFFLINE"] = "1"
            env["HF_HUB_OFFLINE"] = "1"
            
            result = subprocess.run(
                [sys.executable, "-m", "pytest",
                 f"tests/test_new_modules.py::{cls}",
                 "-v", "--tb=short", "-x", "--no-header", "-q"],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            elapsed = time.time() - t0
            
            f.write(f"Exit code: {result.returncode} in {elapsed:.1f}s\n")
            f.write(f"STDOUT:\n{result.stdout[-2000:]}\n")
            if result.stderr:
                f.write(f"STDERR (last 500):\n{result.stderr[-500:]}\n")
        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - t0
            f.write(f"TIMEOUT after {elapsed:.1f}s — THIS CLASS HANGS!\n")
        except Exception as ex:
            elapsed = time.time() - t0
            f.write(f"ERROR after {elapsed:.1f}s: {type(ex).__name__}: {ex}\n")
        
        f.flush()
    
    f.write("\n" + "=" * 70 + "\n")
    f.write("DONE\n")

print(f"Output written to: {output_file}")
print(f"File exists: {os.path.exists(output_file)}")
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        print("\n" + "=" * 70)
        print("CONTENT:")
        print("=" * 70)
        print(f.read())
