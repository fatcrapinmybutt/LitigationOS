import sqlite3
c = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db').cursor()
c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
print(f"Tables: {c.fetchone()[0]}")
for n in ['adversary_assertions','citation_validation','filing_compliance','impeachment_index','alienation_scoring','exhibit_registry','prosecution_timeline','damages_itemization','constitutional_violations','rebuttal_matrix','psych_analysis_results']:
    try:
        c.execute(f"SELECT COUNT(*) FROM {n}")
        print(f"  {n}: {c.fetchone()[0]}")
    except:
        print(f"  {n}: NOT FOUND")
