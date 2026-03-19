import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
db = sqlite3.connect('C:/Users/andre/litigation_context.db')

print("=" * 80)
print("BRUTAL SELF-AUDIT — What Have We Missed?")
print("=" * 80)

# 1. Have we actually READ the court orders?
print("\n### 1. COURT ORDERS — Have we actually read them? ###")
orders = db.execute("""
    SELECT text_content, page_number, document_id FROM pages 
    WHERE text_content LIKE '%COURT ORDERS%' OR text_content LIKE '%IT IS ORDERED%'
    OR text_content LIKE '%THE COURT FINDS%' OR text_content LIKE '%HEREBY ORDERED%'
    OR text_content LIKE '%ORDER OF THE COURT%'
""").fetchall()
print(f"  Pages containing court orders: {len(orders)}")

# What orders exist?
order_docs = db.execute("""
    SELECT DISTINCT d.file_name FROM pages p 
    JOIN documents d ON p.document_id = d.id
    WHERE p.text_content LIKE '%IT IS ORDERED%' OR p.text_content LIKE '%THE COURT FINDS%'
    OR p.text_content LIKE '%HEREBY ORDERED%'
""").fetchall()
print(f"  Documents containing orders: {len(order_docs)}")
for d in order_docs[:10]:
    print(f"    {d[0]}")

# 2. Do we know the CHILD's name, age, DOB?
print("\n### 2. THE CHILD — Do we have child details? ###")
child = db.execute("""
    SELECT quote_text FROM evidence_quotes 
    WHERE quote_text LIKE '%Lincoln%' OR quote_text LIKE '%child%born%'
    OR quote_text LIKE '%minor child%' OR quote_text LIKE '%son%'
    LIMIT 10
""").fetchall()
print(f"  Evidence quotes mentioning child: {len(child)}")

child_pages = db.execute("""
    SELECT COUNT(*) FROM pages 
    WHERE text_content LIKE '%Lincoln%'
""").fetchone()[0]
print(f"  PDF pages mentioning Lincoln: {child_pages}")

child_msgs = db.execute("""
    SELECT COUNT(*) FROM andrew_messages 
    WHERE message_text LIKE '%Lincoln%' OR message_text LIKE '%my son%'
""").fetchone()[0]
print(f"  Andrew messages about son: {child_msgs}")

# 3. GAL — Guardian ad Litem
print("\n### 3. GUARDIAN AD LITEM ###")
gal = db.execute("""
    SELECT COUNT(*) FROM pages WHERE text_content LIKE '%guardian ad litem%' OR text_content LIKE '%GAL%'
""").fetchone()[0]
gal_md = db.execute("""
    SELECT COUNT(*) FROM md_sections WHERE content LIKE '%guardian ad litem%' OR content LIKE '%GAL%'
""").fetchone()[0]
print(f"  PDF pages mentioning GAL: {gal}")
print(f"  MD sections mentioning GAL: {gal_md}")

# 4. FOC — Friend of Court
print("\n### 4. FRIEND OF COURT ###")
foc = db.execute("""
    SELECT COUNT(*) FROM pages WHERE text_content LIKE '%Friend of the Court%' OR text_content LIKE '%FOC%'
""").fetchone()[0]
foc_md = db.execute("""
    SELECT COUNT(*) FROM md_sections WHERE content LIKE '%Friend of Court%' OR content LIKE '%FOC%'
""").fetchone()[0]
foc_msgs = db.execute("""
    SELECT COUNT(*) FROM andrew_messages WHERE message_text LIKE '%friend of court%' OR message_text LIKE '%FOC%'
""").fetchone()[0]
print(f"  PDF pages: {foc}, MD sections: {foc_md}, Andrew msgs: {foc_msgs}")

# 5. Opposing counsel / attorneys
print("\n### 5. OPPOSING COUNSEL ###")
for name in ['Barnes', 'attorney', 'counsel', 'Jennifer Barnes', 'lawyer']:
    cnt = db.execute("SELECT COUNT(*) FROM pages WHERE text_content LIKE ?", (f'%{name}%',)).fetchone()[0]
    cnt2 = db.execute("SELECT COUNT(*) FROM andrew_messages WHERE message_text LIKE ?", (f'%{name}%',)).fetchone()[0]
    print(f"  '{name}': {cnt} pages, {cnt2} msgs")

# 6. Specific hearing dates
print("\n### 6. HEARING DATES ###")
hearings = db.execute("""
    SELECT text_content FROM pages 
    WHERE text_content LIKE '%hearing%' AND (text_content LIKE '%2024%' OR text_content LIKE '%2025%')
    AND LENGTH(text_content) > 100
    LIMIT 5
""").fetchall()
print(f"  Pages with hearing dates: ~{len(hearings)}+")

# What's in docket_events
docket = db.execute("SELECT event_date_iso, title, event_type FROM docket_events ORDER BY event_date_iso").fetchall()
print(f"  Docket events: {len(docket)}")
for d in docket:
    print(f"    {d[0]}: {(d[1] or '')[:60]} [{d[2]}]")

# 7. PPO specific terms
print("\n### 7. PPO TERMS — What does it actually prohibit? ###")
ppo_terms = db.execute("""
    SELECT text_content FROM pages 
    WHERE text_content LIKE '%PERSONAL PROTECTION ORDER%' AND text_content LIKE '%prohibited%'
    OR text_content LIKE '%restrained from%' OR text_content LIKE '%shall not%'
    LIMIT 3
""").fetchall()
print(f"  Pages with PPO terms: {len(ppo_terms)}")

# 8. Criminal history
print("\n### 8. CRIMINAL CHARGES / SENTENCES ###")
criminal = db.execute("""
    SELECT COUNT(*) FROM pages 
    WHERE text_content LIKE '%guilty%' OR text_content LIKE '%sentenced%' 
    OR text_content LIKE '%45 days%' OR text_content LIKE '%jail%'
""").fetchone()[0]
print(f"  Pages with criminal content: {criminal}")

# 9. Financial / child support
print("\n### 9. FINANCIAL / CHILD SUPPORT ###")
finance = db.execute("""
    SELECT COUNT(*) FROM pages 
    WHERE text_content LIKE '%child support%' OR text_content LIKE '%income%'
    OR text_content LIKE '%arrearage%' OR text_content LIKE '%support order%'
""").fetchone()[0]
print(f"  Pages with financial content: {finance}")

# 10. Best interest factor-by-factor analysis
print("\n### 10. BEST INTEREST FACTORS — Factor-by-factor? ###")
for factor in ['factor a', 'factor b', 'factor c', 'factor d', 'factor e', 'factor f', 
               'factor g', 'factor h', 'factor i', 'factor j', 'factor k', 'factor l']:
    cnt = db.execute("SELECT COUNT(*) FROM md_sections WHERE content LIKE ?", (f'%{factor}%',)).fetchone()[0]
    print(f"  {factor.upper()}: {cnt} sections")

# 11. Record on appeal
print("\n### 11. RECORD ON APPEAL ###")
record = db.execute("""
    SELECT COUNT(*) FROM filing_inventory 
    WHERE file_name LIKE '%appendix%' OR file_name LIKE '%record%' OR file_name LIKE '%exhibit%'
""").fetchone()[0]
print(f"  Filing docs with appendix/record/exhibit: {record}")

# 12. Service proofs
print("\n### 12. SERVICE / PROOF OF SERVICE ###")
service = db.execute("""
    SELECT COUNT(*) FROM filing_inventory WHERE file_name LIKE '%service%' OR file_name LIKE '%proof%'
""").fetchone()[0]
print(f"  Service proof documents: {service}")

db.close()
