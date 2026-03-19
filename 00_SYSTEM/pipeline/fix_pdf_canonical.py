"""Fix PDF canonical election — one-time repair script."""
import sqlite3

db = sqlite3.connect('agents/master_index.db')
db.execute('PRAGMA journal_mode=WAL')
db.execute('PRAGMA busy_timeout=30000')

# Step 1: For PDF clusters (dupes), elect canonical = shallowest path preferring LitigationOS
clusters = db.execute("""
    SELECT sha256, COUNT(*) as cnt FROM files
    WHERE extension='.pdf' AND sha256 IS NOT NULL
    GROUP BY sha256 HAVING cnt > 1
""").fetchall()

elected = 0
for c in clusters:
    sha = c[0]
    members = db.execute('SELECT id, full_path FROM files WHERE sha256=?', (sha,)).fetchall()
    best = min(members, key=lambda m: (
        0 if 'LitigationOS' in m[1] else 1,
        m[1].count('\\') + m[1].count('/')
    ))
    db.execute('UPDATE files SET is_canonical=1 WHERE id=?', (best[0],))
    elected += 1

# Step 2: Mark unique PDFs (no dupes) as canonical
unique_pdf = db.execute("""
    UPDATE files SET is_canonical = 1
    WHERE extension = '.pdf'
      AND sha256 IS NOT NULL
      AND is_canonical = 0
      AND sha256 NOT IN (
          SELECT sha256 FROM files
          WHERE extension='.pdf' AND sha256 IS NOT NULL
          GROUP BY sha256 HAVING COUNT(*) > 1
      )
""").rowcount

# Step 3: Also fix .md, .txt, .docx unique files
for ext in ['.md', '.txt', '.docx']:
    cnt = db.execute("""
        UPDATE files SET is_canonical = 1
        WHERE extension = ?
          AND sha256 IS NOT NULL
          AND is_canonical = 0
          AND sha256 NOT IN (
              SELECT sha256 FROM files
              WHERE extension = ? AND sha256 IS NOT NULL
              GROUP BY sha256 HAVING COUNT(*) > 1
          )
    """, (ext, ext)).rowcount
    print(f"  {ext}: {cnt} unique marked canonical")

db.commit()

# Verify
pdf_can = db.execute("SELECT COUNT(*) FROM files WHERE extension='.pdf' AND is_canonical=1").fetchone()[0]
total_can = db.execute("SELECT COUNT(*) FROM files WHERE is_canonical=1").fetchone()[0]
print(f"\nPDF cluster canonicals elected: {elected}")
print(f"PDF unique canonicals: {unique_pdf}")
print(f"Total PDF canonical: {pdf_can}")
print(f"Total canonical (all types): {total_can}")
