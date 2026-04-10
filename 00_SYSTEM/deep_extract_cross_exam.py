"""Deep data extraction for Watson and McNeill cross-exam material."""
import sqlite3, json

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
conn.row_factory = sqlite3.Row

# ===== WATSON DATA =====
print("=" * 80)
print("WATSON — Impeachment Matrix (top 50 by impeachment_value)")
print("=" * 80)

watson_impeachment = conn.execute("""
    SELECT id, category, evidence_summary, source_file, quote_text, 
           impeachment_value, cross_exam_question, filing_relevance, event_date
    FROM impeachment_matrix
    WHERE evidence_summary LIKE '%Watson%' 
       OR evidence_summary LIKE '%Emily%'
       OR quote_text LIKE '%Watson%'
       OR quote_text LIKE '%Emily%'
       OR evidence_summary LIKE '%mother%'
       OR category IN ('FALSE_ALLEGATIONS','PPO_ABUSE','PARENTING_TIME','CUSTODY_INTERFERENCE')
    ORDER BY impeachment_value DESC
    LIMIT 50
""").fetchall()
print(f"Watson impeachment rows: {len(watson_impeachment)}")
for r in watson_impeachment[:5]:
    print(f"  ID={r['id']} cat={r['category']} val={r['impeachment_value']} summary={r['evidence_summary'][:120]}...")

# Watson contradictions
print("\n" + "=" * 80)
print("WATSON — Contradiction Map")
print("=" * 80)
watson_contradictions = conn.execute("""
    SELECT id, claim_id, source_a, source_b, contradiction_text, severity, lane
    FROM contradiction_map
    WHERE contradiction_text LIKE '%Watson%' 
       OR contradiction_text LIKE '%Emily%'
       OR contradiction_text LIKE '%mother%'
       OR contradiction_text LIKE '%defendant%'
    ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
    LIMIT 50
""").fetchall()
print(f"Watson contradiction rows: {len(watson_contradictions)}")
for r in watson_contradictions[:5]:
    print(f"  ID={r['id']} sev={r['severity']} text={r['contradiction_text'][:150]}...")

# Watson evidence quotes - key categories
print("\n" + "=" * 80)
print("WATSON — Evidence Quotes (key categories)")
print("=" * 80)
for cat in ['ppo', 'custody', 'police', 'communication', 'witness']:
    rows = conn.execute("""
        SELECT id, source_file, quote_text, page_number, category, lane, relevance_score, filing_refs
        FROM evidence_quotes
        WHERE category = ? AND is_duplicate = 0
          AND (quote_text LIKE '%Watson%' OR quote_text LIKE '%Emily%' OR quote_text LIKE '%mother%')
        ORDER BY relevance_score DESC
        LIMIT 15
    """, (cat,)).fetchall()
    print(f"\n  Category '{cat}': {len(rows)} Watson-related rows")
    for r in rows[:3]:
        print(f"    ID={r['id']} score={r['relevance_score']} page={r['page_number']} text={r['quote_text'][:120]}...")

# Watson — false allegations evidence
print("\n--- Watson False Allegations Evidence ---")
false_allege = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, relevance_score
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%suicid%' OR quote_text LIKE '%arsenic%' OR quote_text LIKE '%assault%'
           OR quote_text LIKE '%drug%' OR quote_text LIKE '%meth%' OR quote_text LIKE '%threat%'
           OR quote_text LIKE '%false%allega%' OR quote_text LIKE '%recant%')
      AND (quote_text LIKE '%Watson%' OR quote_text LIKE '%Emily%' OR quote_text LIKE '%mother%'
           OR category IN ('ppo','police','custody','witness'))
    ORDER BY relevance_score DESC
    LIMIT 30
