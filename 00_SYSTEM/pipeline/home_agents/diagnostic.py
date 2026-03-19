#!/usr/bin/env python3
import os
import time

SOURCE_DIRS = [
    'C:\\Users\\andre\\Music',
    'C:\\Users\\andre\\Scans'
]

print("Starting file discovery...")
start = time.time()
file_count = 0

for source_dir in SOURCE_DIRS:
    if not os.path.exists(source_dir):
        print(f"Not found: {source_dir}")
        continue
    
    print(f"\nScanning {source_dir}...")
    for root, dirs, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.lower().endswith(('.md', '.txt')):
                file_count += 1
                if file_count % 1000 == 0:
                    print(f"  Found {file_count} files so far... ({time.time()-start:.1f}s)")
        
        if time.time() - start > 60:  # timeout after 60 seconds
            print("TIMEOUT - stopping search")
            exit(1)

elapsed = time.time() - start
print(f"\nTotal files found: {file_count} in {elapsed:.1f}s")
