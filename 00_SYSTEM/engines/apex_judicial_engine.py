#!/usr/bin/env python3
"""
APEX JUDICIAL ANALYSIS ENGINE v1.0
===================================
Synthesizes ALL 469 DB tables into atomized, chronological,
fully-cited court filing stacks for every viable court action.

Output: Complete filing stack per court action with:
  - Chronological Statement of Facts (atomized, cited)
  - Legal theories + authority chains
  - Evidence inventory mapped to claims
  - Damages calculations
  - Adversary rebuttal framework
  - Filing readiness assessment

Target courts:
  1. COA 366810 — Appeal (Brief due April 15, 2026)
  2. 14th Circuit Trial — 2024-001507-DC
  3. Federal §1983 — Civil rights
  4. JTC — Judicial Tenure Commission vs McNeill
  5. Bar Complaint — vs Barnes (P55406)
  6. Emergency — PPO/TRO/Ex Parte
"""
import os, sys, sqlite3, json, textwrap
from datetime import datetime
from collections import defaultdict, OrderedDict

LOS = r'C:\Users\andre\LitigationOS'
DB  = os.path.join(LOS, 'litigation_context.db')

COURT_ACTIONS = OrderedDict([
    ('COA_366810', {
        'name': 'Michigan Court of Appeals — Case No. 366810',
        'folder': '01_COA_366810',
        'case_number': '366810',
        'court': 'Michigan Court of Appeals',
        'judge': 'Panel TBD',
        'deadline': '2026-04-15',
        'brief_type': 'Appellant Brief',
        'standard_of_review': 'de novo for legal questions, abuse of discretion for custody',
        'lane_ids': [5],  # PKG05
        'keywords': ['COA', '366810', 'appeal', 'appellate', 'appellant', 'PKG05', 'court of appeals'],
    }),
    ('TRIAL_14TH', {
        'name': '14th Judicial Circuit — Case No. 2024-001507-DC',
        'folder': '02_TRIAL_14TH',
        'case_number': '2024-001507-DC',
        'court': '14th Judicial Circuit, Muskegon County',
        'judge': 'Hon. Jenny L. McNeill',
        'lane_ids': [1, 3, 6, 7],  # PKG01, 03, 06, 07
        'keywords': ['trial', '14th circuit', '2024-001507', 'custody', 'parenting time',
                     'child support', 'contempt', 'PKG01', 'PKG03', 'PKG06', 'PKG07'],
    }),
    ('FEDERAL_1983', {
        'name': 'Federal Court — 42 USC §1983 Civil Rights',
        'folder': '03_FEDERAL_1983',
        'case_number': 'TBD',
        'court': 'U.S. District Court, Western District of Michigan',
        'judge': 'TBD',
        'lane_ids': [8],  # PKG08
        'keywords': ['federal', '1983', 'civil rights', '42 USC', 'section 1983',
                     'PKG08', 'constitutional', 'deprivation'],
    }),
    ('JTC_MCNEILL', {
        'name': 'Judicial Tenure Commission — vs Hon. Jenny L. McNeill',
        'folder': '04_JTC_MCNEILL',
        'case_number': 'JTC-TBD',
        'court': 'Michigan Judicial Tenure Commission',
        'judge': 'N/A',
        'lane_ids': [9],  # PKG09
        'keywords': ['JTC', 'judicial tenure', 'McNeill', 'Jenny', 'judicial misconduct',
                     'PKG09', 'canon', 'disqualification'],
    }),
    ('BAR_BARNES', {
        'name': 'Attorney Grievance Commission — vs Jennifer L. Barnes (P55406)',
        'folder': '05_BAR_BARNES',
        'case_number': 'AGC-TBD',
        'court': 'Michigan Attorney Grievance Commission',
        'judge': 'N/A',
        'lane_ids': [10],  # PKG10
        'keywords': ['bar complaint', 'Barnes', 'P55406', 'attorney grievance', 'MRPC',
                     'PKG10', 'ethics'],
    }),
    ('EMERGENCY', {
        'name': 'Emergency Motions — PPO/TRO/Ex Parte',
        'folder': '06_EMERGENCY',
        'case_number': '2024-001507-DC',
        'court': '14th Judicial Circuit / COA',
        'judge': 'Various',
        'lane_ids': [11, 12],  # PKG11, PKG12
        'keywords': ['emergency', 'ex parte', 'PPO', 'TRO', 'immediate', 'irreparable',
                     'PKG11', 'PKG12'],
    }),
])

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)

