"""Read J: research files - handle null bytes and binary formats."""
import os, re

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
    with open(fpath, 'rb') as fh:
        raw = fh.read()
    
    # Strategy: strip all null bytes, then decode
    no_nulls = raw.replace(b'\x00', b'')
    
    # Try UTF-8 decode on null-stripped content
    text = no_nulls.decode('utf-8', errors='replace')
    
    # Collapse whitespace
    cleaned = re.sub(r'[ \t]+', ' ', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    # Write cleaned version to temp
    out_path = os.path.join(r"D:\LitigationOS_tmp", f"CLEANED_{label}.txt")
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(cleaned)
    
    print(f"\n{'='*80}")
    print(f"FILE: {os.path.basename(fpath)}")
    print(f"RAW: {size:,} bytes | Null bytes: {raw.count(b'\\x00'):,} | After strip: {len(no_nulls):,}")
    print(f"Cleaned text: {len(cleaned):,} chars")
    print(f"Saved to: {out_path}")
    print(f"{'='*80}")
    
    if len(cleaned) < 50:
        print(f"[EFFECTIVELY EMPTY after cleaning]")
        continue
    
    # Print first 6000 chars
    print(cleaned[:6000])
    print(f"\n... [{len(cleaned):,} total chars]")