""").fetchall()
print(f"False allegations evidence: {len(false_allege)} rows")
for r in false_allege[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# Watson — PPO timeline 
print("\n--- Watson PPO Timeline Evidence ---")
ppo_timeline = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, relevance_score
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%PPO%' OR quote_text LIKE '%protection order%' OR quote_text LIKE '%5907%')
      AND (quote_text LIKE '%recant%' OR quote_text LIKE '%nothing was physical%' 
           OR quote_text LIKE '%October 2023%' OR quote_text LIKE '%Oct 13%' OR quote_text LIKE '%Oct 15%')
    ORDER BY relevance_score DESC
    LIMIT 20
""").fetchall()
print(f"PPO timeline evidence: {len(ppo_timeline)} rows")
for r in ppo_timeline[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# ===== MCNEILL DATA =====
print("\n" + "=" * 80)
print("MCNEILL — Impeachment Matrix")
print("=" * 80)
mcneill_impeachment = conn.execute("""
    SELECT id, category, evidence_summary, source_file, quote_text,
           impeachment_value, cross_exam_question, filing_relevance, event_date
    FROM impeachment_matrix
    WHERE evidence_summary LIKE '%McNeill%'
       OR evidence_summary LIKE '%judge%'
       OR quote_text LIKE '%McNeill%'
       OR quote_text LIKE '%judge%'
       OR category IN ('EX_PARTE','CONTEMPT','DUE_PROCESS','JUDICIAL_MISCONDUCT','EVIDENCE_EXCLUSION')
    ORDER BY impeachment_value DESC
    LIMIT 50
""").fetchall()
print(f"McNeill impeachment rows: {len(mcneill_impeachment)}")
for r in mcneill_impeachment[:5]:
    print(f"  ID={r['id']} cat={r['category']} val={r['impeachment_value']} summary={r['evidence_summary'][:120]}...")

# McNeill contradictions
print("\n" + "=" * 80)
print("MCNEILL — Contradiction Map")
print("=" * 80)
mcneill_contradictions = conn.execute("""
    SELECT id, claim_id, source_a, source_b, contradiction_text, severity, lane
    FROM contradiction_map
    WHERE contradiction_text LIKE '%McNeill%'
       OR contradiction_text LIKE '%judge%'
       OR contradiction_text LIKE '%court%'
       OR contradiction_text LIKE '%ex parte%'
    ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
    LIMIT 50
""").fetchall()
print(f"McNeill contradiction rows: {len(mcneill_contradictions)}")
for r in mcneill_contradictions[:5]:
    print(f"  ID={r['id']} sev={r['severity']} text={r['contradiction_text'][:150]}...")

# McNeill judicial violations
print("\n" + "=" * 80)
print("MCNEILL — Judicial Violations (top 50 by severity)")
print("=" * 80)
jv = conn.execute("""
    SELECT id, violation_type, description, date_occurred, mcr_rule, canon, 
           source_file, source_quote, severity, lane
    FROM judicial_violations
    WHERE severity >= 7
    ORDER BY severity DESC
    LIMIT 50
""").fetchall()
print(f"High-severity judicial violations: {len(jv)}")
for r in jv[:5]:
    print(f"  ID={r['id']} type={r['violation_type']} sev={r['severity']} desc={r['description'][:120]}...")

# McNeill - ex parte evidence
print("\n--- McNeill Ex Parte Evidence ---")
ex_parte = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, relevance_score
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%ex parte%' OR quote_text LIKE '%without notice%' 
           OR quote_text LIKE '%without hearing%' OR quote_text LIKE '%Five Orders%'
           OR quote_text LIKE '%August 8%' OR quote_text LIKE '%Aug 8%')
      AND category IN ('judicial','judicial_violation','due_process','procedural')
    ORDER BY relevance_score DESC
    LIMIT 30
