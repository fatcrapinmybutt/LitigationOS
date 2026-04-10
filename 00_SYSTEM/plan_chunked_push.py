"""Analyze diff between origin/main and HEAD to plan chunked commits."""
import subprocess, collections, os

os.chdir(r"C:\Users\andre\LitigationOS")

# Get all changed files (disable rename detection for speed)
result = subprocess.run(
    ["git", "diff", "--name-only", "-M0", "6911aa7fb", "HEAD"],
    capture_output=True, text=True, timeout=120
)

files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
print(f"Total changed files: {len(files)}")

# Count by top-level directory
top_dirs = collections.Counter()
second_dirs = collections.Counter()
for f in files:
    parts = f.split('/')
    top_dirs[parts[0]] += 1
    if len(parts) >= 2:
        second_dirs[f"{parts[0]}/{parts[1]}"] += 1
    else:
        second_dirs[parts[0]] += 1

print("\n=== TOP-LEVEL DIRECTORIES ===")
for d, count in top_dirs.most_common():
    print(f"  {count:>7,}  {d}/")

print("\n=== SECOND-LEVEL (top 30) ===")
for d, count in second_dirs.most_common(30):
    print(f"  {count:>7,}  {d}/")

# Plan chunks: target ~5000-10000 files per commit
print("\n=== PROPOSED CHUNKING ===")
chunks = []
current_chunk = []
current_count = 0
MAX_PER_CHUNK = 8000

# Sort by top dir to group related changes
sorted_dirs = sorted(top_dirs.items(), key=lambda x: -x[1])
for d, count in sorted_dirs:
    if current_count + count > MAX_PER_CHUNK and current_chunk:
        chunks.append((current_chunk[:], current_count))
        current_chunk = []
        current_count = 0
    current_chunk.append(d)
    current_count += count

if current_chunk:
    chunks.append((current_chunk, current_count))

for i, (dirs, count) in enumerate(chunks):
    print(f"\n  Chunk {i+1}: ~{count:,} files")
    for d in dirs:
        print(f"    - {d}/ ({top_dirs[d]:,})")
