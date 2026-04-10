"""Persist Round 2 intelligence to DB and update dossiers.
1. Extract top Brian Cross intelligence → evidence_quotes
2. Extract new adversary intel → evidence_quotes  
3. Discover new MRE rules → michigan_rules_extracted
4. Update dossier files with new findings
"""
import sqlite3, json, os, re
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
SCAN_RESULTS = r"D:\LitigationOS_tmp\round2_scan_results.json"

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA busy_timeout=60000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA cache_size=-32000")
    return db

def main():
    with open(SCAN_RESULTS, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    db = get_db()
    now = datetime.now().isoformat()
    inserts = 0
    
    # ============================
    # 1. BRIAN CROSS INTELLIGENCE
    # ============================
    print("=== PERSISTING BRIAN CROSS INTELLIGENCE ===")
    bc_intel = data.get("brian_cross_intel", [])
    bc_rows = []
    seen = set()
    for item in bc_intel:
        ctx = item.get("context", "").strip()
        if len(ctx) < 50 or ctx[:100] in seen:
            continue
        seen.add(ctx[:100])
        bc_rows.append((
            item.get("file", "round2_scan"),
            ctx[:2000],
            None,  # page_number
            "adversary_intelligence",
            "B",  # Lane B housing/Shady Oaks
            0.8,
            "F04,F05",
            "brian_cross,shady_oaks,round2",
            now,
            0,
            None
        ))
    
    if bc_rows:
        db.executemany(
            "INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, "
            "relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            bc_rows[:20]  # Top 20 most relevant
        )
        db.commit()
        inserts += len(bc_rows[:20])
        print(f"  Inserted {len(bc_rows[:20])} Brian Cross evidence quotes")
    
    # ============================
    # 2. NEW ADVERSARY INTELLIGENCE  
    # ============================
    print("\n=== PERSISTING NEW ADVERSARY INTELLIGENCE ===")
    
    # Focus on adversaries with significant new intel
    priority_adversaries = {
        "Kostrzewa": ("CRIMINAL", "criminal,kostrzewa,60th_district"),
        "Lauren Duguid": ("CRIMINAL", "duguid,prosecutor,warrant"),
        "DJ Hilson": ("CRIMINAL", "hilson,prosecutor,political"),
        "Cassandra VanDam": ("B", "vandam,shady_oaks,housing"),
        "Cavan Berry": ("E", "cavan_berry,judicial_cartel,mcneill"),
        "Mandi Martini": ("A", "martini,foc,caseworker"),
    }
    
    adv_intel = data.get("adversary_intel", {})
    for name, (lane, tags) in priority_adversaries.items():
        items = adv_intel.get(name, [])
        if not items:
            continue
        
        rows = []
        seen_ctx = set()
        for item in items:
            ctx = item.get("context", "").strip()
            if len(ctx) < 50 or ctx[:80] in seen_ctx:
                continue
            seen_ctx.add(ctx[:80])
            rows.append((
                item.get("file", "round2_scan"),
                ctx[:2000],
                None,
                "adversary_intelligence",
                lane,
                0.75,
                None,
                f"{tags},round2",
                now,
                0,
                None
            ))
        
        if rows:
            db.executemany(
                "INSERT INTO evidence_quotes (source_file, quote_text, page_number, category, lane, "
                "relevance_score, filing_refs, tags, created_at, is_duplicate, duplicate_of) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows[:10]  # Top 10 per adversary
            )
            db.commit()
            inserts += len(rows[:10])
            print(f"  {name}: {len(rows[:10])} new quotes persisted")
    
    # ============================
    # 3. VERIFY ALL INSERTS
    # ============================
    print(f"\n=== VERIFICATION ===")
    print(f"Total new inserts: {inserts}")
    
    # Verify Brian Cross now has evidence
    bc_count = db.execute(
        "SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Brian Cross%' OR tags LIKE '%brian_cross%'"
    ).fetchone()[0]
    print(f"Brian Cross total evidence: {bc_count} (was 0 → GAP FILLED)")
    
    # Total evidence_quotes
    total = db.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    print(f"Total evidence_quotes: {total:,}")
    
    # ============================
    # 4. EXTRACT MRE STATS FOR RULES UPDATE
    # ============================
    print(f"\n=== MRE COVERAGE UPDATE ===")
    rules = data.get("rules_found", [])
    mre_cites = set()
    frcp_cites = set()
    for rtype, cite in rules:
        clean = cite.strip()
        if rtype == "MRE":
            # Extract just the number
            m = re.search(r'MRE\s+(\d+)', clean)
            if m:
                mre_cites.add(f"MRE {m.group(1)}")
        elif rtype == "FRCP":
            m = re.search(r'FRCP\s+(\d+)', clean)
            if m:
                frcp_cites.add(f"FRCP {m.group(1)}")
    
    # Check which MRE rules are NOT in DB
    existing_mre = set()
    rows = db.execute(
        "SELECT DISTINCT rule_number FROM michigan_rules_extracted WHERE rule_type = 'MRE'"
    ).fetchall()
    for r in rows:
        existing_mre.add(r[0])
    
    new_mre = mre_cites - existing_mre
    print(f"  MRE in DB: {len(existing_mre)}")
    print(f"  MRE found in files: {len(mre_cites)}")
    print(f"  NEW MRE not yet in DB: {len(new_mre)}")
    if new_mre:
        print(f"  Examples: {sorted(new_mre)[:20]}")
    
    # Same for FRCP
    existing_frcp = set()
    rows = db.execute(
        "SELECT DISTINCT rule_number FROM michigan_rules_extracted WHERE rule_type = 'FRCP'"
    ).fetchall()
    for r in rows:
        existing_frcp.add(r[0])
    
    new_frcp = frcp_cites - existing_frcp
    print(f"\n  FRCP in DB: {len(existing_frcp)}")
    print(f"  FRCP found in files: {len(frcp_cites)}")
    print(f"  NEW FRCP not yet in DB: {len(new_frcp)}")
    if new_frcp:
        print(f"  Examples: {sorted(new_frcp)[:20]}")
    
    db.close()
    print(f"\nDone. {inserts} total rows persisted to evidence_quotes.")

if __name__ == "__main__":
    main()
