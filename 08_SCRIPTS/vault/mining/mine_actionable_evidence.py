"""
EVIDENCE MINER — Extract ALL actionable evidence from harvest_texts for torts, damages,
civil rights claims, and filing vehicles. Maps evidence to adversaries and legal theories.

Writes results into litigation_context.db:
  - actionable_evidence: every citable evidence item with claim mapping
  - evidence_by_adversary: adversary-specific evidence rollup
  - tort_evidence_matrix: claim × evidence cross-reference
"""
import sys, os, json, re, time
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ─── LEGAL CLAIM PATTERNS ───────────────────────────────────────────────
# Each pattern: (claim_id, claim_name, tort_type, adversary, filing_vehicle, [regex_patterns])
CLAIM_PATTERNS = [
    # === JUDGE McNEILL ===
    ("TORT_EXPARTE_ABUSE", "Ex Parte Abuse — Suspension of PT Without Notice",
     "due_process_violation", "McNeill",
     "MSC_SUPERINTENDING, EMERGENCY_PT, COA_366810, FEDERAL_1983",
     [r'ex\s*parte', r'without\s+notice', r'suspend.*parenting\s+time',
      r'ex\s*parte\s+order', r'emergency.*suspend', r'granted.*without.*hearing',
      r'no\s+hearing.*before.*suspend']),

    ("TORT_ACCESS_COURT", "$250 Bond — Denial of Access to Courts",
     "constitutional_violation", "McNeill",
     "MSC_SUPERINTENDING, FEDERAL_1983, COA_366810",
     [r'\$\s*250', r'bond.*(?:motion|filing)', r'pay.*bond.*before.*fil',
      r'Boddie\s*v', r'access\s+to\s+court', r'filing\s+(?:bond|fee|barrier)',
      r'must\s+pay.*before.*(?:file|motion)']),

    ("TORT_EXPARTE_EVIDENCE", "Ex Parte Handling of Merits Evidence (HealthWest to Chambers)",
     "due_process_violation", "McNeill",
     "MSC_SUPERINTENDING, JTC_COMPLAINT, FEDERAL_1983",
     [r'chambers\s+email', r'submit.*(?:directly|chambers)', r'not.*(?:filed|clerk)',
      r'HealthWest.*chambers', r'evaluation.*chambers', r'off.*record',
      r'judge.*private.*email', r'ex\s+parte.*communication.*merit']),

    ("TORT_NO_HEARING", "Denial of Evidentiary Hearing on PT Modification",
     "due_process_violation", "McNeill",
     "MSC_SUPERINTENDING, COA_366810, EMERGENCY_PT",
     [r'no\s+(?:evidentiary\s+)?hearing', r'denied.*hearing', r'without.*evidentiary.*hearing',
      r'MCR\s+3\.207', r'failed\s+to\s+(?:hold|conduct|schedule).*hearing',
      r'best\s+interest.*(?:never|not).*(?:heard|considered|evaluated)']),

    ("TORT_BIAS_UNEQUAL", "Judicial Bias — Unequal Treatment / Media Intake",
     "judicial_misconduct", "McNeill",
     "JTC_COMPLAINT, DISQUALIFY_MCNEILL, FEDERAL_1983",
     [r'unequal.*(?:treatment|intake|access)', r'bias', r'one.*party.*(?:not|denied)',
      r'Canon\s+[123]', r'appearance.*(?:impropriety|bias|partiality)',
      r'favoritism', r'prejudg', r'predetermin']),

    ("TORT_CANON_VIOLATIONS", "Judicial Canon Violations (1, 2A, 3A4)",
     "judicial_misconduct", "McNeill",
     "JTC_COMPLAINT, DISQUALIFY_MCNEILL",
     [r'Canon\s+1', r'Canon\s+2\s*\(?\s*A\s*\)?', r'Canon\s+3\s*\(?\s*A\s*\)?\s*\(?\s*4\s*\)?',
      r'judicial\s+(?:misconduct|ethics)', r'Code\s+of\s+Judicial\s+Conduct',
      r'tenure\s+commission', r'JTC']),

    ("TORT_CONTEMPT_ABUSE", "Abuse of Contempt/Show Cause Powers",
     "abuse_of_process", "McNeill",
     "COA_366810, MSC_SUPERINTENDING",
     [r'show\s+cause', r'contempt.*(?:Pigors|plaintiff|father)',
      r'bench\s+warrant', r'(?:arrest|jail|incarcerat).*(?:Pigors|plaintiff)',
      r'punitive.*(?:sanction|contempt)', r'coercive.*contempt']),

    # === EMILY WATSON ===
    ("TORT_FALSE_PPO", "False/Exaggerated PPO Claims",
     "abuse_of_process", "Watson",
     "VACATE_PPO, FEDERAL_1983",
     [r'PPO.*(?:false|fabricat|exaggerat|unfounded|meritless)',
      r'personal\s+protection\s+order.*(?:dismiss|vacat|deny)',
      r'no\s+(?:evidence|proof).*(?:threat|assault|stalking|harassment)',
      r'PPO.*(?:weapon|tool|leverage)', r'misuse.*PPO']),

    ("TORT_ALIENATION", "Parental Alienation / Interference with PT",
     "tortious_interference", "Watson",
     "EMERGENCY_PT, CONTEMPT, FEDERAL_1983",
     [r'alien(?:ation|ating)', r'interfer.*(?:parent|PT|visitation|relationship)',
      r'deny.*(?:access|contact|communication)', r'withhold.*child',
      r'turned.*(?:child|son).*against', r'gatekeep', r'restrict.*(?:phone|video|call)',
      r'refus.*(?:exchange|parenting\s+time|PT)', r'no.*contact.*(?:child|son)']),

    ("TORT_FALSE_STATEMENTS", "False Statements to Court / Perjury",
     "fraud_on_court", "Watson",
     "CONTEMPT, COA_366810, FEDERAL_1983",
     [r'(?:false|untrue|fabricat|misrepresent).*(?:statement|claim|allegation|testimony)',
      r'(?:lied|lying|perjur)', r'sworn.*(?:false|untrue)',
      r'contradict.*(?:evidence|record|testimony)', r'inconsistent.*statement']),

    ("TORT_EMERGENCY_ABUSE", "Abuse of Emergency Filing Process",
     "abuse_of_process", "Watson",
     "MSC_SUPERINTENDING, EMERGENCY_PT, COA_366810",
     [r'emergency.*(?:ex\s+parte|without\s+notice|motion)',
      r'not.*(?:sworn|verified|affidavit)', r'unsworn.*(?:motion|petition)',
      r'no.*(?:affidavit|verification).*(?:filed|attached)',
      r'MCR\s+3\.207.*(?:violat|fail|requir.*affidavit)']),

    # === EMILY WATSON — Employment / Financial ===
    ("TORT_FINANCIAL_FRAUD", "Financial Misrepresentation (Income/Employment)",
     "fraud", "Watson",
     "FOC_OBJECTION, CONTEMPT, FEDERAL_1983",
     [r'(?:income|employ|wage|salary|payroll).*(?:hidden|undisclos|misrepresent|false)',
      r'Kent\s+County.*(?:employ|payroll|prosecutor)',
      r'(?:deviation|child\s+support).*(?:fraud|incorrect|misstat)',
      r'actual\s+income', r'imputed.*income', r'\$50.*(?:month|child\s+support)',
      r'UCSOM', r'arrears']),

    # === FOC / RUSCO ===
    ("TORT_FOC_BIAS", "FOC Bias / Unequal Facilitation",
     "due_process_violation", "Rusco",
     "FOC_OBJECTION, FEDERAL_1983",
     [r'FOC.*(?:bias|partial|unequal|unfair)', r'Rusco.*(?:bias|unfair|partial)',
      r'friend\s+of\s+(?:the\s+)?court.*(?:bias|unfair)',
      r'FOC.*(?:recommend|report).*(?:one.*sided|biased)',
      r'(?:Rusco|FOC).*(?:chambers|private|ex\s+parte)']),

    # === BARNES (former attorney) ===
    ("TORT_BARNES_WITHDRAW", "Attorney Withdrawal Issues",
     "procedural_violation", "Barnes",
     "COA_366810",
     [r'Barnes.*(?:withdraw|withdrew|withdrawal)', r'P55406.*withdraw',
      r'attorney.*(?:abandon|withdraw|substitut)', r'left.*without.*(?:counsel|attorney)']),

    # === CONSTITUTIONAL / §1983 ===
    ("TORT_DUE_PROCESS_14", "14th Amendment Due Process Violation",
     "civil_rights_1983", "McNeill",
     "FEDERAL_1983, MSC_SUPERINTENDING",
     [r'(?:14th|fourteenth)\s+(?:amendment|amend)', r'due\s+process',
      r'(?:liberty|fundamental.*right).*(?:parent|child|family)',
      r'Troxel\s*v', r'Santosky\s*v', r'Stanley\s*v', r'substantive\s+due\s+process',
      r'procedural\s+due\s+process']),

    ("TORT_FIRST_AMEND", "1st Amendment — Petition / Redress",
     "civil_rights_1983", "McNeill",
     "FEDERAL_1983, MSC_SUPERINTENDING",
     [r'(?:1st|first)\s+(?:amendment|amend)', r'right\s+to\s+petition',
      r'petition.*(?:government|redress|grievance)', r'retaliat.*(?:filing|petition|motion)',
      r'chill.*(?:speech|filing|petition)', r'punish.*(?:filing|exercis)']),

    ("TORT_EQUAL_PROTECTION", "Equal Protection Violation",
     "civil_rights_1983", "McNeill",
     "FEDERAL_1983",
     [r'equal\s+protection', r'(?:class|similarly\s+situated)',
      r'(?:discriminat|unequal).*(?:treatment|application)', r'pro\s*se.*(?:discriminat|bias|unequal)']),

    ("TORT_FAMILY_INTEGRITY", "Right to Family Integrity",
     "civil_rights_1983", "McNeill",
     "FEDERAL_1983, EMERGENCY_PT",
     [r'family\s+integrity', r'(?:right|fundamental).*(?:parent.*child|family\s+unit)',
      r'separation.*(?:parent|father|child)', r'(?:sever|destroy).*(?:bond|relationship|family)',
      r'(?:569|567)\s+(?:days|consecutive)']),

    # === SPOLIATION / EVIDENCE TAMPERING ===
    ("TORT_SPOLIATION", "Spoliation of Evidence",
     "spoliation", "McNeill",
     "SPOLIATION, FEDERAL_1983",
     [r'spoliation', r'(?:destroy|delete|alter|tamper).*(?:evidence|record|document)',
      r'(?:missing|lost|unavailable).*(?:record|transcript|filing)',
      r'(?:clerk|court).*(?:lost|missing|unavailable).*(?:file|record)',
      r'off.*(?:the.*)?record']),

    # === EMOTIONAL DISTRESS / DAMAGES ===
    ("TORT_IIED", "Intentional Infliction of Emotional Distress",
     "emotional_distress", "Watson,McNeill",
     "FEDERAL_1983, STATE_TORT",
     [r'emotional\s+distress', r'mental\s+(?:anguish|suffering|health)',
      r'(?:depress|anxiety|PTSD|trauma|suicid)', r'PHQ.*9', r'C-SSRS',
      r'(?:HealthWest|mental\s+health\s+eval)', r'psychological.*(?:harm|damage|injury)',
      r'(?:F22|delusional)', r'outrageous.*conduct']),

    ("TORT_CHILD_HARM", "Harm to Child from Separation",
     "damages", "Watson,McNeill",
     "EMERGENCY_PT, FEDERAL_1983",
     [r'(?:child|son|Lincoln|minor).*(?:suffer|harm|damage|trauma|distress)',
      r'(?:bond|attachment).*(?:disrupt|sever|damage)',
      r'best\s+interest.*(?:factor|child)', r'(?:developmental|emotional).*(?:harm|impact)',
      r'(?:569|567)\s+(?:days|consecutive).*(?:separation|no.*contact)']),
]