""").fetchall()
print(f"Ex parte evidence: {len(ex_parte)} rows")
for r in ex_parte[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# McNeill - contempt evidence
print("\n--- McNeill Contempt Abuse Evidence ---")
contempt = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, relevance_score
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%contempt%' OR quote_text LIKE '%jail%' OR quote_text LIKE '%incarcerat%'
           OR quote_text LIKE '%shut%mouth%' OR quote_text LIKE '%do not file%'
           OR quote_text LIKE '%birthday%' OR quote_text LIKE '%AppClose%')
      AND category IN ('judicial','judicial_violation','due_process','procedural','custody','communication')
    ORDER BY relevance_score DESC
    LIMIT 30
""").fetchall()
print(f"Contempt evidence: {len(contempt)} rows")
for r in contempt[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# McNeill - evidence exclusion
print("\n--- McNeill Evidence Exclusion ---")
exclusion = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category, relevance_score
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%HealthWest%' OR quote_text LIKE '%LOCUS%' 
           OR quote_text LIKE '%exclud%' OR quote_text LIKE '%evaluation%'
           OR quote_text LIKE '%evidence%exclus%')
      AND category IN ('judicial','judicial_violation','due_process','procedural','custody')
    ORDER BY relevance_score DESC
    LIMIT 20
""").fetchall()
print(f"Evidence exclusion: {len(exclusion)} rows")
for r in exclusion[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# Get unique categories used in impeachment_matrix
print("\n--- All Impeachment Categories ---")
cats = conn.execute("SELECT category, COUNT(*) as cnt FROM impeachment_matrix GROUP BY category ORDER BY cnt DESC").fetchall()
for c in cats:
    print(f"  {c['category']:40s} {c['cnt']:>6d}")

# Get violation_type distribution
print("\n--- Judicial Violation Types ---")
types = conn.execute("SELECT violation_type, COUNT(*) as cnt FROM judicial_violations GROUP BY violation_type ORDER BY cnt DESC").fetchall()
for t in types:
    print(f"  {t['violation_type']:40s} {t['cnt']:>6d}")

# Albert Watson premeditation evidence
print("\n--- Albert Watson Premeditation (NS2505044) ---")
albert = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%NS2505044%' OR quote_text LIKE '%Albert%' 
           OR quote_text LIKE '%premeditat%' OR quote_text LIKE '%ex parte order for full custody%')
    ORDER BY relevance_score DESC
    LIMIT 15
""").fetchall()
print(f"Albert premeditation evidence: {len(albert)} rows")
for r in albert[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# Meth use / Officer Randall
print("\n--- Meth Use / Officer Randall ---")
meth = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%meth%' OR quote_text LIKE '%Randall%' 
           OR quote_text LIKE '%drug use%' OR quote_text LIKE '%substance%')
      AND (quote_text LIKE '%Emily%' OR quote_text LIKE '%Watson%' OR quote_text LIKE '%mother%' OR quote_text LIKE '%Randall%')
    ORDER BY relevance_score DESC
    LIMIT 15
""").fetchall()
print(f"Meth/Randall evidence: {len(meth)} rows")
for r in meth[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# Medication coercion
print("\n--- Medication Coercion ---")
med = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%medication%' OR quote_text LIKE '%prescri%' 
           OR quote_text LIKE '%mental health%' OR quote_text LIKE '%Rx%'
           OR quote_text LIKE '%condition%parenting%' OR quote_text LIKE '%medic%condition%')
    ORDER BY relevance_score DESC
    LIMIT 15
""").fetchall()
print(f"Medication coercion evidence: {len(med)} rows")
for r in med[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

# Cavan Berry / FOC connection
print("\n--- Berry/FOC Connection ---")
berry = conn.execute("""
    SELECT id, source_file, quote_text, page_number, category
    FROM evidence_quotes
    WHERE is_duplicate = 0
      AND (quote_text LIKE '%Cavan%' OR quote_text LIKE '%Berry%' 
           OR quote_text LIKE '%990 Terrace%' OR quote_text LIKE '%Ron%Berry%'
           OR quote_text LIKE '%Ladas%Hoopes%')
    ORDER BY relevance_score DESC
    LIMIT 15
""").fetchall()
print(f"Berry/FOC evidence: {len(berry)} rows")
for r in berry[:5]:
    print(f"  ID={r['id']} cat={r['category']} text={r['quote_text'][:150]}...")

conn.close()
print("\n✅ Deep extraction complete")
