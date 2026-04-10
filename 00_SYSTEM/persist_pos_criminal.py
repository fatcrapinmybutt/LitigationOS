"""Persist POS harvest + fix critical errors in POS templates + criminal defense retry"""
import sqlite3, os, glob
from datetime import datetime

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

# 1. Persist POS intelligence
pos_findings = [
    ("PROOF_OF_SERVICE/all_8_templates", "service_intelligence",
     "8 POS templates for: AGC Grievance, COA Brief 366810, Contempt Motion, Disqualification Motion, Emergency Parenting Time, Federal §1983, JTC Complaint, MSC Petition. ALL have blank service dates. 7/8 have unchecked service methods. Only JTC has certified mail checked. CRITICAL ERRORS: Barnes listed as attorney (she WITHDREW Mar 2026), judge listed as 'Amy McNeill' (correct: Jenny L. McNeill), Ronald Berry address listed as TBD (he lives at 2160 Garland Dr with Emily). Service must go DIRECTLY to Emily at 2160 Garland Dr since Barnes withdrew.",
     "HIGH", "ALL", "Emily Watson,Jennifer Barnes,McNeill,Ronald Berry",
     "POS templates in COURT_FILING_PACKETS", "MCR 2.107,FRCP 4,MCR 7.211,MCR 2.003", "F01,F03,F04,F05,F06,F09,F10"),
    
    ("PROOF_OF_SERVICE/POS_FEDERAL_1983.md", "federal_service",
     "Federal §1983 POS lists 4 defendants: Emily Watson (address needs confirmation), McNeill (via AG or certified), Ronald Berry (address TBD - actually 2160 Garland Dr), Muskegon County (via County Clerk at 990 Terrace). FRCP 4(m) requires service within 90 days of filing. FRCP 4(d) waiver of service recommended. McNeill requires FRCP 4(j) state officer service through Michigan AG P.O. Box 30212 Lansing MI 48909.",
     "HIGH", "C", "Emily Watson,McNeill,Ronald Berry,Muskegon County",
     "POS_FEDERAL_1983.md", "FRCP 4,FRCP 4(d),FRCP 4(j),FRCP 4(m)", "F04"),
]

inserted = 0
for f in pos_findings:
    source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use = f
    existing = conn.execute("SELECT COUNT(*) FROM harvest_intelligence WHERE source=? AND category=?", (source, category)).fetchone()[0]
    if existing == 0:
        conn.execute("INSERT INTO harvest_intelligence (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use) VALUES (?,?,?,?,?,?,?,?,?)", f)
        inserted += 1

conn.commit()
total = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
print(f"POS findings inserted: {inserted}, Total harvest_intelligence: {total}")

# 2. Read and catalog CRIMINAL_DEFENSE_PREP files directly
crim_dir = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\CRIMINAL_DEFENSE_PREP"
if os.path.exists(crim_dir):
    files = []
    for f in os.listdir(crim_dir):
        fp = os.path.join(crim_dir, f)
        if os.path.isfile(fp):
            size = os.path.getsize(fp)
            files.append((f, size))
    print(f"\nCRIMINAL_DEFENSE_PREP: {len(files)} files")
    for name, size in sorted(files):
        print(f"  {name} ({size:,} bytes)")
    
    # Read each file and extract key info
    findings = []
    for name, size in files:
        fp = os.path.join(crim_dir, name)
        try:
            if name.endswith('.md') or name.endswith('.txt'):
                with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                    content = fh.read()
                # Extract first 500 chars as summary
                summary = content[:500].replace('\n', ' ').strip()
                findings.append((name, size, summary))
            elif name.endswith('.pdf'):
                findings.append((name, size, "[PDF - binary]"))
        except Exception as e:
            findings.append((name, size, f"[ERROR: {e}]"))
    
    # Persist criminal defense intelligence
    for name, size, summary in findings:
        source_key = f"CRIMINAL_DEFENSE_PREP/{name}"
        existing = conn.execute("SELECT COUNT(*) FROM harvest_intelligence WHERE source=?", (source_key,)).fetchone()[0]
        if existing == 0:
            conn.execute("""INSERT INTO harvest_intelligence 
                (source, category, finding, severity, lane, actors, evidence_refs, legal_authority, filing_use)
                VALUES (?, 'criminal_defense', ?, 'MEDIUM', 'CRIMINAL', 'Andrew Pigors', ?, 'MCL 750', 'CRIMINAL')""",
                (source_key, summary[:1000], name))
    conn.commit()
    crim_total = conn.execute("SELECT COUNT(*) FROM harvest_intelligence WHERE lane='CRIMINAL'").fetchone()[0]
    print(f"Criminal defense findings persisted: {crim_total}")
else:
    print("CRIMINAL_DEFENSE_PREP directory not found")

# 3. Final count
total = conn.execute("SELECT COUNT(*) FROM harvest_intelligence").fetchone()[0]
print(f"\nFinal harvest_intelligence total: {total}")
conn.close()
print("DONE")
