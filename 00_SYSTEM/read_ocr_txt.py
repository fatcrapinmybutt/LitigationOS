"""Read OCR-extracted .txt files that have massive whitespace, extract actual text."""
import os, re, sys

FILES = [
    r"D:\EVIDENCE\SRC-00039.txt",
    r"J:\ROOT_CLEANUP\DOCUMENTS\circuit court docket mcneill custody.txt",
    r"J:\ROOT_CLEANUP\DOCUMENTS\2023_5907_ppThewholestory_TEXT(1).txt.extracted(0).txt",
    r"J:\ROOT_CLEANUP\DOCUMENTS\Exhibit_F_PPO_Docket_Pages (1)(0).txt",
]

for fpath in FILES:
    print(f"\n{'='*80}")
    print(f"FILE: {fpath}")
    print(f"SIZE: {os.path.getsize(fpath):,} bytes")
    print(f"{'='*80}")
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        # Collapse runs of whitespace
        cleaned = re.sub(r'\s+', ' ', raw).strip()
        # Show first 3000 chars
        if len(cleaned) < 50:
            print("[EMPTY OR WHITESPACE-ONLY FILE]")
        else:
            print(f"CLEANED LENGTH: {len(cleaned):,} chars")
            print(f"FIRST 3000 CHARS:\n{cleaned[:3000]}")
            print(f"\n... LAST 1000 CHARS:\n{cleaned[-1000:]}")
    except Exception as e:
        print(f"ERROR: {e}")
