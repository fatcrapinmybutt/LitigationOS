"""Quick verification of email_pdf_analysis table."""
import sqlite3, os

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT = r"C:\Users\andre\LitigationOS\04_ANALYSIS\EMAIL_PDF_ANALYSIS_REPORT.md"

conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout = 60000")
conn.row_factory = sqlite3.Row

# Verify table
total = conn.execute("SELECT COUNT(*) FROM email_pdf_analysis").fetchone()[0]
fts = conn.execute("SELECT COUNT(*) FROM email_pdf_analysis_fts").fetchone()[0]
hv = conn.execute("SELECT COUNT(*) FROM email_pdf_analysis WHERE high_value=1").fetchone()[0]

print(f"email_pdf_analysis: {total} rows")
print(f"FTS5 index: {fts} rows")
print(f"High-value docs: {hv}")

# Lane + type summary
print("\nLane summary:")
for r in conn.execute("SELECT lane, COUNT(*) c, SUM(high_value) hv FROM email_pdf_analysis GROUP BY lane ORDER BY c DESC"):
    print(f"  Lane {r['lane']}: {r['c']} ({r['hv']} high-value)")

print("\nDoc type summary:")
for r in conn.execute("SELECT doc_type, COUNT(*) c FROM email_pdf_analysis GROUP BY doc_type ORDER BY c DESC"):
    print(f"  {r['doc_type']}: {r['c']}")

# FTS5 test
print("\nFTS5 search test - 'HealthWest evaluation':")
try:
    results = conn.execute("""
        SELECT filename, lane, doc_type FROM email_pdf_analysis_fts
        WHERE email_pdf_analysis_fts MATCH 'HealthWest evaluation'
        LIMIT 5
    """).fetchall()
    for r in results:
        print(f"  {r['filename']} [{r['lane']}] {r['doc_type']}")
except Exception as e:
    print(f"  FTS5 error: {e}")

# Unique senders
print("\nTop senders:")
for r in conn.execute("""
    SELECT sender, COUNT(*) c, SUM(high_value) hv
    FROM email_pdf_analysis WHERE sender != ''
    GROUP BY sender ORDER BY c DESC LIMIT 10
"""):
    print(f"  {r['sender'][:50]}: {r['c']} PDFs ({r['hv']} high-value)")

# Report file check
if os.path.isfile(REPORT):
    size = os.path.getsize(REPORT)
    print(f"\nReport saved: {REPORT} ({size:,} bytes)")
else:
    print(f"\nWARNING: Report NOT found at {REPORT}")

# Key evidence highlights
print("\n=== KEY EVIDENCE HIGHLIGHTS ===")
print("\nNSPD Police Reports (NS case numbers):")
for r in conn.execute("""
    SELECT filename, saved_path, substr(text_preview,1,200) as snip
    FROM email_pdf_analysis
    WHERE text_preview LIKE '%NS25%' AND doc_type = 'police_report'
    LIMIT 5
"""):
    print(f"  {r['filename']}")
    print(f"    {r['snip'][:150]}")

print("\nHealthWest evaluations:")
for r in conn.execute("""
    SELECT DISTINCT filename, saved_path
    FROM email_pdf_analysis
    WHERE text_preview LIKE '%HealthWest%' AND doc_type = 'expert_eval'
    LIMIT 5
"""):
    print(f"  {r['filename']}")

print("\nEx parte orders (Aug 8, 2025):")
for r in conn.execute("""
    SELECT filename, lane, saved_path, substr(text_preview,1,200) as snip
    FROM email_pdf_analysis
    WHERE text_preview LIKE '%8/8/2025%' AND doc_type = 'court_order'
    LIMIT 5
"""):
    print(f"  [{r['lane']}] {r['filename']}")
    print(f"    {r['snip'][:150]}")

print("\nJTC complaints:")
for r in conn.execute("""
    SELECT filename, saved_path
    FROM email_pdf_analysis
    WHERE text_preview LIKE '%JUDICIAL TENURE%'
    LIMIT 5
"""):
    print(f"  {r['filename']}: {r['saved_path']}")

conn.close()
print("\nVERIFICATION COMPLETE.")
