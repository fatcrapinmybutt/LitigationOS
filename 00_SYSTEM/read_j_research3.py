"""Read J: research files - strip whitespace artifacts, find real text."""
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
    
    # Check encoding - look for BOM or null bytes (UTF-16)
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        text = raw.decode('utf-16', errors='replace')
    elif b'\x00' in raw[:100]:
        text = raw.decode('utf-16-le', errors='replace')
    else:
        text = raw.decode('utf-8', errors='replace')
    
    # Strip and analyze
    stripped = text.strip()
    
    # Find first non-whitespace character position
    first_char_pos = -1
    for i, c in enumerate(text):
        if not c.isspace():
            first_char_pos = i
            break
    
    # Find actual text by collapsing runs of spaces
    # Replace tabs and multiple spaces with single space, preserve newlines
    cleaned = re.sub(r'[^\S\n]+', ' ', text)  # collapse horizontal whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # collapse excessive newlines
    cleaned = cleaned.strip()
    
    print(f"\n{'='*80}")
    print(f"FILE: {os.path.basename(fpath)}")
    print(f"SIZE: {size:,} bytes | Raw chars: {len(text):,}")
    print(f"First non-space at position: {first_char_pos}")
    print(f"Cleaned length: {len(cleaned):,} chars")
    print(f"First 20 raw bytes: {raw[:20]}")
    print(f"{'='*80}")
    
    # Print first 5000 chars of cleaned content
    print(cleaned[:5000])
    print(f"\n... [END OF PREVIEW - {len(cleaned):,} total cleaned chars]")
    print()
