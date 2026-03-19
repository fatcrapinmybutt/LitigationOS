"""Register all converged filings in DB filing_packages table."""
import sys, os, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shell_resilience_engine import safe_db

VEHICLES = r"C:\Users\andre\LitigationOS\06_VEHICLES"
DESKTOP = r"C:\Users\andre\Desktop\COURT_READY_PACKAGES"

filings = []
for root, dirs, files in os.walk(VEHICLES):
    for f in files:
        if not f.endswith(".md"):
            continue
        fp = os.path.join(root, f)
        lane = os.path.basename(root)
        size = os.path.getsize(fp)
        filings.append((lane, f, fp, size))

with safe_db() as conn:
    # Get existing
    existing = set()
    try:
        rows = conn.execute("SELECT file_path FROM filing_packages").fetchall()
        existing = set(r[0] for r in rows)
    except:
        pass

    inserted = 0
    for lane, fname, fp, size in filings:
        if fp in existing:
            continue
        try:
            conn.execute(
                "INSERT INTO filing_packages (lane, title, file_path, file_size, status, created_at) VALUES (?, ?, ?, ?, 'converged', datetime('now'))",
                (lane, fname.replace(".md", ""), fp, size)
            )
            inserted += 1
        except Exception as e:
            # Table schema may differ
            try:
                conn.execute(
                    "INSERT INTO filing_packages (title, file_path) VALUES (?, ?)",
                    (fname.replace(".md", ""), fp)
                )
                inserted += 1
            except:
                pass

    print(f"Registered {inserted} new filings in DB ({len(filings)} total files)")

# Summary
print(f"\nFiling inventory:")
for lane, fname, fp, size in sorted(filings, key=lambda x: -x[3]):
    print(f"  {lane:40s} {fname:50s} {size:>8,} bytes")