def main():
    t0 = time.time()
    conn = sqlite3.connect(DB_PATH, timeout=180)
    conn.execute("PRAGMA busy_timeout = 180000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB for this heavy operation
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Create output tables
    conn.execute("DROP TABLE IF EXISTS actionable_evidence")
    conn.execute("""
        CREATE TABLE actionable_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT NOT NULL,
            claim_name TEXT NOT NULL,
            tort_type TEXT NOT NULL,
            adversary TEXT NOT NULL,
            filing_vehicle TEXT,
            source_file TEXT NOT NULL,
            harvest_id TEXT,
            evidence_text TEXT NOT NULL,
            context_before TEXT,
            context_after TEXT,
            matched_pattern TEXT,
            char_offset INTEGER,
            line_number INTEGER,
            strength TEXT DEFAULT 'MODERATE',
            admissibility_notes TEXT,
            case_lane TEXT,
            topic TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("DROP TABLE IF EXISTS evidence_by_adversary")
    conn.execute("""
        CREATE TABLE evidence_by_adversary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            claim_name TEXT NOT NULL,
            tort_type TEXT NOT NULL,
            file_count INTEGER,
            hit_count INTEGER,
            strongest_file TEXT,
            strongest_excerpt TEXT,
            filing_vehicles TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("DROP TABLE IF EXISTS tort_evidence_matrix")
    conn.execute("""
        CREATE TABLE tort_evidence_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tort_type TEXT NOT NULL,
            claim_id TEXT NOT NULL,
            adversary TEXT NOT NULL,
            total_files INTEGER,
            total_hits INTEGER,
            avg_strength REAL,
            top_files TEXT,
            filing_vehicles TEXT,
            evidence_sufficient TEXT DEFAULT 'NEEDS_REVIEW',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Load ALL harvest texts (HARVEST_007 = I: drive files)
    print("Loading harvest texts...")
    rows = conn.execute("""
        SELECT harvest_id, original_filename, text_content, doc_subcategory, lane
        FROM harvest_texts
        WHERE harvest_id LIKE 'HARVEST_007%'
        ORDER BY harvest_id
    """).fetchall()
    print(f"  Loaded {len(rows)} HARVEST_007 texts")

    # Also load HARVEST_006 (the earlier 764 files)
    rows_006 = conn.execute("""
        SELECT harvest_id, original_filename, text_content, doc_subcategory, lane
        FROM harvest_texts
        WHERE harvest_id NOT LIKE 'HARVEST_007%'
        ORDER BY harvest_id
    """).fetchall()
    print(f"  Loaded {len(rows_006)} earlier harvest texts")
    all_rows = rows + rows_006
    print(f"  Total: {len(all_rows)} documents to scan")

    # Compile patterns
    compiled_claims = []
    for claim_id, claim_name, tort_type, adversary, vehicles, patterns in CLAIM_PATTERNS:
        compiled = [(p, re.compile(p, re.IGNORECASE)) for p in patterns]
        compiled_claims.append((claim_id, claim_name, tort_type, adversary, vehicles, compiled))

    # Scan every document against every claim pattern
    evidence_rows = []
    claim_file_hits = {}  # (claim_id) -> {filename: (hit_count, best_excerpt, harvest_id)}
    total_hits = 0

    for doc_idx, (harvest_id, filename, text, topic, lane) in enumerate(all_rows):
        if not text:
            continue

        lines = text.split('\n')

        for claim_id, claim_name, tort_type, adversary, vehicles, patterns in compiled_claims:
            doc_hits = 0
            best_excerpt = ""
            best_offset = 0

            for pattern_str, pattern_re in patterns:
                for match in pattern_re.finditer(text):
                    start = match.start()
                    end = match.end()

                    # Extract context: 200 chars before and after
                    ctx_start = max(0, start - 200)
                    ctx_end = min(len(text), end + 200)
                    evidence_text = text[ctx_start:ctx_end].strip()

                    # Narrower excerpt for the match itself
                    match_start = max(0, start - 80)
                    match_end = min(len(text), end + 80)
                    excerpt = text[match_start:match_end].strip()

                    # Line number
                    line_num = text[:start].count('\n') + 1

                    # Context before/after (1 line each)
                    line_idx = line_num - 1
                    ctx_before = lines[max(0, line_idx - 1)] if line_idx > 0 else ""
                    ctx_after = lines[min(len(lines) - 1, line_idx + 1)] if line_idx < len(lines) - 1 else ""

                    # Strength scoring
                    strength = "MODERATE"
                    evidence_lower = evidence_text.lower()
                    if any(kw in evidence_lower for kw in ['it is ordered', 'it is hereby ordered', 'the court orders']):
                        strength = "STRONG_COURT_ORDER"
                    elif any(kw in evidence_lower for kw in ['sworn', 'affidavit', 'under penalty of perjury', 'verified']):
                        strength = "STRONG_SWORN"
                    elif any(kw in evidence_lower for kw in ['transcript', 'testimony', 'on the record', 'q:', 'a:']):
                        strength = "STRONG_TESTIMONY"
                    elif any(kw in evidence_lower for kw in ['email', 'sent:', 'from:', 'subject:', 'date:']):
                        strength = "MODERATE_DOCUMENTARY"
                    elif any(kw in evidence_lower for kw in ['police', 'officer', 'report', 'incident']):
                        strength = "STRONG_OFFICIAL"

                    # Admissibility
                    admissibility = "Potentially admissible"
                    if 'COURT_ORDER' in strength:
                        admissibility = "Judicial notice — court's own records (MRE 201)"
                    elif 'SWORN' in strength:
                        admissibility = "Sworn statement — admissible as affidavit evidence"
                    elif 'TESTIMONY' in strength:
                        admissibility = "Prior testimony — admissible under MRE 801(d)(1) or 804(b)(1)"
                    elif 'OFFICIAL' in strength:
                        admissibility = "Official record — public records exception MRE 803(8)"
                    elif 'DOCUMENTARY' in strength:
                        admissibility = "Documentary evidence — authenticate under MRE 901"

                    evidence_rows.append((
                        claim_id, claim_name, tort_type, adversary, vehicles,
                        filename, harvest_id, evidence_text,
                        ctx_before[:500], ctx_after[:500],
                        pattern_str, start, line_num,
                        strength, admissibility, lane or '', topic or ''
                    ))

                    doc_hits += 1
                    total_hits += 1
                    if len(excerpt) > len(best_excerpt):
                        best_excerpt = excerpt
                        best_offset = start

            if doc_hits > 0:
                key = claim_id
                if key not in claim_file_hits:
                    claim_file_hits[key] = {}
                if filename not in claim_file_hits[key] or doc_hits > claim_file_hits[key][filename][0]:
                    claim_file_hits[key][filename] = (doc_hits, best_excerpt, harvest_id)

        if (doc_idx + 1) % 200 == 0:
            print(f"  Scanned {doc_idx+1}/{len(all_rows)} docs, {total_hits:,} hits so far...")

    print(f"\nScan complete: {total_hits:,} evidence hits across {len(all_rows)} documents")

    # Batch insert actionable_evidence
    print(f"Inserting {len(evidence_rows):,} evidence rows...")
    conn.executemany("""
        INSERT INTO actionable_evidence
        (claim_id, claim_name, tort_type, adversary, filing_vehicle,
         source_file, harvest_id, evidence_text, context_before, context_after,
         matched_pattern, char_offset, line_number, strength, admissibility_notes,
         case_lane, topic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, evidence_rows)
    conn.commit()
    print("  actionable_evidence inserted.")

    # Build evidence_by_adversary
    print("Building evidence_by_adversary...")
    adversary_data = {}
    for claim_id, claim_name, tort_type, adversary, vehicles, patterns in CLAIM_PATTERNS:
        for adv in adversary.split(','):
            adv = adv.strip()
            key = (adv, claim_id)
            files = claim_file_hits.get(claim_id, {})
            if not files:
                continue
            file_count = len(files)
            hit_count = sum(f[0] for f in files.values())
            # Find strongest file
            strongest = max(files.items(), key=lambda x: x[1][0])
            adversary_data[key] = (
                adv, claim_id, claim_name, tort_type,
                file_count, hit_count,
                strongest[0], strongest[1][1][:500],
                vehicles
            )

    if adversary_data:
        conn.executemany("""
            INSERT INTO evidence_by_adversary
            (adversary, claim_id, claim_name, tort_type, file_count, hit_count,
             strongest_file, strongest_excerpt, filing_vehicles)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, list(adversary_data.values()))
        conn.commit()
    print(f"  {len(adversary_data)} adversary-claim rows inserted.")

    # Build tort_evidence_matrix
    print("Building tort_evidence_matrix...")

    # Pre-fetch all strength values in ONE query instead of N per-claim round-trips
    _all_strengths = conn.execute(
        "SELECT claim_id, strength FROM actionable_evidence"
    ).fetchall()
    _strength_by_claim: dict = defaultdict(list)
    for _r in _all_strengths:
        _cid, _s = _r[0], _r[1]
        if 'STRONG' in _s:
            _strength_by_claim[_cid].append(3)
        elif 'MODERATE' in _s:
            _strength_by_claim[_cid].append(2)
        else:
            _strength_by_claim[_cid].append(1)

    matrix_rows = []
    for claim_id, claim_name, tort_type, adversary, vehicles, patterns in CLAIM_PATTERNS:
        files = claim_file_hits.get(claim_id, {})
        if not files:
            matrix_rows.append((
                tort_type, claim_id, adversary, 0, 0, 0.0, '[]', vehicles, 'INSUFFICIENT'
            ))
            continue

        total_files = len(files)
        total_file_hits = sum(f[0] for f in files.values())

        # Strength scoring — use pre-fetched data (no per-claim query)
        strength_scores = _strength_by_claim.get(claim_id, [])
        avg_str = sum(strength_scores) / len(strength_scores) if strength_scores else 0

        # Top files by hit count
        sorted_files = sorted(files.items(), key=lambda x: -x[1][0])[:5]
        top = json.dumps([f[0] for f in sorted_files])

        # Sufficiency
        if total_files >= 10 and avg_str >= 2.5:
            sufficiency = "OVERWHELMING"
        elif total_files >= 5 and avg_str >= 2.0:
            sufficiency = "STRONG"
        elif total_files >= 3:
            sufficiency = "MODERATE"
        elif total_files >= 1:
            sufficiency = "DEVELOPING"
        else:
            sufficiency = "INSUFFICIENT"

        matrix_rows.append((
            tort_type, claim_id, adversary, total_files, total_file_hits,
            round(avg_str, 2), top, vehicles, sufficiency
        ))

    conn.executemany("""
        INSERT INTO tort_evidence_matrix
        (tort_type, claim_id, adversary, total_files, total_hits,
         avg_strength, top_files, filing_vehicles, evidence_sufficient)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, matrix_rows)
    conn.commit()
    print(f"  {len(matrix_rows)} matrix rows inserted.")

    # Create indexes for fast queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ae_claim ON actionable_evidence(claim_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ae_adversary ON actionable_evidence(adversary)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ae_tort ON actionable_evidence(tort_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ae_strength ON actionable_evidence(strength)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ae_source ON actionable_evidence(source_file)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_eba_adversary ON evidence_by_adversary(adversary)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tem_tort ON tort_evidence_matrix(tort_type)")
    conn.commit()

    # ─── PRINT SUMMARY REPORT ───────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  ACTIONABLE EVIDENCE MINING REPORT")
    print("=" * 80)

    # By adversary
    print("\n--- EVIDENCE BY ADVERSARY ---")
    adv_summary = conn.execute("""
        SELECT adversary, COUNT(DISTINCT claim_id), SUM(hit_count), SUM(file_count)
        FROM evidence_by_adversary
        GROUP BY adversary ORDER BY SUM(hit_count) DESC
    """).fetchall()
    for a in adv_summary:
        print(f"  {a[0]:15s}  {a[1]:2d} claims  {a[2]:6,d} hits  {a[3]:4d} files")

    # By tort type
    print("\n--- EVIDENCE BY TORT TYPE ---")
    tort_summary = conn.execute("""
        SELECT tort_type, COUNT(*), SUM(total_files), SUM(total_hits), 
               ROUND(AVG(avg_strength),2), GROUP_CONCAT(DISTINCT evidence_sufficient)
        FROM tort_evidence_matrix
        GROUP BY tort_type ORDER BY SUM(total_hits) DESC
    """).fetchall()
    for t in tort_summary:
        print(f"  {t[0]:30s}  {t[1]:2d} claims  {t[2]:5d} files  {t[3]:6,d} hits  strength={t[4]}  [{t[5]}]")

    # Individual claim breakdown
    print("\n--- TORT EVIDENCE MATRIX (all claims) ---")
    matrix = conn.execute("""
        SELECT claim_id, adversary, total_files, total_hits, 
               ROUND(avg_strength,1), evidence_sufficient, filing_vehicles
        FROM tort_evidence_matrix
        ORDER BY total_hits DESC
    """).fetchall()
    print(f"  {'CLAIM_ID':35s} {'ADV':10s} {'FILES':>6s} {'HITS':>7s} {'STR':>4s} {'SUFFICIENCY':>14s}")
    print(f"  {'-'*35} {'-'*10} {'-'*6} {'-'*7} {'-'*4} {'-'*14}")
    for m in matrix:
        print(f"  {m[0]:35s} {m[1]:10s} {m[2]:6d} {m[3]:7,d} {m[4]:4.1f} {m[5]:>14s}")

    # Strength distribution
    print("\n--- EVIDENCE STRENGTH DISTRIBUTION ---")
    strengths = conn.execute("""
        SELECT strength, COUNT(*) FROM actionable_evidence
        GROUP BY strength ORDER BY COUNT(*) DESC
    """).fetchall()
    for s in strengths:
        print(f"  {s[0]:30s}  {s[1]:,d}")

    # Top 20 most-cited files
    print("\n--- TOP 20 EVIDENCE FILES (by claim coverage) ---")
    top_files = conn.execute("""
        SELECT source_file, COUNT(DISTINCT claim_id) as claims, COUNT(*) as hits,
               GROUP_CONCAT(DISTINCT adversary) as adversaries,
               GROUP_CONCAT(DISTINCT strength) as strengths
        FROM actionable_evidence
        GROUP BY source_file
        ORDER BY claims DESC, hits DESC
        LIMIT 20
    """).fetchall()
    for f in top_files:
        print(f"  {f[0][:60]:60s}  {f[1]:2d} claims  {f[2]:5,d} hits  vs:{f[3]}")

    # Sufficiency summary
    print("\n--- SUFFICIENCY SUMMARY ---")
    suff = conn.execute("""
        SELECT evidence_sufficient, COUNT(*), GROUP_CONCAT(claim_id, ', ')
        FROM tort_evidence_matrix
        GROUP BY evidence_sufficient
        ORDER BY CASE evidence_sufficient
            WHEN 'OVERWHELMING' THEN 1
            WHEN 'STRONG' THEN 2
            WHEN 'MODERATE' THEN 3
            WHEN 'DEVELOPING' THEN 4
            WHEN 'INSUFFICIENT' THEN 5
        END
    """).fetchall()
    for s in suff:
        print(f"  {s[0]:14s}  {s[1]:2d} claims: {s[2][:200]}")

    elapsed = time.time() - t0
    total_ae = conn.execute("SELECT COUNT(*) FROM actionable_evidence").fetchone()[0]
    print(f"\n=== COMPLETE in {elapsed:.1f}s ===")
    print(f"  actionable_evidence:    {total_ae:,d} rows")
    print(f"  evidence_by_adversary:  {len(adversary_data)} rows")
    print(f"  tort_evidence_matrix:   {len(matrix_rows)} rows")

    conn.close()

if __name__ == '__main__':
    main()
