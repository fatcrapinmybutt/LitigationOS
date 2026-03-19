#!/usr/bin/env python3
import os
import sys

target_dir = r"C:\Users\andre\LitigationOS\00_SYSTEM\ai_modules\rag_brief_gen\tests"
try:
    os.makedirs(target_dir, exist_ok=True)
    print("DONE")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
