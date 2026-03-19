import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
c = conn.cursor()

citations_to_check = [
    'MCL 777.49', 'MCR 7.306', 'MCL 400.106', 'MCL 600.5756', 'MCL 600.8371',
    'MCR 4.201', 'MCL 600.6431', 'MCL 600.2950a', 'MCR 3.708', 'MCL 750.411h',
    'MCL 750.411i', 'MCL 770.16', 'MCL 750.520e', 'MCL 257.728', 'MCL 764.15f',
    'MCL 600.3204', 'MCR 3.965', 'MCL 125.3606', 'MCL 722.27a', 'MCL 722.23',
    'MCL 552.603', 'MCR 7.305', 'MCR 3.206', 'MCR 3.207'
]

print('=== CITATION VERIFICATION ===')
for cite in citations_to_check:
    pattern = '%' + cite.replace(' ', '%') + '%'
    c.execute('SELECT COUNT(*), citation_type FROM omega_authority_inventory WHERE citation LIKE ? GROUP BY citation_type', (pattern,))
    results = c.fetchall()
    if results:
        for cnt, ctype in results:
            print(f'FOUND: {cite} -> type={ctype}, count={cnt}')
    else:
        print(f'NOT FOUND: {cite}')

print()
print('=== RELEVANT CUSTODY/FAMILY AUTHORITIES IN DB ===')
c.execute("""SELECT DISTINCT citation, citation_type, evidence_category FROM omega_authority_inventory
WHERE (citation LIKE '%722%' OR citation LIKE '%MCR 3.2%' OR citation LIKE '%MCR 7.3%'
OR citation LIKE '%MCR 7.2%' OR citation LIKE '%552%' OR citation LIKE '%MCR 3.7%')
AND citation_type IN ('MCL','MCR')
LIMIT 40""")
for r in c.fetchall():
    print(r)

print()
print('=== MCR 7.3xx AUTHORITIES (MSC/COA rules) ===')
c.execute("""SELECT DISTINCT citation, citation_type FROM omega_authority_inventory
WHERE citation LIKE '%MCR 7.3%' OR citation LIKE '%MCR 7.2%'
LIMIT 20""")
for r in c.fetchall():
    print(r)

print()
print('=== HABEAS CORPUS AUTHORITIES ===')
c.execute("""SELECT DISTINCT citation, citation_type FROM omega_authority_inventory
WHERE citation LIKE '%habeas%' OR citation LIKE '%3.303%' OR citation LIKE '%3.304%'
LIMIT 10""")
for r in c.fetchall():
    print(r)

print()
print('=== MANDAMUS AUTHORITIES ===')
c.execute("""SELECT DISTINCT citation, citation_type FROM omega_authority_inventory
WHERE citation LIKE '%mandamus%' OR citation LIKE '%3.305%'
LIMIT 10""")
for r in c.fetchall():
    print(r)

print()
print('=== SUPERINTENDING CONTROL AUTHORITIES ===')
c.execute("""SELECT DISTINCT citation, citation_type FROM omega_authority_inventory
WHERE citation LIKE '%superintending%' OR citation LIKE '%7.304%' OR citation LIKE '%7.305%'
LIMIT 10""")
for r in c.fetchall():
    print(r)

conn.close()
