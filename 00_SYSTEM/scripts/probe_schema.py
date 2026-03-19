import sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
conn.execute('PRAGMA busy_timeout=60000')
tables = ['evidence_quotes','authority_chains','deadlines','documents','filings','claims','docket_events','court_rules',
          'master_citations','drive_manifest','omega_filesystem_map','file_inventory','file_inventory_external',
          'pages','auth_authority_edges','evidence_dedup_map','master_file_index','evidence_file_index',
          'master_citations_parsed','master_violations_parsed','chatgpt_conversations','chatgpt_litigation_intel',
          'tfidf_index','d_drive_catalog','scan_inventory','master_timeline_parsed','file_atoms',
          'case_intelligence_hub','canonical_facts','extracted_harms','prosecution_timeline']
for t in tables:
    try:
        cols = conn.execute(f'PRAGMA table_info([{t}])').fetchall()
        if cols:
            cnames = [c[1] for c in cols]
            print(f'{t}: {cnames}')
        else:
            print(f'{t}: TABLE NOT FOUND or VIRTUAL')
    except Exception as e:
        print(f'{t}: ERROR {e}')
print()
print('=== EXISTING INDEXES ===')
idxs = conn.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY tbl_name, name").fetchall()
for name, tbl, sql in idxs:
    print(f'  {tbl}.{name}: {sql}')
conn.close()
