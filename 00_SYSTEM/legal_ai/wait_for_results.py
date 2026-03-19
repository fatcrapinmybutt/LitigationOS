#!/usr/bin/env python
"""Monitor for test results and print them"""
import os
import time
import sys

results_path = r'C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_all_results.txt'
max_wait = 1200  # 20 minutes
check_interval = 10
elapsed = 0

print("Waiting for test results file...")
sys.stdout.flush()

while elapsed < max_wait:
    if os.path.exists(results_path):
        print(f"\n✓ Results file found at {results_path}")
        with open(results_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("\n" + "="*80)
        print("TEST RESULTS:")
        print("="*80 + "\n")
        print(content)
        sys.exit(0)
    
    elapsed += check_interval
    remaining = max_wait - elapsed
    print(f"  Waiting... ({elapsed}s/{max_wait}s)")
    sys.stdout.flush()
    time.sleep(check_interval)

print(f"\n✗ Results file not found after {max_wait} seconds")
sys.exit(1)
