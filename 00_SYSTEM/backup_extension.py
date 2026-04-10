"""Backup extension.mjs to scripts/ and verify."""
import shutil, hashlib, os

src = r"C:\Users\andre\LitigationOS\.github\extensions\singularity\extension.mjs"
dst = r"C:\Users\andre\LitigationOS\scripts\extension_v7.3.mjs"

shutil.copy2(src, dst)

# Verify
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

src_hash = sha(src)
dst_hash = sha(dst)
src_size = os.path.getsize(src)
dst_size = os.path.getsize(dst)

print(f"Source:  {src_size:,} bytes  sha256={src_hash}")
print(f"Backup:  {dst_size:,} bytes  sha256={dst_hash}")
print(f"Match: {'✅ YES' if src_hash == dst_hash else '❌ NO'}")
