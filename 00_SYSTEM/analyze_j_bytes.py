"""Analyze actual byte content of J: research files."""
import os
from collections import Counter

files = [
    r"J:\HOLY SHIT 2 CHAT RESEARCH (1).txt",
    r"J:\all chat researches combined 1.txt",
    r"J:\CHAT RESEARCH ON THE RIGHT TRACK-dup1.txt",
    r"J:\RESEARCH MOTION TO CONVERT.docx.txt",
    r"J:\DIAMOND 9999DEEP RESEARCH PROMPT FOR LITIGATION OS  FRED_CEPS_SUPREME(1).txt",
    r"J:\DIAMOND 9999DEEP RESEARCH PROMPT FOR LITIGATION OS  FRED_CEPS_SUPREME.txt",
]

for fpath in files:
    size = os.path.getsize(fpath)
    with open(fpath, 'rb') as fh:
        raw = fh.read()
    
    # Count byte frequencies
    byte_counts = Counter(raw)
    top5 = byte_counts.most_common(5)
    
    # Count null bytes specifically
    null_count = byte_counts.get(0, 0)
    space_count = byte_counts.get(0x20, 0)
    unique_bytes = len(byte_counts)
    
    print(f"\nFILE: {os.path.basename(fpath)}")
    print(f"  Size: {size:,} bytes")
    print(f"  Null bytes (0x00): {null_count:,} ({null_count*100/size:.1f}%)")
    print(f"  Space bytes (0x20): {space_count:,} ({space_count*100/size:.1f}%)")
    print(f"  Unique byte values: {unique_bytes}")
    print(f"  Top 5 bytes: {[(hex(b), cnt) for b, cnt in top5]}")
    
    # Find first non-null, non-space byte
    for i, b in enumerate(raw[:10000]):
        if b not in (0x00, 0x20, 0x0a, 0x0d, 0x09):
            print(f"  First printable byte at offset {i}: 0x{b:02x} = '{chr(b) if 32 <= b < 127 else '?'}'")
            # Print 200 bytes from there
            snippet = raw[i:i+200]
            try:
                print(f"  Snippet: {snippet.decode('utf-8', errors='replace')[:200]}")
            except:
                print(f"  Snippet (hex): {snippet[:50].hex()}")
            break
    else:
        # Check deeper
        for i, b in enumerate(raw):
            if b not in (0x00, 0x20, 0x0a, 0x0d, 0x09):
                print(f"  First printable byte at offset {i}: 0x{b:02x} = '{chr(b) if 32 <= b < 127 else '?'}'")
                snippet = raw[i:i+200]
                print(f"  Snippet: {snippet.decode('utf-8', errors='replace')[:200]}")
                break
        else:
            print(f"  FILE IS 100% WHITESPACE/NULL - NO PRINTABLE CONTENT")
