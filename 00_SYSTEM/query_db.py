import sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
conn.execute('PRAGMA busy_timeout=60000')

# 1. Show previews of dockets_notices_proofs pages
print('=== DOCKETS/NOTICES/PROOFS ===')
rows = conn.execute("""SELECT file_path, substr(page_text,1,300) FROM downloads_pages 
WHERE set_name='dockets_notices_proofs' ORDER BY file_path""").fetchall()
import os
for fp, prev in rows:
    print(f'\n{os.path.basename(fp)}:')
    print(prev)

# 2. Show Emily's filings
print('\n\n=== EMILY''S FILINGS ===')
rows = conn.execute("""SELECT file_path, substr(page_text,1,300) FROM downloads_pages 
WHERE set_name='emilys_filings' ORDER BY file_path""").fetchall()
for fp, prev in rows:
    print(f'\n{os.path.basename(fp)}:')
    print(prev)

# 3. Show JTC scanned pages
print('\n\n=== JTC SCANNED ===')
rows = conn.execute("""SELECT file_path, substr(page_text,1,300) FROM downloads_pages 
WHERE set_name='jtc_scanned' ORDER BY file_path""").fetchall()
for fp, prev in rows:
    print(f'\n{os.path.basename(fp)}:')
    print(prev)

conn.close()
