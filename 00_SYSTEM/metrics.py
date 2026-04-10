import sqlite3
conn = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db')
cursor = conn.cursor()

# Authority-focused tables
try:
    cursor.execute("SELECT COUNT(*) FROM auth_authority_nodes")
    auth_nodes = cursor.fetchone()[0]
except: auth_nodes = 0

try:
    cursor.execute("SELECT COUNT(*) FROM auth_authority_edges")
    auth_edges = cursor.fetchone()[0]
except: auth_edges = 0

try:
    cursor.execute("SELECT COUNT(*) FROM citation_index")
    citations = cursor.fetchone()[0]
except: citations = 0

try:
    cursor.execute("SELECT COUNT(*) FROM court_forms")
    forms = cursor.fetchone()[0]
except: forms = 0

try:
    cursor.execute("SELECT COUNT(*) FROM mcr_authority_library")
    mcr_lib = cursor.fetchone()[0]
except: mcr_lib = 0

try:
    cursor.execute("SELECT COUNT(*) FROM mcl_authority_library")
    mcl_lib = cursor.fetchone()[0]
except: mcl_lib = 0

try:
    cursor.execute("SELECT COUNT(*) FROM mre_authority_library")
    mre_lib = cursor.fetchone()[0]
except: mre_lib = 0

print('KEY AUTHORITY/LEGAL METRICS:')
print('=' * 60)
print('  auth_authority_nodes: {} entries'.format(auth_nodes))
print('  auth_authority_edges: {} relationships'.format(auth_edges))
print('  citation_index: {} indexed citations'.format(citations))
print('  court_forms: {} form definitions'.format(forms))
print('  mcr_authority_library: {} MCR entries'.format(mcr_lib))
print('  mcl_authority_library: {} MCL entries'.format(mcl_lib))
print('  mre_authority_library: {} MRE entries'.format(mre_lib))

conn.close()
