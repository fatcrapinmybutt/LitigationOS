"""Quick DB status check for convergence monitoring."""
import sqlite3
conn = sqlite3.connect(r"C:\Users\andre\litigation_context.db")
c = conn.cursor()

# Check all custom tables
all_tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
custom = [t for t in all_tables if any(k in t for k in ['tort','drive_ev','agent_perf','convergence','rose','coherence','party_contact'])]
print(f"Custom tables found: {custom}")

for t in custom:
    try:
        count = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {count} rows")
    except Exception as e:
        print(f"  {t}: ERROR - {e}")

# Check filing packages
try:
    count = c.execute("SELECT COUNT(*) FROM filing_packages").fetchone()[0]
    print(f"\nFiling packages: {count}")
    latest = c.execute("SELECT id, title FROM filing_packages ORDER BY id DESC LIMIT 5").fetchall()
    for r in latest:
        print(f"  #{r[0]}: {r[1]}")
except Exception as e:
    print(f"Filing packages: {e}")

# Check system_files
try:
    count = c.execute("SELECT COUNT(*) FROM system_files").fetchone()[0]
    print(f"\nSystem files: {count}")
except:
    print("No system_files table")

conn.close()
print("\nDone.")
