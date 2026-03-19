import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
db = sqlite3.connect('C:/Users/andre/litigation_context.db')

print("=" * 80)
print("SYSTEM INTELLIGENCE GAPS — What's shallow vs deep?")
print("=" * 80)

# 1. How many forensic_findings are just regex patterns vs real analysis?
print("\n### FORENSIC FINDINGS DEPTH ###")
# Check source distribution
sources = db.execute("""
    SELECT 
        CASE 
            WHEN source LIKE 'chatgpt_%' THEN 'chatgpt_pattern'
            WHEN source LIKE 'page_%' THEN 'pdf_pattern'
            WHEN source LIKE 'md_%' THEN 'md_pattern'
            WHEN source LIKE 'impeach_%' THEN 'impeachment'
            WHEN source LIKE 'violation_%' THEN 'violation'
            ELSE source
        END as src_type,
        COUNT(*)
    FROM forensic_findings 
    GROUP BY src_type
    ORDER BY COUNT(*) DESC
""").fetchall()
for s, c in sources:
    print(f"  {s:30s} {c:>6,}")

# How many have actual evidence_text?
has_text = db.execute("SELECT COUNT(*) FROM forensic_findings WHERE evidence_text IS NOT NULL AND LENGTH(evidence_text) > 50").fetchone()[0]
no_text = db.execute("SELECT COUNT(*) FROM forensic_findings WHERE evidence_text IS NULL OR LENGTH(evidence_text) < 50").fetchone()[0]
print(f"\n  With substantive evidence text: {has_text:,}")
print(f"  Without (shallow/pattern only): {no_text:,}")

# 2. Contradiction quality
print("\n### CONTRADICTION MAP QUALITY ###")
types = db.execute("SELECT contradiction_type, COUNT(*) FROM contradiction_map GROUP BY contradiction_type ORDER BY COUNT(*) DESC").fetchall()
for t, c in types:
    print(f"  {(t or ''):30s} {c:>6,}")

# How many are date conflicts (low value) vs substantive?
date_conflicts = db.execute("SELECT COUNT(*) FROM contradiction_map WHERE contradiction_type = 'TIMELINE_DATE_CONFLICT'").fetchone()[0]
substantive = db.execute("SELECT COUNT(*) FROM contradiction_map WHERE contradiction_type != 'TIMELINE_DATE_CONFLICT'").fetchone()[0]
print(f"\n  Date conflicts (low signal): {date_conflicts:,} ({date_conflicts*100//10558}%)")
print(f"  Substantive contradictions: {substantive:,} ({substantive*100//10558}%)")

# 3. Impeachment depth  
print("\n### IMPEACHMENT ITEM QUALITY ###")
# How many have actual contradicting_text vs empty?
has_contra = db.execute("SELECT COUNT(*) FROM impeachment_items WHERE contradicting_text IS NOT NULL AND LENGTH(contradicting_text) > 50").fetchone()[0]
has_hook = db.execute("SELECT COUNT(*) FROM impeachment_items WHERE legal_hook IS NOT NULL AND LENGTH(legal_hook) > 10").fetchone()[0]
total_imp = db.execute("SELECT COUNT(*) FROM impeachment_items").fetchone()[0]
print(f"  Total: {total_imp:,}")
print(f"  With contradicting text: {has_contra:,}")
print(f"  With legal hook: {has_hook:,}")
print(f"  Empty/shallow: {total_imp - has_contra:,}")

# 4. What tables are EMPTY that shouldn't be?
print("\n### EMPTY/NEAR-EMPTY TABLES ###")
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%fts%' ORDER BY name").fetchall()
for (t,) in tables:
    try:
        cnt = db.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        if cnt == 0:
            print(f"  EMPTY: {t}")
        elif cnt < 5:
            print(f"  SPARSE ({cnt}): {t}")
    except:
        pass

# 5. What PDF documents have we NOT read?
print("\n### UNREAD DOCUMENTS ###")
total_docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
docs_with_pages = db.execute("SELECT COUNT(DISTINCT document_id) FROM pages").fetchone()[0]
print(f"  Total documents: {total_docs}")
print(f"  Documents with extracted pages: {docs_with_pages}")
print(f"  Documents NOT read: {total_docs - docs_with_pages}")

# Unread docs
unread = db.execute("""
    SELECT d.file_name, d.file_path FROM documents d 
    WHERE d.id NOT IN (SELECT DISTINCT document_id FROM pages WHERE document_id IS NOT NULL)
    LIMIT 20
""").fetchall()
for name, path in unread:
    print(f"    UNREAD: {name}")

db.close()
