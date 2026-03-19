#!/usr/bin/env python3
"""
Delta99-Level Litigation Filing Stack Generator
Andrew J. Pigors v. Shady Oaks Park MHP LLC et al.
Queries litigation_context.db and generates full filing stack.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT_DIR = r"C:\Users\andre\LitigationOS\02_TRIAL_14TH\SHADY_OAKS_EXPANDED_STACK"

os.makedirs(OUT_DIR, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

print("=" * 60)
print("PHASE 1: DATABASE EXTRACTION")
print("=" * 60)

conn = get_conn()

# 1. Get all 49 existing claims
print("[1] Extracting shadyoaks_claim_table...")
try:
    claims = conn.execute("SELECT * FROM shadyoaks_claim_table ORDER BY claim_id").fetchall()
    claim_cols = [d[0] for d in conn.execute("SELECT * FROM shadyoaks_claim_table LIMIT 1").description]
    print(f"    -> {len(claims)} claims. Columns: {claim_cols}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    claims = []; claim_cols = []

# 2. Housing violations
print("[2] Extracting housing_violations...")
try:
    violations = conn.execute("SELECT * FROM housing_violations ORDER BY rowid").fetchall()
    viol_cols = [d[0] for d in conn.execute("SELECT * FROM housing_violations LIMIT 1").description]
    print(f"    -> {len(violations)} violations. Columns: {viol_cols}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    violations = []; viol_cols = []

# 3. Extracted harms
print("[3] Extracting harms...")
try:
    harms = conn.execute("""
        SELECT * FROM extracted_harms 
        WHERE LOWER(adversary) LIKE '%shady%' 
           OR LOWER(adversary) LIKE '%homes of america%' 
           OR LOWER(adversary) LIKE '%alden%' 
           OR LOWER(category) LIKE '%housing%'
           OR LOWER(adversary) LIKE '%brandel%'
           OR LOWER(adversary) LIKE '%brown%'
           OR LOWER(adversary) LIKE '%partridge%'
        ORDER BY rowid LIMIT 5000
    """).fetchall()
    harm_cols = [d[0] for d in conn.execute("SELECT * FROM extracted_harms LIMIT 1").description]
    print(f"    -> {len(harms)} harms. Columns: {harm_cols}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    harms = []; harm_cols = []

# 4. Adversary summary
print("[4] Extracting adversary_harm_summary...")
try:
    adv_summary = conn.execute("""
        SELECT * FROM adversary_harm_summary 
        WHERE LOWER(adversary) LIKE '%shady%' OR LOWER(adversary) LIKE '%homes%' 
           OR LOWER(adversary) LIKE '%alden%' OR LOWER(adversary) LIKE '%housing%'
           OR LOWER(adversary) LIKE '%brandel%' OR LOWER(adversary) LIKE '%brown%'
           OR LOWER(adversary) LIKE '%partridge%'
    """).fetchall()
    adv_cols = [d[0] for d in conn.execute("SELECT * FROM adversary_harm_summary LIMIT 1").description]
    print(f"    -> {len(adv_summary)} rows. Columns: {adv_cols}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    adv_summary = []; adv_cols = []

# 5. Canonical facts
print("[5] Extracting canonical_fact_index...")
try:
    facts = conn.execute("""
        SELECT * FROM canonical_fact_index 
        WHERE LOWER(fact) LIKE '%shady%' OR LOWER(fact) LIKE '%evict%' 
           OR LOWER(fact) LIKE '%housing%' OR LOWER(fact) LIKE '%sewage%'
           OR LOWER(fact) LIKE '%egle%' OR LOWER(fact) LIKE '%ledger%'
           OR LOWER(fact) LIKE '%whitehall%' OR LOWER(fact) LIKE '%set-out%'
           OR LOWER(fact) LIKE '%homeless%' OR LOWER(fact) LIKE '%custody%'
           OR LOWER(fact) LIKE '%mobile home%' OR LOWER(fact) LIKE '%lot 17%'
           OR LOWER(fact) LIKE '%muskegon%' OR LOWER(fact) LIKE '%brandel%'
           OR LOWER(fact) LIKE '%brown%' OR LOWER(fact) LIKE '%abandon%'
           OR LOWER(fact) LIKE '%lock%' OR LOWER(fact) LIKE '%drill%'
           OR LOWER(fact) LIKE '%free sign%' OR LOWER(fact) LIKE '%sale%'
           OR LOWER(fact) LIKE '%destroy%' OR LOWER(fact) LIKE '%partridge%'
        ORDER BY rowid LIMIT 3000
    """).fetchall()
    fact_cols = [d[0] for d in conn.execute("SELECT * FROM canonical_fact_index LIMIT 1").description]
    print(f"    -> {len(facts)} facts. Columns: {fact_cols}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    facts = []; fact_cols = []

# 6. Evidence quotes
print("[6] Extracting evidence_quotes...")
try:
    quotes = conn.execute("""
        SELECT * FROM evidence_quotes 
        WHERE LOWER(quote) LIKE '%shady%' OR LOWER(quote) LIKE '%evict%' 
           OR LOWER(quote) LIKE '%sewage%' OR LOWER(quote) LIKE '%lot 17%'
           OR LOWER(quote) LIKE '%whitehall%' OR LOWER(quote) LIKE '%mobile home%'
           OR LOWER(quote) LIKE '%homeless%' OR LOWER(quote) LIKE '%set-out%'
           OR LOWER(quote) LIKE '%drill%' OR LOWER(quote) LIKE '%destroy%'
           OR LOWER(quote) LIKE '%abandon%' OR LOWER(quote) LIKE '%brandel%'
           OR LOWER(quote) LIKE '%brown%' OR LOWER(quote) LIKE '%ledger%'
           OR LOWER(quote) LIKE '%housing%'
        ORDER BY rowid LIMIT 5000
    """).fetchall()
    quote_cols = [d[0] for d in conn.execute("SELECT * FROM evidence_quotes LIMIT 1").description]
    print(f"    -> {len(quotes)} quotes. Columns: {quote_cols}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    quotes = []; quote_cols = []

# 7. Harm category counts
print("[7] Harm category counts...")
try:
    harm_counts = conn.execute("""
        SELECT category, COUNT(*) as cnt FROM extracted_harms 
        WHERE LOWER(adversary) LIKE '%shady%' OR LOWER(adversary) LIKE '%homes of america%' 
           OR LOWER(adversary) LIKE '%alden%'
        GROUP BY category ORDER BY cnt DESC
    """).fetchall()
    for r in harm_counts:
        print(f"    {dict(r)['category']}: {dict(r)['cnt']}")
except Exception as e:
    print(f"    -> ERROR: {e}")
    harm_counts = []

# 8. All tables
print("[8] All tables...")
try:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print(f"    -> {[dict(t)['name'] for t in tables]}")
except:
    pass

conn.close()

# Convert to dicts
def to_dicts(rows):
    return [dict(r) for r in rows]

claims_data = to_dicts(claims)
violations_data = to_dicts(violations)
harms_data = to_dicts(harms)
facts_data = to_dicts(facts)
quotes_data = to_dicts(quotes)
adv_data = to_dicts(adv_summary)

# Save extraction reference
with open(os.path.join(OUT_DIR, "_db_extraction.json"), "w", encoding="utf-8") as f:
    json.dump({
        "extraction_time": datetime.now().isoformat(),
        "claims_count": len(claims_data),
        "violations_count": len(violations_data),
        "harms_count": len(harms_data),
        "facts_count": len(facts_data),
        "quotes_count": len(quotes_data),
        "adversary_summaries": adv_data,
        "harm_categories": [(dict(r)['category'], dict(r)['cnt']) for r in harm_counts] if harm_counts else [],
        "sample_claims": claims_data[:5],
        "sample_violations": violations_data[:5],
        "sample_harms": harms_data[:5],
        "sample_facts": facts_data[:5],
    }, f, indent=2, default=str)

print(f"\nExtraction complete. Claims={len(claims_data)} Violations={len(violations_data)} Harms={len(harms_data)} Facts={len(facts_data)} Quotes={len(quotes_data)}")
print("PHASE 1 COMPLETE")
