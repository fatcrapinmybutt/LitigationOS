
import sqlite3, json
conn = sqlite3.connect(r"C:\\Users\\andre\\LitigationOS\\litigation_context.db")
conn.execute("PRAGMA busy_timeout=30000")
t = 'Homes of America'
results = {"target": t}

# Evidence quotes
try:
    rows = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE ? AND is_duplicate=0", (f'%{t}%',)).fetchone()
    results["evidence_quotes"] = rows[0]
    top = conn.execute("SELECT quote_text, source_file, category FROM evidence_quotes WHERE quote_text LIKE ? AND is_duplicate=0 ORDER BY relevance_score DESC LIMIT 5", (f'%{t}%',)).fetchall()
    results["top_quotes"] = [{"text": r[0][:200], "source": r[1], "cat": r[2]} for r in top]
except Exception as e:
    results["evidence_error"] = str(e)

# Impeachment
try:
    rows = conn.execute("SELECT COUNT(*) FROM impeachment_matrix WHERE target LIKE ?", (f'%{t}%',)).fetchone()
    results["impeachment_entries"] = rows[0]
    top = conn.execute("SELECT category, evidence_summary, impeachment_value FROM impeachment_matrix WHERE target LIKE ? ORDER BY impeachment_value DESC LIMIT 5", (f'%{t}%',)).fetchall()
    results["top_impeachment"] = [{"cat": r[0], "summary": r[1][:150], "value": r[2]} for r in top]
except:
    pass

# Contradictions
try:
    rows = conn.execute("SELECT COUNT(*) FROM contradiction_map WHERE contradiction_text LIKE ?", (f'%{t}%',)).fetchone()
    results["contradictions"] = rows[0]
except:
    pass

# Timeline
try:
    rows = conn.execute("SELECT COUNT(*) FROM timeline_events WHERE event_description LIKE ? OR actors LIKE ?", (f'%{t}%', f'%{t}%')).fetchone()
    results["timeline_events"] = rows[0]
except:
    pass

# Judicial violations
try:
    rows = conn.execute("SELECT COUNT(*) FROM judicial_violations WHERE description LIKE ? OR judge_name LIKE ?", (f'%{t}%', f'%{t}%')).fetchone()
    results["judicial_violations"] = rows[0]
except:
    pass

conn.close()
print(json.dumps(results, indent=2, default=str))
