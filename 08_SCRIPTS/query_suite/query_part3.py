import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

print("=" * 100)
print("EVIDENCE_QUOTES TABLE SCHEMA")
print("=" * 100)
cur.execute("PRAGMA table_info(evidence_quotes)")
schema = cur.fetchall()
for row in schema:
    print(f"  {row[1]:<30} | {row[2]:<15}")

print("\n" + "=" * 100)
print("QUERY 7: Ella Randall - (first 20)")
print("=" * 100)
cur.execute("""SELECT quote_text, doc_id, page_no FROM evidence_quotes 
              WHERE quote_text LIKE '%Randall%' OR quote_text LIKE '%Ella%' LIMIT 20""")
rows = cur.fetchall()
print(f"[Found {len(rows)} results]")
for i, row in enumerate(rows, 1):
    print(f"\n{i}. Doc ID: {row[1]} | Page: {row[2]}")
    print(f"   {row[0][:200]}...")

print("\n" + "=" * 100)
print("QUERY 8: Nitpicking")
print("=" * 100)
cur.execute("""SELECT quote_text, doc_id, page_no FROM evidence_quotes 
              WHERE quote_text LIKE '%nitpick%' LIMIT 20""")
rows = cur.fetchall()
print(f"[Found {len(rows)} results]")
for i, row in enumerate(rows, 1):
    print(f"\n{i}. Doc ID: {row[1]} | Page: {row[2]}")
    print(f"   {row[0][:250]}")

print("\n" + "=" * 100)
print("QUERY 9: Meth/Drug accusations")
print("=" * 100)
cur.execute("""SELECT quote_text, doc_id, page_no FROM evidence_quotes 
              WHERE (quote_text LIKE '%meth%' OR quote_text LIKE '%drug%' OR quote_text LIKE '%substance%') 
              AND quote_text NOT LIKE '%method%' LIMIT 30""")
rows = cur.fetchall()
print(f"[Found {len(rows)} results]")
for i, row in enumerate(rows, 1):
    print(f"\n{i}. Doc ID: {row[1]} | Page: {row[2]}")
    print(f"   {row[0][:250]}")

print("\n" + "=" * 100)
print("QUERY 10: False Police Report")
print("=" * 100)
cur.execute("""SELECT quote_text, doc_id FROM evidence_quotes 
              WHERE (quote_text LIKE '%false%' AND quote_text LIKE '%police%') 
              OR (quote_text LIKE '%false%' AND quote_text LIKE '%report%') LIMIT 20""")
rows = cur.fetchall()
print(f"[Found {len(rows)} results]")
for i, row in enumerate(rows, 1):
    print(f"\n{i}. Doc ID: {row[1]}")
    print(f"   {row[0][:250]}")

print("\n" + "=" * 100)
print("QUERY 11: Perjury/False Statements")
print("=" * 100)
cur.execute("""SELECT quote_text, doc_id FROM evidence_quotes 
              WHERE quote_text LIKE '%perjur%' OR quote_text LIKE '%false statement%' 
              OR quote_text LIKE '%lied%' OR quote_text LIKE '%lying%' LIMIT 30""")
rows = cur.fetchall()
print(f"[Found {len(rows)} results]")
for i, row in enumerate(rows, 1):
    print(f"\n{i}. Doc ID: {row[1]}")
    print(f"   {row[0][:250]}")

print("\n" + "=" * 100)
print("QUERY 12: Ex Parte Related")
print("=" * 100)
cur.execute("""SELECT COUNT(*) as total FROM evidence_quotes WHERE quote_text LIKE '%ex parte%'""")
total = cur.fetchone()[0]
print(f"[Total ex parte entries: {total}]")
cur.execute("""SELECT quote_text, doc_id FROM evidence_quotes 
              WHERE quote_text LIKE '%ex parte%' LIMIT 15""")
rows = cur.fetchall()
for i, row in enumerate(rows, 1):
    print(f"\n{i}. Doc ID: {row[1]}")
    print(f"   {row[0][:250]}")

conn.close()
