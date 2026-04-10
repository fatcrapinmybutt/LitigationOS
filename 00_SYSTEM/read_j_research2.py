"""Read J: research files - dump actual content."""
import os

files = [
    (r"J:\HOLY SHIT 2 CHAT RESEARCH (1).txt", "HOLY_SHIT_2"),
    (r"J:\all chat researches combined 1.txt", "ALL_COMBINED"),
    (r"J:\CHAT RESEARCH ON THE RIGHT TRACK-dup1.txt", "RIGHT_TRACK"),
    (r"J:\RESEARCH MOTION TO CONVERT.docx.txt", "MOTION_CONVERT"),
    (r"J:\DIAMOND 9999DEEP RESEARCH PROMPT FOR LITIGATION OS  FRED_CEPS_SUPREME(1).txt", "DIAMOND_1"),
    (r"J:\DIAMOND 9999DEEP RESEARCH PROMPT FOR LITIGATION OS  FRED_CEPS_SUPREME.txt", "DIAMOND_2"),
]

for fpath, label in files:
    size = os.path.getsize(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
        text = fh.read().strip()
    
    # Write first 15000 chars to separate output file for review
    out = os.path.join(r"D:\LitigationOS_tmp", f"J_RESEARCH_{label}.txt")
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(text)
    
    print(f"\n{'='*80}")
    print(f"FILE: {os.path.basename(fpath)} ({size:,} bytes)")
    print(f"Written to: {out}")
    print(f"{'='*80}")
    # Print first 4000 chars to see what it contains
    print(text[:4000])
    print(f"\n... [{len(text):,} total chars]")
