#!/usr/bin/env python3
"""Query adversary filings, violations, and psych patterns from DB"""
import sqlite3

conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
c = conn.cursor()

# Get adversary filing documents
c.execute("""SELECT id, title, doc_type, court, file_path
FROM filing_documents 
WHERE title LIKE '%Watson%' OR title LIKE '%Emily%' OR title LIKE '%Barnes%' 
   OR title LIKE '%McNeill%' OR title LIKE '%exparte%' OR title LIKE '%ex parte%'
   OR file_path LIKE '%emily%' OR file_path LIKE '%watson%' OR file_path LIKE '%barnes%'
ORDER BY doc_type""")
rows = c.fetchall()
print(f'=== ADVERSARY FILINGS IN DB ({len(rows)}) ===')
for row in rows:
    title = (row[1] or '')[:60]
    fp = (row[4] or '')[-50:]
    print(f'  [{row[0][:8]}] {row[2]} | {title} | ...{fp}')

# Get judicial violations summary
c.execute('SELECT judge_name, COUNT(*), GROUP_CONCAT(DISTINCT canon_number) FROM judicial_violations GROUP BY judge_name')
print('\n=== JUDICIAL VIOLATIONS SUMMARY ===')
for row in c.fetchall():
    canons = (row[2] or '')[:100]
    print(f'  {row[0]}: {row[1]} violations - Canons: {canons}')

# Get psych analysis pattern distribution
c.execute('SELECT pattern_detected, COUNT(*), severity FROM psych_analysis_results GROUP BY pattern_detected ORDER BY COUNT(*) DESC')
print('\n=== PSYCH PATTERN DISTRIBUTION ===')
for row in c.fetchall():
    print(f'  {row[0]}: {row[1]} instances (severity: {row[2]})')

# Get evidence quotes from adversaries
c.execute("""SELECT COUNT(*), speaker FROM evidence_quotes 
WHERE speaker LIKE '%Emily%' OR speaker LIKE '%Watson%' OR speaker LIKE '%Barnes%' OR speaker LIKE '%McNeill%'
GROUP BY speaker ORDER BY COUNT(*) DESC LIMIT 10""")
print('\n=== ADVERSARY EVIDENCE QUOTES BY SPEAKER ===')
for row in c.fetchall():
    src = (row[1] or '')[:80]
    print(f'  {row[0]} quotes from: {src}')

# Count files on disk related to adversaries
c.execute("""SELECT COUNT(*), category FROM disk_inventory_omega 
WHERE file_name LIKE '%emily%' OR file_name LIKE '%watson%' OR file_name LIKE '%barnes%' 
   OR file_name LIKE '%mcneill%' OR file_name LIKE '%exparte%'
GROUP BY category ORDER BY COUNT(*) DESC LIMIT 15""")
print('\n=== ADVERSARY-RELATED FILES ON DISK BY CATEGORY ===')
for row in c.fetchall():
    print(f'  {row[0]} files in: {row[1]}')

# Summary stats
c.execute("SELECT metric_name, metric_value FROM omega_analysis_summary ORDER BY metric_name")
print('\n=== OMEGA SUMMARY METRICS ===')
for row in c.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
