"""Read J:\ research files - handle single-line format."""
import os

files = [
    r"J:\HOLY SHIT 2 CHAT RESEARCH (1).txt",
    r"J:\all chat researches combined 1.txt",
    r"J:\CHAT RESEARCH ON THE RIGHT TRACK-dup1.txt",
    r"J:\RESEARCH MOTION TO CONVERT.docx.txt",
    r"J:\DIAMOND 9999DEEP RESEARCH PROMPT FOR LITIGATION OS  FRED_CEPS_SUPREME(1).txt",
    r"J:\DIAMOND 9999DEEP RESEARCH PROMPT FOR LITIGATION OS  FRED_CEPS_SUPREME.txt",
]

for f in files:
    if not os.path.exists(f):
        print(f"NOT FOUND: {f}")
        continue
    size = os.path.getsize(f)
    print(f"\n{'='*80}")
    print(f"FILE: {os.path.basename(f)}")
    print(f"SIZE: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"{'='*80}")
    
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    
    # Strip leading/trailing whitespace
    content = content.strip()
    
    # Check if it's mostly spaces (docx conversion artifact)
    non_space = len(content.replace(' ', ''))
    print(f"Total chars: {len(content):,} | Non-space chars: {non_space:,}")
    
    if non_space == 0:
        print("FILE IS EMPTY (only whitespace)")
        continue
    
    # Try to find actual text content by looking for runs of non-space chars
    # Split on multiple spaces to find text chunks
    import re
    # Find chunks of text (sequences of chars not separated by huge space runs)
    chunks = re.split(r'\s{3,}', content)
    real_chunks = [c.strip() for c in chunks if c.strip() and len(c.strip()) > 5]
    
    if real_chunks:
        print(f"Found {len(real_chunks)} text chunks")
        # Print first 5000 chars worth of chunks
        output = ""
        for chunk in real_chunks:
            if len(output) + len(chunk) > 8000:
                break
            output += chunk + "\n\n"
        print(output[:8000])
    else:
        # Maybe it's just one huge line - print first 5000 chars of non-space content
        # Try splitting on double-space as paragraph separator
        paragraphs = re.split(r'  +', content)
        real_paras = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 3]
        if real_paras:
            print(f"Found {len(real_paras)} paragraphs (double-space split)")
            output = "\n".join(real_paras[:200])
            print(output[:8000])
        else:
            print(f"FIRST 3000 chars: {content[:3000]}")