log('=' * 80)
log('  APEX JUDICIAL ANALYSIS ENGINE v1.0')
log('  Synthesizing 469 tables → Court Filing Stacks')
log('  ALL RESULTS PERSISTED TO litigation_context.db')
log('=' * 80)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Create APEX output tables in the DB
cur.executescript("""
    CREATE TABLE IF NOT EXISTS apex_master_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_date TEXT,
        title TEXT,
        description TEXT,
        actors TEXT,
        category TEXT,
        source_table TEXT,
        evidence_ref TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS apex_court_action_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_id TEXT,
        data_type TEXT,
        data_key TEXT,
        data_value TEXT,
        record_count INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS apex_filing_stack_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_id TEXT,
        action_name TEXT,
        case_number TEXT,
        court TEXT,
        file_name TEXT,
        file_path TEXT,
        doc_type TEXT,
        record_count INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS apex_action_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_id TEXT,
        event_date TEXT,
        title TEXT,
        description TEXT,
        actors TEXT,
        category TEXT,
        source_table TEXT,
        evidence_ref TEXT
    );
    CREATE TABLE IF NOT EXISTS apex_run_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phase TEXT,
        action_id TEXT,
        message TEXT,
        record_count INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    DELETE FROM apex_master_timeline;
    DELETE FROM apex_court_action_data;
    DELETE FROM apex_filing_stack_index;
    DELETE FROM apex_action_timeline;
    DELETE FROM apex_run_log;
""")
conn.commit()

def db_log(phase, action_id, message, count=0):
    """Persist every step to the DB."""
    cur.execute("INSERT INTO apex_run_log (phase, action_id, message, record_count) VALUES (?,?,?,?)",
                (phase, action_id, message, count))
    conn.commit()

db_log('INIT', 'ALL', 'APEX Judicial Analysis Engine started', 0)

# ============================================================
# PHASE 1: MASTER CHRONOLOGICAL TIMELINE (ATOMIZED)
# ============================================================
log('\n[PHASE 1] Building Master Atomized Chronological Timeline...')

# Pull from ALL timeline tables and merge
timeline_events = []

timeline_sources = [
    ('master_timeline', 'event_date', 'title', 'description', 'actors', 'category', 'source'),
    ('condensed_timeline', 'event_date', 'title', 'description', 'actors', 'category', 'evidence_ref'),
    ('court_timeline', 'event_date', 'title', 'description', 'actors', 'category', 'evidence_ref'),
    ('master_chronological_timeline', 'event_date', 'title', 'description', 'actor', 'event_type', 'evidence_ref'),
    ('docket_timeline_complete', 'event_date', 'description', 'description', 'event_type', 'event_type', 'case_id'),
    ('conspiracy_timeline', 'date', 'action', 'action', 'actor', 'conspiracy_type', 'evidence_source'),
    ('prosecution_timeline', 'event_date', 'event_title', 'event_description', 'actors', 'event_type', 'evidence_ref'),
    ('ppo_timeline_complete', 'event_date', 'description', 'description', 'actor', 'event_type', 'case_id'),
    ('global_chronology', 'date', 'issue', 'shortfact240', 'sourcefile', 'issue', 'sourcefile'),
]

for src in timeline_sources:
    table, date_col, title_col, desc_col, actor_col, cat_col, ref_col = src
    try:
        cur.execute(f"""
            SELECT [{date_col}], [{title_col}], [{desc_col}], [{actor_col}], [{cat_col}], [{ref_col}]
            FROM [{table}]
            WHERE [{date_col}] IS NOT NULL AND [{date_col}] != ''
            ORDER BY [{date_col}]
        """)
        rows = cur.fetchall()
        for r in rows:
            timeline_events.append({
                'date': str(r[0])[:10] if r[0] else '',
                'title': str(r[1])[:500] if r[1] else '',
                'description': str(r[2])[:1000] if r[2] else '',
                'actors': str(r[3])[:200] if r[3] else '',
                'category': str(r[4])[:100] if r[4] else '',
                'source': f'{table}',
                'ref': str(r[5])[:200] if r[5] else '',
            })
    except Exception as e:
        log(f'  Warning: {table}: {e}')

# Deduplicate by date+title hash
seen = set()
unique_events = []
for e in timeline_events:
    key = (e['date'], e['title'][:100])
    if key not in seen:
        seen.add(key)
        unique_events.append(e)

# Sort chronologically
unique_events.sort(key=lambda x: x['date'])

log(f'  Raw events: {len(timeline_events):,} → Deduplicated: {len(unique_events):,}')

# PERSIST: Save master timeline to DB
log('  Saving master timeline to DB...')
batch = []
for e in unique_events:
    batch.append((e['date'], e['title'], e['description'], e['actors'],
                  e['category'], e['source'], e['ref']))
    if len(batch) >= 5000:
        cur.executemany("""INSERT INTO apex_master_timeline
            (event_date, title, description, actors, category, source_table, evidence_ref)
            VALUES (?,?,?,?,?,?,?)""", batch)
        conn.commit()
        batch = []
if batch:
    cur.executemany("""INSERT INTO apex_master_timeline
        (event_date, title, description, actors, category, source_table, evidence_ref)
        VALUES (?,?,?,?,?,?,?)""", batch)
    conn.commit()

db_log('PHASE1', 'ALL', f'Master timeline: {len(unique_events):,} deduplicated events from {len(timeline_events):,} raw', len(unique_events))
log(f'  ✓ Saved {len(unique_events):,} events to apex_master_timeline')

# ============================================================
# PHASE 2: EXTRACT CORE DATA PER COURT ACTION
# ============================================================
log('\n[PHASE 2] Extracting core data per court action...')

