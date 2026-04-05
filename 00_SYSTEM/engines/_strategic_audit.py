import sqlite3
from pathlib import Path
conn = sqlite3.connect(str(Path(__file__).resolve().parents[2] / "litigation_context.db"))
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
c = conn.cursor()

c.execute("SELECT package_name, COUNT(*), SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END), SUM(CASE WHEN status='WARN' THEN 1 ELSE 0 END), SUM(CASE WHEN status='FAIL' THEN 1 ELSE 0 END) FROM filing_compliance GROUP BY package_name ORDER BY package_name")
print('=== PACKAGE COMPLIANCE STATUS ===')
for pkg, total, p, w, f in c.fetchall():
    print(f'  {pkg}: {p}P/{w}W/{f}F of {total} checks')

c.execute("SELECT DISTINCT filing_target FROM rebuttal_matrix WHERE filing_target IS NOT NULL ORDER BY filing_target")
print('\n=== FILING TARGETS IN REBUTTAL MATRIX ===')
for r in c.fetchall():
    print(f'  {r[0]}')

c.execute("SELECT assertion_type, COUNT(*) FROM adversary_assertions GROUP BY assertion_type ORDER BY COUNT(*) DESC")
print('\n=== ADVERSARY ASSERTION BREAKDOWN ===')
for t, cnt in c.fetchall():
    print(f'  {t}: {cnt:,}')

c.execute("SELECT target_witness, impeachment_value, COUNT(*) FROM impeachment_index GROUP BY target_witness, impeachment_value ORDER BY target_witness")
print('\n=== IMPEACHMENT TARGETS ===')
for t, v, cnt in c.fetchall():
    print(f'  {t} [{v}]: {cnt}')

# Check citation issues by type
c.execute("SELECT citation_type, COUNT(*), SUM(CASE WHEN is_valid=0 THEN 1 ELSE 0 END) FROM citation_validation GROUP BY citation_type ORDER BY COUNT(*) DESC")
print('\n=== CITATION STATUS ===')
for t, cnt, bad in c.fetchall():
    print(f'  {t}: {cnt:,} total, {bad or 0:,} need verification')
