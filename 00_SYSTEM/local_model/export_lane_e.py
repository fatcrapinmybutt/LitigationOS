import sqlite3, os
from datetime import datetime

DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
OUT_DIR = r'C:\Users\andre\LitigationOS\00_SYSTEM\LITIGATIONOS_MASTER\LANE_E_JUDICIAL'

def export_violations():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    
    try:
        cur = db.execute('SELECT * FROM judicial_violations ORDER BY severity DESC, id ASC')
        findings = [dict(r) for r in cur.fetchall()]
        
        print(f"Found {len(findings)} judicial violations in database.")
        
        content = [
            "# MASTER JUDICIAL VIOLATIONS LEDGER",
            f"**Total Violations:** {len(findings)}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n---\n"
        ]
        
        for f in findings:
            entry = [
                f"## Violation {f['id']}",
                f"- **Judge:** {f['judge']}",
                f"- **Severity:** {f['severity']}/10",
                f"- **Canon Reference:** {f['canon_number']}",
                f"- **Authority Hook:** {f['authority_hook']}",
                f"- **Description:** {f['violation_description']}",
                ""
            ]
            content.extend(entry)
            
        out_path = os.path.join(OUT_DIR, 'MASTER_VIOLATIONS_LEDGER.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
            
        print(f"✅ Successfully exported to: {out_path}")
        
    except Exception as e:
        print(f"❌ Error during export: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    export_violations()
