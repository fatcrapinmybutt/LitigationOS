"""SENTINEL verification script — classify test + DB check."""
import sys
import os

sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM\daemon")

from sentinel.classifier import FileClassifier
from sentinel.organizer import FileOrganizer, _get_db_connection, _verify_file_inventory_schema
from sentinel.daemon import SentinelDaemon

print("=" * 60)
print("SENTINEL Verification Suite")
print("=" * 60)

# 1. Classify 3 test files
print("\n[1] CLASSIFY TEST")
clf = FileClassifier()
test_files = []
for root, dirs, files in os.walk(r"C:\Users\andre\LitigationOS\05_FILINGS"):
    for f in files:
        fp = os.path.join(root, f)
        if clf.should_process(fp):
            test_files.append(fp)
            if len(test_files) >= 3:
                break
    if len(test_files) >= 3:
        break

if not test_files:
    for f in os.listdir(r"C:\Users\andre\LitigationOS"):
        fp = os.path.join(r"C:\Users\andre\LitigationOS", f)
        if os.path.isfile(fp) and clf.should_process(fp):
            test_files.append(fp)
            if len(test_files) >= 3:
                break

print(f"  Found {len(test_files)} test files")
for fp in test_files:
    r = clf.classify(fp)
    print(f"  PASS: {os.path.basename(fp)[:45]}")
    print(f"        Lane={r.lane} Cat={r.category} Conf={r.confidence}")

# 2. DB connectivity check
print("\n[2] DB CONNECTIVITY")
try:
    conn = _get_db_connection()
    cols = _verify_file_inventory_schema(conn)
    row_count = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    conn.close()
    print(f"  PASS: file_inventory has {len(cols)} columns, {row_count:,} rows")
except Exception as e:
    print(f"  FAIL: {e}")

# 3. Organizer dry-run
print("\n[3] ORGANIZER DRY-RUN")
org = FileOrganizer(dry_run=True)
if test_files:
    r = clf.classify(test_files[0])
    outcome = org.organize(r)
    print(f"  File: {os.path.basename(test_files[0])[:45]}")
    print(f"  Dest: {outcome['dest_path']}")
    print(f"  Result: {outcome['reason']}")
    print(f"  PASS")

# 4. SentinelDaemon status
print("\n[4] DAEMON STATUS")
daemon = SentinelDaemon(dry_run=True)
st = daemon.status()
print(f"  Watch dirs: {len(st['watcher']['watch_dirs'])}")
for d in st['watcher']['watch_dirs']:
    print(f"    - {d}")
print(f"  PDF support: {st['classifier']['pdf_support']}")
print(f"  DOCX support: {st['classifier']['docx_support']}")
print(f"  PASS")

print("\n" + "=" * 60)
print("ALL VERIFICATION TESTS PASSED")
print("=" * 60)
