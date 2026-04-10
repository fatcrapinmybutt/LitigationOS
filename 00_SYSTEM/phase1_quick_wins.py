"""Phase 1C+1D: Quick space recovery — cache purge, __pycache__ removal, WAL checkpoint."""
import os, sys, sqlite3, subprocess, shutil, glob

REPO = r"C:\Users\andre\LitigationOS"
os.chdir(REPO)

recovered = 0.0

# --- 1D: WAL Checkpoint ---
print("=" * 60)
print("[1D] WAL CHECKPOINT")
print("=" * 60)

wal_dbs = []
for root, dirs, files in os.walk(REPO):
    # Skip .git, pytools_venv, .mcp_venv
    dirs[:] = [d for d in dirs if d not in ('.git', 'pytools_venv', '.mcp_venv', 'node_modules', '11_ARCHIVES')]
    for f in files:
        if f.endswith('.db-wal'):
            db_path = os.path.join(root, f[:-4])  # Remove -wal suffix
            if os.path.exists(db_path):
                wal_size = os.path.getsize(os.path.join(root, f))
                wal_dbs.append((db_path, wal_size))

print(f"Found {len(wal_dbs)} WAL files")
for db_path, wal_size in sorted(wal_dbs, key=lambda x: -x[1]):
    wal_mb = wal_size / (1024*1024)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=30000")
        result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        conn.close()
        new_wal = os.path.getsize(db_path + "-wal") if os.path.exists(db_path + "-wal") else 0
        saved = (wal_size - new_wal) / (1024*1024)
        recovered += saved
        rel = os.path.relpath(db_path, REPO)
        print(f"  [OK] {rel}: {wal_mb:.1f} MB WAL -> saved {saved:.1f} MB")
    except Exception as e:
        rel = os.path.relpath(db_path, REPO)
        print(f"  [WARN] {rel}: {e}")

# Also checkpoint root-level DBs
for db_name in ['litigation_context.db', 'mbp_brain.db']:
    db_path = os.path.join(REPO, db_name)
    wal_path = db_path + "-wal"
    if os.path.exists(wal_path):
        wal_size = os.path.getsize(wal_path)
        wal_mb = wal_size / (1024*1024)
        if wal_mb > 0.1:
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("PRAGMA busy_timeout=60000")
                result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
                conn.close()
                new_wal = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
                saved = (wal_size - new_wal) / (1024*1024)
                recovered += saved
                print(f"  [OK] {db_name}: {wal_mb:.1f} MB WAL -> saved {saved:.1f} MB")
            except Exception as e:
                print(f"  [WARN] {db_name}: {e}")

# --- 1C: __pycache__ removal ---
print()
print("=" * 60)
print("[1C] __pycache__ REMOVAL")
print("=" * 60)

pycache_count = 0
pycache_size = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in ('.git', 'pytools_venv', '.mcp_venv', 'node_modules', '11_ARCHIVES')]
    if os.path.basename(root) == '__pycache__':
        size = sum(os.path.getsize(os.path.join(root, f)) for f in files if os.path.isfile(os.path.join(root, f)))
        pycache_size += size
        pycache_count += 1
        try:
            shutil.rmtree(root)
        except Exception:
            pass

pycache_mb = pycache_size / (1024*1024)
recovered += pycache_mb
print(f"  Removed {pycache_count} __pycache__ dirs ({pycache_mb:.1f} MB)")

# --- 1C: .pyc files outside __pycache__ ---
pyc_count = 0
pyc_size = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in ('.git', 'pytools_venv', '.mcp_venv', 'node_modules', '11_ARCHIVES')]
    for f in files:
        if f.endswith('.pyc'):
            fp = os.path.join(root, f)
            pyc_size += os.path.getsize(fp)
            pyc_count += 1
            try:
                os.remove(fp)
            except Exception:
                pass

pyc_mb = pyc_size / (1024*1024)
recovered += pyc_mb
if pyc_count:
    print(f"  Removed {pyc_count} stray .pyc files ({pyc_mb:.1f} MB)")

# --- 1C: Temp files in D:\LitigationOS_tmp older than 7 days ---
print()
print("=" * 60)
print("[1C] TEMP FILE AUDIT")
print("=" * 60)

tmp_dir = r"D:\LitigationOS_tmp"
if os.path.exists(tmp_dir):
    tmp_files = os.listdir(tmp_dir)
    print(f"  D:\\LitigationOS_tmp: {len(tmp_files)} files (keeping all — temp is on D:, not C:)")

# --- Check .SHM files ---
shm_size = 0
for root, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in ('.git', 'pytools_venv', '.mcp_venv', 'node_modules', '11_ARCHIVES')]
    for f in files:
        if f.endswith('.db-shm'):
            fp = os.path.join(root, f)
            shm_size += os.path.getsize(fp)

shm_mb = shm_size / (1024*1024)
print(f"  SHM files: {shm_mb:.1f} MB (managed by SQLite, no action needed)")

# --- Summary ---
print()
print("=" * 60)
print(f"PHASE 1C+1D TOTAL RECOVERED: {recovered:.1f} MB ({recovered/1024:.2f} GB)")
print("=" * 60)

# --- Check C: free space after ---
import ctypes
free_bytes = ctypes.c_ulonglong(0)
ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("C:\\"), None, None, ctypes.pointer(free_bytes))
free_gb = free_bytes.value / (1024**3)
print(f"C: drive free space now: {free_gb:.2f} GB")