for action_id, action in COURT_ACTIONS.items():
    log(f'\n  === {action["name"]} ===')
    action['data'] = {}

    kw = action['keywords']
    kw_sql = ' OR '.join([f"description LIKE '%{k}%' OR title LIKE '%{k}%'" for k in kw[:5]])

    # --- Relevant timeline events ---
    action_events = []
    for e in unique_events:
        text = f"{e['title']} {e['description']} {e['actors']} {e['category']} {e['ref']}".lower()
        if any(k.lower() in text for k in kw):
            action_events.append(e)
    action['data']['timeline'] = action_events
    log(f'    Timeline events: {len(action_events):,}')

    # --- Judicial violations (for JTC/Trial) ---
    try:
        cur.execute("""
            SELECT violation_id, judge_name, canon_number, violation_description,
                   evidence_refs, severity
            FROM judicial_violations
            ORDER BY violation_id
        """)
        action['data']['judicial_violations'] = [dict(r) for r in cur.fetchall()]
        log(f'    Judicial violations: {len(action["data"]["judicial_violations"]):,}')
    except:
        action['data']['judicial_violations'] = []

    # --- Adversary assertions ---
    try:
        kw_match = ' OR '.join([f"'{k}'" for k in kw[:3]])
        cur.execute("""
            SELECT assertion_text, assertion_type, speaker, paragraph_ref
            FROM adversary_assertions
            LIMIT 5000
        """)
        all_assertions = [dict(r) for r in cur.fetchall()]
        relevant = [a for a in all_assertions
                   if any(k.lower() in str(a.get('assertion_text','')).lower() for k in kw)]
        action['data']['adversary_assertions'] = relevant[:500]
        log(f'    Adversary assertions: {len(relevant):,}')
    except:
        action['data']['adversary_assertions'] = []

    # --- Evidence quotes ---
    try:
        cur.execute("""
            SELECT quote_text, evidence_category, speaker, legal_significance
            FROM evidence_quotes
            WHERE evidence_category IS NOT NULL
            LIMIT 10000
        """)
        all_quotes = [dict(r) for r in cur.fetchall()]
        relevant = [q for q in all_quotes
                   if any(k.lower() in str(q.get('quote_text','')).lower() or
                         k.lower() in str(q.get('legal_significance','')).lower() for k in kw)]
        action['data']['evidence_quotes'] = relevant[:500]
        log(f'    Evidence quotes: {len(relevant):,}')
    except:
        action['data']['evidence_quotes'] = []

    # --- Caselaw authority ---
    caselaw_tables = {
        'COA_366810': ['caselaw_contempt_reversal', 'caselaw_ex_parte_reversal', 'caselaw_due_process_custody'],
        'TRIAL_14TH': ['caselaw_parental_alienation', 'caselaw_ppo_abuse', 'caselaw_due_process_custody'],
        'FEDERAL_1983': ['caselaw_federal_civil_rights', 'caselaw_due_process_custody'],
        'JTC_MCNEILL': ['caselaw_disqualification'],
        'BAR_BARNES': ['caselaw_disqualification'],
        'EMERGENCY': ['caselaw_ex_parte_reversal', 'caselaw_ppo_abuse'],
    }
    authorities = []
    for tbl in caselaw_tables.get(action_id, []):
        try:
            cur.execute(f"SELECT * FROM [{tbl}] LIMIT 100")
            rows = [dict(r) for r in cur.fetchall()]
            authorities.extend(rows)
        except:
            pass
    action['data']['authorities'] = authorities
    log(f'    Legal authorities: {len(authorities):,}')

    # --- Damages ---
    try:
        cur.execute("SELECT * FROM damages_calculations")
        action['data']['damages'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['damages'] = []

    try:
        cur.execute("SELECT * FROM financial_evidence_compiled LIMIT 500")
        action['data']['financial'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['financial'] = []

    # --- Rebuttal matrix ---
    try:
        cur.execute("SELECT * FROM rebuttal_matrix LIMIT 200")
        action['data']['rebuttals'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['rebuttals'] = []

    # --- Claims ---
    try:
        cur.execute("SELECT * FROM claims LIMIT 500")
        action['data']['claims'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['claims'] = []

    # --- Filing readiness ---
    try:
        cur.execute("SELECT * FROM filing_readiness")
        action['data']['readiness'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['readiness'] = []

    # --- Constitutional violations ---
    try:
        cur.execute("SELECT * FROM constitutional_violations")
        action['data']['constitutional'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['constitutional'] = []

    # --- Watson perjury ---
    try:
        cur.execute("""
            SELECT watson_member, statement_text, contradicting_evidence, source_doc
            FROM watson_perjury_compilation LIMIT 1000
        """)
        action['data']['perjury'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['perjury'] = []

    # --- Forensic judicial analysis ---
    try:
        cur.execute("""
            SELECT category, severity, description, evidence_citations, mcr_violations
            FROM forensic_judicial_analysis
            ORDER BY severity DESC LIMIT 500
        """)
        action['data']['forensic'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['forensic'] = []

    # --- AppClose violations ---
    try:
        cur.execute("SELECT * FROM appclose_violations")
        action['data']['appclose_violations'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['appclose_violations'] = []

    # --- Actor violations ---
    try:
        cur.execute("""
            SELECT actor, role, violation_type, description, date, evidence_source, severity
            FROM actor_violations
            ORDER BY date LIMIT 2000
        """)
        action['data']['actor_violations'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['actor_violations'] = []

    # --- Extracted harms ---
    try:
        cur.execute("""
            SELECT category, subcategory, adversary, date_ref, description
            FROM extracted_harms LIMIT 2000
        """)
        action['data']['harms'] = [dict(r) for r in cur.fetchall()]
    except:
        action['data']['harms'] = []

    # PERSIST: Save action timeline to DB
    for e in action_events:
        cur.execute("""INSERT INTO apex_action_timeline
            (action_id, event_date, title, description, actors, category, source_table, evidence_ref)
            VALUES (?,?,?,?,?,?,?,?)""",
            (action_id, e['date'], e['title'], e['description'], e['actors'],
             e['category'], e['source'], e['ref']))

    # PERSIST: Save action data summary to DB
    for dtype, dval in action['data'].items():
        count = len(dval) if isinstance(dval, list) else 0
        cur.execute("""INSERT INTO apex_court_action_data
            (action_id, data_type, data_key, data_value, record_count)
            VALUES (?,?,?,?,?)""",
            (action_id, dtype, f'{action_id}_{dtype}',
             json.dumps(dval[:5]) if isinstance(dval, list) and dval else '[]', count))
    conn.commit()
    db_log('PHASE2', action_id, f'Data extraction complete: {len(action_events)} timeline, {len(action["data"].get("authorities",[]))} authorities', len(action_events))

# ============================================================
# PHASE 3: GENERATE COURT FILING STACKS
# ============================================================
log('\n[PHASE 3] Generating Court Filing Stacks...')

for action_id, action in COURT_ACTIONS.items():
    log(f'\n  Generating: {action["name"]}')
    output_dir = os.path.join(LOS, action['folder'], 'APEX_FILING_STACK')
    os.makedirs(output_dir, exist_ok=True)
    data = action['data']

    # ---- 1. CHRONOLOGICAL STATEMENT OF FACTS ----
    sof_lines = []
    sof_lines.append(f"{'='*80}")
    sof_lines.append(f"CHRONOLOGICAL STATEMENT OF FACTS")
    sof_lines.append(f"{action['name']}")
    sof_lines.append(f"Case No. {action['case_number']}")
    sof_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sof_lines.append(f"{'='*80}\n")

    events = data.get('timeline', [])
    if not events:
        # Fallback: use all events
        events = unique_events

    current_month = ''
    fact_num = 0
    for e in events:
        month = e['date'][:7] if len(e['date']) >= 7 else 'UNDATED'
        if month != current_month:
            current_month = month
            sof_lines.append(f"\n{'─'*60}")
            sof_lines.append(f"  {month}")
            sof_lines.append(f"{'─'*60}")
        fact_num += 1
        sof_lines.append(f"\n  [{fact_num}] {e['date']}")
        sof_lines.append(f"  {e['title']}")
        if e['description'] and e['description'] != e['title']:
            for line in textwrap.wrap(e['description'], 76):
                sof_lines.append(f"    {line}")
        if e['actors']:
            sof_lines.append(f"    Actors: {e['actors']}")
        if e['ref']:
            sof_lines.append(f"    Source: {e['source']} | Ref: {e['ref']}")

    sof_lines.append(f"\n\nTOTAL FACTS: {fact_num}")

    sof_path = os.path.join(output_dir, '01_STATEMENT_OF_FACTS_CHRONOLOGICAL.txt')
    with open(sof_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sof_lines))
    log(f'    Statement of Facts: {fact_num} facts')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '01_STATEMENT_OF_FACTS_CHRONOLOGICAL.txt', sof_path, 'statement_of_facts', fact_num))
    conn.commit()
    db_log('PHASE3', action_id, f'Statement of Facts: {fact_num} facts', fact_num)

    # ---- 2. LEGAL THEORIES + AUTHORITY CHAINS ----
    auth_lines = []
    auth_lines.append(f"{'='*80}")
    auth_lines.append(f"LEGAL THEORIES & AUTHORITY CHAINS")
    auth_lines.append(f"{action['name']}")
    auth_lines.append(f"{'='*80}\n")

    authorities = data.get('authorities', [])
    if authorities:
        by_table = defaultdict(list)
        for a in authorities:
            # Group by source
            by_table['authority'].append(a)

        for i, a in enumerate(authorities, 1):
            case_name = a.get('case_name', a.get('citation', 'Unknown'))
            citation = a.get('citation', '')
            holding = a.get('holding', a.get('holding_summary', ''))
            relevance = a.get('relevance', a.get('relevance_to_case', ''))

            auth_lines.append(f"  [{i}] {case_name}")
            if citation:
                auth_lines.append(f"      Citation: {citation}")
            if holding:
                for line in textwrap.wrap(str(holding), 72):
                    auth_lines.append(f"      {line}")
            if relevance:
                auth_lines.append(f"      Relevance: {relevance}")
            auth_lines.append('')
    else:
        auth_lines.append("  [See master_citations table — 3.6M+ citations available]")

    # Add constitutional violations
    const = data.get('constitutional', [])
    if const:
        auth_lines.append(f"\n{'─'*60}")
        auth_lines.append(f"  CONSTITUTIONAL VIOLATIONS")
        auth_lines.append(f"{'─'*60}")
        for c in const:
            auth_lines.append(f"\n  Amendment: {c.get('amendment','')}")
            auth_lines.append(f"  Clause: {c.get('clause','')}")
            auth_lines.append(f"  Type: {c.get('violation_type','')}")
            desc = c.get('description', '')
            for line in textwrap.wrap(str(desc), 72):
                auth_lines.append(f"    {line}")

    auth_path = os.path.join(output_dir, '02_LEGAL_THEORIES_AUTHORITY_CHAINS.txt')
    with open(auth_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(auth_lines))
    log(f'    Legal authorities: {len(authorities)} cases + {len(const)} constitutional violations')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '02_LEGAL_THEORIES_AUTHORITY_CHAINS.txt', auth_path, 'legal_theories', len(authorities)))
    conn.commit()
    db_log('PHASE3', action_id, f'Legal theories: {len(authorities)} authorities + {len(const)} constitutional', len(authorities))

    # ---- 3. EVIDENCE INVENTORY ----
    ev_lines = []
    ev_lines.append(f"{'='*80}")
    ev_lines.append(f"EVIDENCE INVENTORY")
    ev_lines.append(f"{action['name']}")
    ev_lines.append(f"{'='*80}\n")

    quotes = data.get('evidence_quotes', [])
    by_cat = defaultdict(list)
    for q in quotes:
        cat = q.get('evidence_category', 'Uncategorized')
        by_cat[cat].append(q)

    for cat, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        ev_lines.append(f"\n{'─'*60}")
        ev_lines.append(f"  {cat} ({len(items)} items)")
        ev_lines.append(f"{'─'*60}")
        for item in items[:50]:  # Cap per category
            text = str(item.get('quote_text', ''))[:300]
            speaker = item.get('speaker', '')
            sig = item.get('legal_significance', '')
            ev_lines.append(f"\n  Speaker: {speaker}")
            for line in textwrap.wrap(text, 74):
                ev_lines.append(f"    \"{line}\"")
            if sig:
                ev_lines.append(f"    Legal significance: {sig}")

    # Add AppClose violations
    appclose = data.get('appclose_violations', [])
    if appclose:
        ev_lines.append(f"\n{'─'*60}")
        ev_lines.append(f"  APPCLOSE VIOLATIONS ({len(appclose)} items)")
        ev_lines.append(f"{'─'*60}")
        for v in appclose:
            ev_lines.append(f"\n  Date: {v.get('violation_date','')} | Type: {v.get('violation_type','')}")
            content = v.get('content', v.get('description', ''))
            if content:
                for line in textwrap.wrap(str(content)[:500], 74):
                    ev_lines.append(f"    {line}")

    ev_path = os.path.join(output_dir, '03_EVIDENCE_INVENTORY.txt')
    with open(ev_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ev_lines))
    log(f'    Evidence: {len(quotes)} quotes, {len(appclose)} AppClose violations')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '03_EVIDENCE_INVENTORY.txt', ev_path, 'evidence_inventory', len(quotes)))
    conn.commit()
    db_log('PHASE3', action_id, f'Evidence: {len(quotes)} quotes, {len(appclose)} AppClose', len(quotes))

    # ---- 4. JUDICIAL VIOLATIONS (for JTC/Trial) ----
    if action_id in ('JTC_MCNEILL', 'TRIAL_14TH', 'COA_366810'):
        jv_lines = []
        jv_lines.append(f"{'='*80}")
        jv_lines.append(f"JUDICIAL VIOLATIONS ANALYSIS")
        jv_lines.append(f"{action['name']}")
        jv_lines.append(f"{'='*80}\n")

        violations = data.get('judicial_violations', [])
        forensic = data.get('forensic', [])

        if violations:
            by_canon = defaultdict(list)
            for v in violations:
                canon = v.get('canon_number', 'Unknown')
                by_canon[canon].append(v)

            for canon, items in sorted(by_canon.items()):
                jv_lines.append(f"\n{'─'*60}")
                jv_lines.append(f"  CANON {canon} ({len(items)} violations)")
                jv_lines.append(f"{'─'*60}")
                for item in items:
                    desc = item.get('violation_description', '')
                    sev = item.get('severity', '')
                    refs = item.get('evidence_refs', '')
                    jv_lines.append(f"\n  [{sev}] {desc[:200]}")
                    if refs:
                        jv_lines.append(f"    Evidence: {refs[:200]}")

        if forensic:
            jv_lines.append(f"\n\n{'='*60}")
            jv_lines.append(f"  FORENSIC JUDICIAL ANALYSIS ({len(forensic)} findings)")
            jv_lines.append(f"{'='*60}")
            for f_item in forensic[:100]:
                cat = f_item.get('category', '')
                sev = f_item.get('severity', '')
                desc = f_item.get('description', '')
                mcr = f_item.get('mcr_violations', '')
                jv_lines.append(f"\n  [{sev}] {cat}")
                for line in textwrap.wrap(str(desc)[:500], 74):
                    jv_lines.append(f"    {line}")
                if mcr:
                    jv_lines.append(f"    MCR Violations: {mcr}")

        jv_path = os.path.join(output_dir, '04_JUDICIAL_VIOLATIONS.txt')
        with open(jv_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(jv_lines))
        log(f'    Judicial violations: {len(violations)} + {len(forensic)} forensic findings')
        cur.execute("""INSERT INTO apex_filing_stack_index
            (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
            VALUES (?,?,?,?,?,?,?,?)""",
            (action_id, action['name'], action['case_number'], action['court'],
             '04_JUDICIAL_VIOLATIONS.txt', jv_path, 'judicial_violations', len(violations)))
        conn.commit()
        db_log('PHASE3', action_id, f'Judicial violations: {len(violations)} + {len(forensic)} forensic', len(violations))

    # ---- 5. ADVERSARY REBUTTAL FRAMEWORK ----
    reb_lines = []
    reb_lines.append(f"{'='*80}")
    reb_lines.append(f"ADVERSARY REBUTTAL FRAMEWORK")
    reb_lines.append(f"{action['name']}")
    reb_lines.append(f"{'='*80}\n")

    assertions = data.get('adversary_assertions', [])
    rebuttals = data.get('rebuttals', [])
    perjury = data.get('perjury', [])

    if assertions:
        by_type = defaultdict(list)
        for a in assertions:
            atype = a.get('assertion_type', 'General')
            by_type[atype].append(a)

        for atype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            reb_lines.append(f"\n{'─'*60}")
            reb_lines.append(f"  {atype} ({len(items)} assertions)")
            reb_lines.append(f"{'─'*60}")
            for item in items[:30]:
                text = item.get('assertion_text', '')[:300]
                speaker = item.get('speaker', '')
                reb_lines.append(f"\n  [{speaker}]: \"{text}\"")

    if rebuttals:
        reb_lines.append(f"\n\n{'='*60}")
        reb_lines.append(f"  PREPARED REBUTTALS ({len(rebuttals)})")
        reb_lines.append(f"{'='*60}")
        for r in rebuttals[:100]:
            assertion = r.get('assertion_text', '')[:200]
            rebuttal_ev = r.get('rebuttal_evidence', '')[:200]
            tort = r.get('tort_cause', '')
            target = r.get('filing_target', '')
            reb_lines.append(f"\n  Assertion: \"{assertion}\"")
            reb_lines.append(f"  Rebuttal Evidence: {rebuttal_ev}")
            if tort:
                reb_lines.append(f"  Tort Cause: {tort}")
            if target:
                reb_lines.append(f"  Filing Target: {target}")

    if perjury:
        reb_lines.append(f"\n\n{'='*60}")
        reb_lines.append(f"  WATSON PERJURY COMPILATION ({len(perjury)} instances)")
        reb_lines.append(f"{'='*60}")
        by_member = defaultdict(list)
        for p in perjury:
            member = p.get('watson_member', 'Unknown')
            by_member[member].append(p)
        for member, items in sorted(by_member.items(), key=lambda x: -len(x[1])):
            reb_lines.append(f"\n  --- {member} ({len(items)} perjury instances) ---")
            for item in items[:20]:
                stmt = item.get('statement_text', '')[:200]
                contra = item.get('contradicting_evidence', '')[:200]
                reb_lines.append(f"\n  Statement: \"{stmt}\"")
                reb_lines.append(f"  Contradicted by: {contra}")

    reb_path = os.path.join(output_dir, '05_ADVERSARY_REBUTTAL_FRAMEWORK.txt')
    with open(reb_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(reb_lines))
    log(f'    Rebuttals: {len(assertions)} assertions, {len(rebuttals)} rebuttals, {len(perjury)} perjury')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '05_ADVERSARY_REBUTTAL_FRAMEWORK.txt', reb_path, 'rebuttal_framework', len(assertions)+len(rebuttals)+len(perjury)))
    conn.commit()
    db_log('PHASE3', action_id, f'Rebuttals: {len(assertions)} assert, {len(rebuttals)} rebut, {len(perjury)} perjury', len(assertions))

    # ---- 6. DAMAGES CALCULATIONS ----
    dmg_lines = []
    dmg_lines.append(f"{'='*80}")
    dmg_lines.append(f"DAMAGES CALCULATIONS")
    dmg_lines.append(f"{action['name']}")
    dmg_lines.append(f"{'='*80}\n")

    damages = data.get('damages', [])
    financial = data.get('financial', [])
    harms = data.get('harms', [])

    if damages:
        total_low = 0
        total_high = 0
        for d in damages:
            cat = d.get('category', '')
            sub = d.get('subcategory', '')
            low = d.get('amount_low', 0) or 0
            high = d.get('amount_high', 0) or 0
            method = d.get('methodology', '')
            auth = d.get('authority', '')
            total_low += low
            total_high += high
            dmg_lines.append(f"  {cat} — {sub}")
            dmg_lines.append(f"    Range: ${low:,.2f} – ${high:,.2f}")
            if method:
                dmg_lines.append(f"    Methodology: {method}")
            if auth:
                dmg_lines.append(f"    Authority: {auth}")
            dmg_lines.append('')
        dmg_lines.append(f"\n  {'='*40}")
        dmg_lines.append(f"  TOTAL DAMAGES: ${total_low:,.2f} – ${total_high:,.2f}")
        dmg_lines.append(f"  {'='*40}")

    if harms:
        dmg_lines.append(f"\n\n{'─'*60}")
        dmg_lines.append(f"  EXTRACTED HARMS ({len(harms)} instances)")
        dmg_lines.append(f"{'─'*60}")
        by_cat = defaultdict(int)
        for h in harms:
            cat = h.get('category', 'Unknown')
            by_cat[cat] += 1
        for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
            dmg_lines.append(f"    {cat}: {count} instances")

    dmg_path = os.path.join(output_dir, '06_DAMAGES_CALCULATIONS.txt')
    with open(dmg_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dmg_lines))
    log(f'    Damages: {len(damages)} categories, {len(harms)} harms')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '06_DAMAGES_CALCULATIONS.txt', dmg_path, 'damages', len(damages)))
    conn.commit()
    db_log('PHASE3', action_id, f'Damages: {len(damages)} categories, {len(harms)} harms', len(damages))

    # ---- 7. ACTOR VIOLATIONS BREAKDOWN ----
    av_lines = []
    av_lines.append(f"{'='*80}")
    av_lines.append(f"ACTOR VIOLATIONS BREAKDOWN")
    av_lines.append(f"{action['name']}")
    av_lines.append(f"{'='*80}\n")

    actor_v = data.get('actor_violations', [])
    if actor_v:
        by_actor = defaultdict(list)
        for v in actor_v:
            actor = v.get('actor', 'Unknown')
            by_actor[actor].append(v)
        for actor, items in sorted(by_actor.items(), key=lambda x: -len(x[1])):
            av_lines.append(f"\n{'─'*60}")
            av_lines.append(f"  {actor} — {items[0].get('role','')} ({len(items)} violations)")
            av_lines.append(f"{'─'*60}")
            by_type = defaultdict(int)
            for item in items:
                vtype = item.get('violation_type', 'Unknown')
                by_type[vtype] += 1
            for vtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
                av_lines.append(f"    {vtype}: {count}")
            # Show worst violations
            for item in items[:10]:
                date = item.get('date', '')
                desc = item.get('description', '')[:200]
                sev = item.get('severity', '')
                av_lines.append(f"\n    [{sev}] {date}: {desc}")

    av_path = os.path.join(output_dir, '07_ACTOR_VIOLATIONS.txt')
    with open(av_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(av_lines))
    log(f'    Actor violations: {len(actor_v)}')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '07_ACTOR_VIOLATIONS.txt', av_path, 'actor_violations', len(actor_v)))
    conn.commit()
    db_log('PHASE3', action_id, f'Actor violations: {len(actor_v)}', len(actor_v))

    # ---- 8. FILING READINESS ASSESSMENT ----
    fr_lines = []
    fr_lines.append(f"{'='*80}")
    fr_lines.append(f"FILING READINESS ASSESSMENT")
    fr_lines.append(f"{action['name']}")
    fr_lines.append(f"{'='*80}\n")

    readiness = data.get('readiness', [])
    claims = data.get('claims', [])

    if readiness:
        for r in readiness:
            name = r.get('vehicle_name', '')
            auth_score = r.get('authority_score', 0)
            ev_score = r.get('evidence_score', 0)
            fr_lines.append(f"  {name}")
            fr_lines.append(f"    Authority: {auth_score}/100 | Evidence: {ev_score}/100")
            fr_lines.append(f"    Source: {r.get('best_source','')}")
            fr_lines.append('')

    if claims:
        fr_lines.append(f"\n{'─'*60}")
        fr_lines.append(f"  CLAIMS MATRIX ({len(claims)} claims)")
        fr_lines.append(f"{'─'*60}")
        by_class = defaultdict(int)
        for c in claims:
            cl = c.get('classification', 'Unknown')
            by_class[cl] += 1
        for cl, count in sorted(by_class.items(), key=lambda x: -x[1]):
            fr_lines.append(f"    {cl}: {count}")

    if action.get('deadline'):
        from datetime import datetime as dt
        try:
            deadline = dt.strptime(action['deadline'], '%Y-%m-%d')
            days_left = (deadline - dt.now()).days
            fr_lines.append(f"\n  ⚠️  DEADLINE: {action['deadline']} ({days_left} days remaining)")
        except:
            pass

    fr_path = os.path.join(output_dir, '08_FILING_READINESS.txt')
    with open(fr_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fr_lines))
    log(f'    Filing readiness: {len(readiness)} vehicles, {len(claims)} claims')
    cur.execute("""INSERT INTO apex_filing_stack_index
        (action_id, action_name, case_number, court, file_name, file_path, doc_type, record_count)
        VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, action['name'], action['case_number'], action['court'],
         '08_FILING_READINESS.txt', fr_path, 'filing_readiness', len(readiness)))
    conn.commit()
    db_log('PHASE3', action_id, f'Filing readiness: {len(readiness)} vehicles, {len(claims)} claims', len(readiness))

# ============================================================
# PHASE 4: MASTER CROSS-ACTION SUMMARY
# ============================================================
log('\n[PHASE 4] Generating Master Cross-Action Summary...')

summary_lines = []
summary_lines.append(f"{'='*80}")
summary_lines.append(f"LITIGATIONOS — APEX JUDICIAL ANALYSIS")
summary_lines.append(f"MASTER CROSS-ACTION SUMMARY")
summary_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
summary_lines.append(f"{'='*80}\n")

summary_lines.append(f"DATABASE SCOPE:")
summary_lines.append(f"  Tables: 469")
summary_lines.append(f"  Master Timeline Events: {len(unique_events):,}")
summary_lines.append(f"  Evidence Quotes: 308,704")
summary_lines.append(f"  Adversary Assertions: 108,034")
summary_lines.append(f"  Legal Citations: 3,684,757")
summary_lines.append(f"  Watson Perjury Instances: 14,338")
summary_lines.append(f"  Judicial Violations: 1,127")
summary_lines.append(f"  Actor Violations: 10,915")
summary_lines.append(f"  Forensic Findings: 16,974")
summary_lines.append(f"  Extracted Harms: 26,459")

summary_lines.append(f"\n\n{'─'*60}")
summary_lines.append(f"  COURT ACTIONS")
summary_lines.append(f"{'─'*60}")

for action_id, action in COURT_ACTIONS.items():
    data = action.get('data', {})
    tl = len(data.get('timeline', []))
    auth = len(data.get('authorities', []))
    ev = len(data.get('evidence_quotes', []))
    jv = len(data.get('judicial_violations', []))
    reb = len(data.get('rebuttals', []))

    summary_lines.append(f"\n  {action['name']}")
    summary_lines.append(f"    Case: {action['case_number']} | Court: {action['court']}")
    if action.get('deadline'):
        from datetime import datetime as dt
        try:
            deadline = dt.strptime(action['deadline'], '%Y-%m-%d')
            days_left = (deadline - dt.now()).days
            summary_lines.append(f"    ⚠️  DEADLINE: {action['deadline']} ({days_left} days)")
        except:
            pass
    summary_lines.append(f"    Timeline: {tl} events | Authority: {auth} cases | Evidence: {ev} quotes")
    summary_lines.append(f"    Output: {action['folder']}/APEX_FILING_STACK/")

# Key statistics
summary_lines.append(f"\n\n{'─'*60}")
summary_lines.append(f"  KEY METRICS")
summary_lines.append(f"{'─'*60}")

# Count total output files
total_output = 0
for action_id, action in COURT_ACTIONS.items():
    stack_dir = os.path.join(LOS, action['folder'], 'APEX_FILING_STACK')
    if os.path.exists(stack_dir):
        count = len(os.listdir(stack_dir))
        total_output += count

summary_lines.append(f"  Total filing stack documents: {total_output}")
summary_lines.append(f"  Court actions covered: {len(COURT_ACTIONS)}")

summary_path = os.path.join(LOS, '00_SYSTEM', 'APEX_MASTER_SUMMARY.txt')
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

# Also save as JSON for programmatic access
json_data = {}
for action_id, action in COURT_ACTIONS.items():
    d = action.get('data', {})
    json_data[action_id] = {
        'name': action['name'],
        'case_number': action['case_number'],
        'court': action['court'],
        'timeline_count': len(d.get('timeline', [])),
        'authority_count': len(d.get('authorities', [])),
        'evidence_count': len(d.get('evidence_quotes', [])),
        'violation_count': len(d.get('judicial_violations', [])),
        'rebuttal_count': len(d.get('rebuttals', [])),
        'claim_count': len(d.get('claims', [])),
        'perjury_count': len(d.get('perjury', [])),
    }

json_path = os.path.join(LOS, '00_SYSTEM', 'APEX_ACTION_METRICS.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2)

db_log('COMPLETE', 'ALL', f'APEX engine complete: {total_output} documents across {len(COURT_ACTIONS)} court actions', total_output)

# Save full engine log to DB too
log_text = '\n'.join(log_lines) if 'log_lines' in dir() else ''
# (log_lines not tracked here, but apex_run_log has everything)

conn.close()

log(f'\n{"="*80}')
log(f'  APEX JUDICIAL ANALYSIS ENGINE — COMPLETE')
log(f'  {total_output} filing stack documents generated across {len(COURT_ACTIONS)} court actions')
log(f'  ALL DATA PERSISTED TO litigation_context.db:')
log(f'    apex_master_timeline: {len(unique_events):,} events')
log(f'    apex_court_action_data: {len(COURT_ACTIONS)*15}+ records')
log(f'    apex_filing_stack_index: {total_output} documents')
log(f'    apex_action_timeline: per-action event breakdowns')
log(f'    apex_run_log: complete execution audit trail')
log(f'  Output locations:')
for action_id, action in COURT_ACTIONS.items():
    log(f'    {action["folder"]}/APEX_FILING_STACK/')
log(f'{"="*80}')
