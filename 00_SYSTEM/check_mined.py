import sqlite3

c = sqlite3.connect('../litigation_context.db')
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mined_documents'").fetchall()]
print('mined_documents exists:', bool(tables))
c.close()
