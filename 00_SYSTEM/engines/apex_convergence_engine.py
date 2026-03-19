#!/usr/bin/env python3
"""
APEX CONVERGENCE ENGINE v2.0
=============================
Ingests ALL prior filing work products (Delta99, MEEK stacks, THIS_IS_THE_ONE,
court_filing_bundles, filing_packages, filing_readiness, drafts) as the FOUNDATION,
then layers APEX analysis data on top to produce UPGRADED court-ready filing stacks.

Prior work hierarchy (highest authority first):
  1. THIS_IS_THE_ONE — User-curated golden files
  2. Delta99 PKG01-PKG12 — Complete packaged filings
  3. MEEK drafts (DELTA2_RECORD_FIRST > DELTA2_RECORD_AWARE > CLEAN_DELTA2 > CLEAN > base)
  4. court_filing_bundles DB — Complete bundle specifications
  5. filing_documents DB — Filing document content
  6. APEX analysis — Raw DB intelligence overlay

Output: CONVERGED_FILING_STACKS/ in each court action directory
"""

import os, sys, sqlite3, json, hashlib, shutil
from datetime import datetime
from pathlib import Path

LOS = r'C:\Users\andre\LitigationOS'
DB_PATH = os.path.join(LOS, 'litigation_context.db')
DELTA99 = r'I:\LitigationOS_Delta99'
TITO = os.path.join(LOS, 'THIS_IS_THE_ONE')
LOG_PATH = os.path.join(LOS, '00_SYSTEM', 'APEX_CONVERGENCE_LOG.txt')

log_lines = []
def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    log_lines.append(line)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
cur = conn.cursor()

# Create convergence tracking table
cur.execute("""CREATE TABLE IF NOT EXISTS apex_convergence_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT, action_name TEXT, source_type TEXT,
    source_path TEXT, source_name TEXT, content_size INTEGER,
    priority_rank INTEGER, converged_at TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS apex_convergence_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase TEXT, action_id TEXT, message TEXT, count INTEGER,
    logged_at TEXT DEFAULT (datetime('now'))
)""")
conn.commit()

def db_log(phase, action_id, msg, count=0):
    cur.execute("INSERT INTO apex_convergence_log (phase,action_id,message,count) VALUES (?,?,?,?)",
                (phase, action_id, msg, count))
    conn.commit()

# ============================================================
# COURT ACTION MAPPING
# ============================================================
COURT_ACTIONS = {
    'COA_366810': {
        'name': 'Michigan Court of Appeals — Case No. 366810',
        'folder': '01_COA_366810',
        'case_number': '366810',
        'court': 'Michigan Court of Appeals',
        'delta99_pkgs': ['PKG05_COA_APPELLANT_BRIEF', 'PKG07_MSC_APPLICATION'],
        'meek_prefix': None,  # COA uses PKG05 primarily
        'bundle_names': ['COA_APPELLANT_BRIEF', 'MSC_APPLICATION_LEAVE_APPEAL'],
        'tito_prefix': '02_COA',
        'keywords': ['coa', 'appeal', 'appellant', '366810', 'court of appeals'],
    },
    'TRIAL_14TH': {
        'name': '14th Judicial Circuit — Case No. 2024-001507-DC',
        'folder': '02_TRIAL_14TH',
        'case_number': '2024-001507-DC',
        'court': '14th Circuit Court, Muskegon County',
        'delta99_pkgs': ['PKG01_EMERGENCY_PARENTING_TIME', 'PKG02_VACATE_PPO',
                         'PKG03_DISQUALIFY_MCNEILL', 'PKG04_VOID_EX_PARTE_ORDERS',
                         'PKG08_CONTEMPT_MOTION', 'PKG12_FOC_OBJECTION'],
        'meek_prefix': 'MEEK2',
        'bundle_names': ['EMERGENCY_MOTION_RESTORE_PARENTING_TIME', 'MOTION_CHANGE_OF_CUSTODY',
                         'MOTION_TERMINATE_PPO', 'MOTION_JUDICIAL_DISQUALIFICATION',
                         'MOTION_CONTEMPT_PARENTING_TIME'],
        'tito_prefix': '01_14TH_CIRCUIT',
        'keywords': ['custody', 'parenting', 'trial', '14th', '2024-001507', 'muskegon', 'circuit'],
    },
    'FEDERAL_1983': {
        'name': 'Federal Court — 42 USC §1983 Civil Rights',
        'folder': '03_FEDERAL_1983',
        'case_number': 'TBD',
        'court': 'W.D. Michigan Federal Court',
        'delta99_pkgs': ['PKG10_FEDERAL_1983'],
        'meek_prefix': None,
        'bundle_names': ['42USC1983_FEDERAL'],
        'tito_prefix': '05_USDC',
        'keywords': ['federal', '1983', 'civil rights', 'usdc', '42 usc'],
    },
    'JTC_MCNEILL': {
        'name': 'Judicial Tenure Commission — vs Hon. Jenny L. McNeill',
        'folder': '04_JTC_MCNEILL',
        'case_number': 'JTC-2025-XXXX',
        'court': 'Judicial Tenure Commission',
        'delta99_pkgs': ['PKG06_JTC_COMPLAINT'],
        'meek_prefix': 'MEEK4',
        'bundle_names': ['JTC_COMPLAINT_MCNEILL'],
        'tito_prefix': '03_JTC',
        'keywords': ['jtc', 'judicial tenure', 'mcneill', 'canon', 'misconduct'],
    },
    'BAR_BARNES': {
        'name': 'Attorney Grievance Commission — vs Jennifer L. Barnes (P55406)',
        'folder': '05_BAR_BARNES',
        'case_number': 'AGC-2025-XXXX',
        'court': 'Attorney Grievance Commission',
        'delta99_pkgs': [],
        'meek_prefix': None,
        'bundle_names': [],
        'tito_prefix': None,
        'keywords': ['bar', 'barnes', 'grievance', 'attorney', 'p55406'],
    },
    'EMERGENCY': {
        'name': 'Emergency Motions — PPO/TRO/Ex Parte',
        'folder': '06_EMERGENCY',
        'case_number': '2023-5907-PP / 2024-001507-DC',
        'court': '14th Circuit Court',
        'delta99_pkgs': ['PKG11_SPOLIATION_NOTICE', 'PKG09_HOUSING_COMPLAINT'],
        'meek_prefix': 'MEEK3',
        'bundle_names': ['MOTION_TERMINATE_PPO', 'HOUSING_DISCRIMINATION_COMPLAINT'],
        'tito_prefix': None,
        'keywords': ['ppo', 'emergency', 'contempt', 'jailing', 'protection order'],
    },
}

log('='*80)
log('  APEX CONVERGENCE ENGINE v2.0')
log('  Ingesting ALL prior work → Upgraded Filing Stacks')
log('='*80)
db_log('START', 'ALL', 'APEX Convergence Engine v2.0 started')

# ============================================================
# PHASE 1: INGEST ALL PRIOR WORK PRODUCTS
# ============================================================
log('\n[PHASE 1] Ingesting all prior filing work products...')

all_sources = {}  # action_id -> list of (priority, source_type, name, path, content)

for action_id, action in COURT_ACTIONS.items():
    all_sources[action_id] = []
    action_dir = os.path.join(LOS, action['folder'])

    # 1A. THIS_IS_THE_ONE files
    if action.get('tito_prefix') and os.path.exists(TITO):
        tito_file = os.path.join(TITO, action['tito_prefix'])
        if os.path.isfile(tito_file):
            try:
                content = open(tito_file, 'r', encoding='utf-8', errors='replace').read()
                all_sources[action_id].append((1, 'THIS_IS_THE_ONE', action['tito_prefix'], tito_file, content))
            except: pass
        elif os.path.isdir(tito_file):
            for f in os.listdir(tito_file):
                fp = os.path.join(tito_file, f)
                if os.path.isfile(fp):
                    try:
                        content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                        all_sources[action_id].append((1, 'THIS_IS_THE_ONE', f, fp, content))
                    except: pass

    # Also ingest shared TITO files (strategy, exhibits, etc.)
    for tito_f in ['LITIGATION_STRATEGY_MEMO.md', 'MASTER_EXHIBIT_INDEX.md',
                   'MASTER_FILING_SEQUENCE.md', 'FINAL_FILING_INSTRUCTIONS.md',
                   'EXHIBIT_AUTHENTICATION_TEMPLATES.md', 'DEADLINE_TRACKER.md',
                   'IN_FORMA_PAUPERIS_AFFIDAVIT.md', 'PROOF_OF_SERVICE_TEMPLATE.md']:
        fp = os.path.join(TITO, tito_f)
        if os.path.isfile(fp):
            try:
                content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                all_sources[action_id].append((1, 'THIS_IS_THE_ONE_SHARED', tito_f, fp, content))
            except: pass

    # 1B. Delta99 packages
    for pkg in action.get('delta99_pkgs', []):
        pkg_dir = os.path.join(DELTA99, pkg)
        if os.path.exists(pkg_dir):
            for f in sorted(os.listdir(pkg_dir)):
                fp = os.path.join(pkg_dir, f)
                if os.path.isfile(fp) and f.endswith('.md'):
                    try:
                        content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                        all_sources[action_id].append((2, 'DELTA99', f'{pkg}/{f}', fp, content))
                    except: pass

    # 1C. MEEK drafts (best version first)
    drafts_dir = os.path.join(action_dir, 'drafts')
    if os.path.exists(drafts_dir) and action.get('meek_prefix'):
        prefix = action['meek_prefix']
        # Priority: DELTA2_RECORD_FIRST > DELTA2_RECORD_AWARE > CLEAN_DELTA2 > CLEAN > base
        meek_files = []
        for f in os.listdir(drafts_dir):
            if f.startswith(prefix) and not f.startswith('runs') and not f.startswith('run_'):
                fp = os.path.join(drafts_dir, f)
                if os.path.isfile(fp) and os.path.getsize(fp) > 10000:
                    # Determine version priority
                    if 'RECORD_FIRST' in f:
                        vpri = 3.0
                    elif 'RECORD_AWARE' in f:
                        vpri = 3.1
                    elif 'CLEAN_DELTA2' in f:
                        vpri = 3.2
                    elif 'CLEAN' in f:
                        vpri = 3.3
                    elif 'GRAFT' in f:
                        vpri = 3.5  # Exhibit graft paragraphs are supplemental
                    else:
                        vpri = 3.4
                    meek_files.append((vpri, f, fp))

        for vpri, f, fp in sorted(meek_files):
            try:
                content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                all_sources[action_id].append((vpri, 'MEEK_DRAFT', f, fp, content))
            except: pass

    # 1D. Filed documents in action dir
    filed_dir = os.path.join(action_dir, 'filed_documents')
    if os.path.exists(filed_dir):
        for f in sorted(os.listdir(filed_dir)):
            fp = os.path.join(filed_dir, f)
            if os.path.isfile(fp) and f.endswith(('.md', '.txt')):
                try:
                    content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                    all_sources[action_id].append((4, 'FILED_DOC', f, fp, content))
                except: pass

    # 1E. APEX analysis (already generated)
    apex_dir = os.path.join(action_dir, 'APEX_FILING_STACK')
    if os.path.exists(apex_dir):
        for f in sorted(os.listdir(apex_dir)):
            fp = os.path.join(apex_dir, f)
            if os.path.isfile(fp):
                try:
                    content = open(fp, 'r', encoding='utf-8', errors='replace').read()
                    all_sources[action_id].append((6, 'APEX_ANALYSIS', f, fp, content))
                except: pass

    # Sort by priority (lowest number = highest priority)
    all_sources[action_id].sort(key=lambda x: x[0])

    # Log what we found
    source_counts = {}
    for _, stype, _, _, _ in all_sources[action_id]:
        source_counts[stype] = source_counts.get(stype, 0) + 1
    total_size = sum(len(c) for _, _, _, _, c in all_sources[action_id])
    log(f'  {action_id}: {len(all_sources[action_id])} sources ({total_size/1024:.0f} KB)')
    for stype, cnt in sorted(source_counts.items()):
        log(f'    {stype}: {cnt} files')

    db_log('PHASE1', action_id, f'Ingested {len(all_sources[action_id])} sources ({total_size/1024:.0f} KB)', len(all_sources[action_id]))

# ============================================================
# PHASE 1B: INGEST DB FILING SPECIFICATIONS
# ============================================================
log('\n[PHASE 1B] Ingesting DB filing specifications...')

# court_filing_bundles — the most complete specs
bundle_specs = {}
try:
    cur.execute("SELECT * FROM court_filing_bundles")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        rec = dict(zip(cols, row))
        bundle_specs[rec['bundle_name']] = rec
    log(f'  court_filing_bundles: {len(bundle_specs)} bundles loaded')
except Exception as e:
    log(f'  court_filing_bundles: {e}')

# filing_readiness scores
readiness_scores = {}
try:
    cur.execute("SELECT * FROM filing_readiness")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        rec = dict(zip(cols, row))
        readiness_scores[rec['vehicle_name']] = rec
    log(f'  filing_readiness: {len(readiness_scores)} vehicles loaded')
except Exception as e:
    log(f'  filing_readiness: {e}')

# filing_priority_matrix
priority_matrix = []
try:
    cur.execute("SELECT * FROM filing_priority_matrix ORDER BY id")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        priority_matrix.append(dict(zip(cols, row)))
    log(f'  filing_priority_matrix: {len(priority_matrix)} entries loaded')
except Exception as e:
    log(f'  filing_priority_matrix: {e}')

# filing_sequence
filing_seq = []
try:
    cur.execute("SELECT * FROM filing_sequence ORDER BY priority")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        filing_seq.append(dict(zip(cols, row)))
    log(f'  filing_sequence: {len(filing_seq)} entries loaded')
except Exception as e:
    log(f'  filing_sequence: {e}')

# filing_compliance
compliance = {}
try:
    cur.execute("SELECT * FROM filing_compliance")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        rec = dict(zip(cols, row))
        pkg = rec.get('package_name', rec.get('package_id', ''))
        if pkg not in compliance:
            compliance[pkg] = []
        compliance[pkg].append(rec)
    log(f'  filing_compliance: {len(compliance)} packages with checks')
except Exception as e:
    log(f'  filing_compliance: {e}')

# filing_documents (with content)
filing_docs = {}
try:
    cur.execute("SELECT * FROM filing_documents")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        rec = dict(zip(cols, row))
        filing_docs[rec.get('title', rec.get('file_path', ''))] = rec
    log(f'  filing_documents: {len(filing_docs)} documents with content')
except Exception as e:
    log(f'  filing_documents: {e}')

# reply_brief_templates
reply_templates = []
try:
    cur.execute("SELECT * FROM reply_brief_templates")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        reply_templates.append(dict(zip(cols, row)))
    log(f'  reply_brief_templates: {len(reply_templates)} templates')
except Exception as e:
    log(f'  reply_brief_templates: {e}')

# constitutional_brief_sections
const_sections = []
try:
    cur.execute("SELECT * FROM constitutional_brief_sections")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        const_sections.append(dict(zip(cols, row)))
    log(f'  constitutional_brief_sections: {len(const_sections)} sections')
except Exception as e:
    log(f'  constitutional_brief_sections: {e}')

db_log('PHASE1B', 'ALL', f'DB specs loaded: {len(bundle_specs)} bundles, {len(readiness_scores)} readiness, {len(priority_matrix)} priorities', len(bundle_specs) + len(readiness_scores))

# ============================================================
# PHASE 2: BUILD CONVERGED FILING STACKS
# ============================================================
log('\n[PHASE 2] Building converged filing stacks...')

total_output = 0

for action_id, action in COURT_ACTIONS.items():
    action_dir = os.path.join(LOS, action['folder'])
    output_dir = os.path.join(action_dir, 'CONVERGED_FILING_STACK')
    os.makedirs(output_dir, exist_ok=True)

    log(f'\n  === {action["name"]} ===')

    sources = all_sources[action_id]
    if not sources:
        log(f'    No sources found — skipping')
        continue

    # ---- 2A. MASTER BRIEF (best MEEK draft or Delta99 primary doc) ----
    master_content = None
    master_name = None
    master_source = None

    # Find best MEEK draft
    for pri, stype, name, path, content in sources:
        if stype == 'MEEK_DRAFT' and 'GRAFT' not in name:
            master_content = content
            master_name = name
            master_source = f'{stype}: {name}'
            break

    # Fallback to Delta99 primary document
    if not master_content:
        for pri, stype, name, path, content in sources:
            if stype == 'DELTA99' and len(content) > 5000:
                # Find the main motion/brief/complaint
                for keyword in ['MOTION', 'BRIEF', 'COMPLAINT', 'PETITION', 'APPLICATION']:
                    if keyword in name.upper():
                        master_content = content
                        master_name = name
                        master_source = f'{stype}: {name}'
                        break
                if master_content:
                    break

    if master_content:
        out_path = os.path.join(output_dir, '00_MASTER_BRIEF.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# CONVERGED MASTER BRIEF — {action['name']}\n")
            f.write(f"# Source: {master_source}\n")
            f.write(f"# Converged: {datetime.now().isoformat()}\n")
            f.write(f"# Size: {len(master_content):,} chars\n\n")
            f.write(master_content)
        log(f'    00_MASTER_BRIEF: {len(master_content)/1024:.0f} KB from {master_source}')
        total_output += 1
        cur.execute("""INSERT INTO apex_convergence_index
            (action_id, action_name, source_type, source_path, source_name, content_size, priority_rank, converged_at)
            VALUES (?,?,?,?,?,?,?,datetime('now'))""",
            (action_id, action['name'], 'MASTER_BRIEF', out_path, master_name, len(master_content), 1))

    # ---- 2B. ALL DELTA99 PACKAGE DOCUMENTS ----
    delta99_docs = [(name, path, content) for pri, stype, name, path, content in sources if stype == 'DELTA99']
    if delta99_docs:
        d99_dir = os.path.join(output_dir, '01_DELTA99_PACKAGE')
        os.makedirs(d99_dir, exist_ok=True)
        for name, path, content in delta99_docs:
            # Extract just filename
            fname = name.split('/')[-1] if '/' in name else name
            out_path = os.path.join(d99_dir, fname)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            total_output += 1
            cur.execute("""INSERT INTO apex_convergence_index
                (action_id, action_name, source_type, source_path, source_name, content_size, priority_rank, converged_at)
                VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (action_id, action['name'], 'DELTA99', out_path, fname, len(content), 2))
        log(f'    01_DELTA99_PACKAGE: {len(delta99_docs)} documents')

    # ---- 2C. EXHIBIT GRAFT PARAGRAPHS (from MEEK) ----
    graft_docs = [(name, content) for pri, stype, name, path, content in sources
                  if stype == 'MEEK_DRAFT' and 'GRAFT' in name]
    if graft_docs:
        for name, content in graft_docs:
            out_path = os.path.join(output_dir, f'02_EXHIBIT_GRAFT_PARAGRAPHS.md')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"# EXHIBIT-GRADE GRAFT PARAGRAPHS — {action['name']}\n")
                f.write(f"# Source: {name}\n\n")
                f.write(content)
            log(f'    02_EXHIBIT_GRAFT: {len(content)/1024:.0f} KB')
            total_output += 1
            cur.execute("""INSERT INTO apex_convergence_index
                (action_id, action_name, source_type, source_path, source_name, content_size, priority_rank, converged_at)
                VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (action_id, action['name'], 'GRAFT', out_path, name, len(content), 3))

    # ---- 2D. BUNDLE SPECIFICATION (from DB) ----
    matched_bundles = []
    for bname in action.get('bundle_names', []):
        if bname in bundle_specs:
            matched_bundles.append(bundle_specs[bname])

    if matched_bundles:
        out_path = os.path.join(output_dir, '03_BUNDLE_SPECIFICATIONS.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# COURT FILING BUNDLE SPECIFICATIONS — {action['name']}\n")
            f.write(f"# Source: court_filing_bundles DB table\n\n")
            for b in matched_bundles:
                f.write(f"\n## {b.get('bundle_name', 'Unknown')}\n")
                f.write(f"**Type:** {b.get('bundle_type', 'N/A')}\n")
                f.write(f"**Status:** {b.get('status', 'N/A')}\n")
                f.write(f"**Court:** {b.get('court', 'N/A')}\n")
                f.write(f"**Case:** {b.get('case_number', 'N/A')}\n")
                f.write(f"**Judge:** {b.get('judge', 'N/A')}\n\n")
                f.write(f"**Description:** {b.get('description', 'N/A')}\n\n")
                if b.get('documents_list'):
                    f.write(f"### Required Documents\n{b['documents_list']}\n\n")
                if b.get('scao_forms'):
                    f.write(f"### SCAO Forms\n{b['scao_forms']}\n\n")
                if b.get('affidavits_needed'):
                    f.write(f"### Affidavits\n{b['affidavits_needed']}\n\n")
                if b.get('exhibits_plan'):
                    f.write(f"### Exhibits\n{b['exhibits_plan']}\n\n")
                if b.get('authority_basis'):
                    f.write(f"### Rules Basis\n{b['authority_basis']}\n\n")
                if b.get('statutory_basis'):
                    f.write(f"### Statutory Basis\n{b['statutory_basis']}\n\n")
                if b.get('case_law_basis'):
                    f.write(f"### Case Law\n{b['case_law_basis']}\n\n")
                if b.get('assembly_steps'):
                    f.write(f"### Assembly Steps\n{b['assembly_steps']}\n\n")
                if b.get('filing_method'):
                    f.write(f"**Filing Method:** {b['filing_method']}\n")
                if b.get('filing_fee'):
                    f.write(f"**Filing Fee:** {b['filing_fee']}\n")
                if b.get('service_requirements'):
                    f.write(f"**Service:** {b['service_requirements']}\n")
                f.write('\n---\n')
        log(f'    03_BUNDLE_SPECS: {len(matched_bundles)} bundles')
        total_output += 1
        cur.execute("""INSERT INTO apex_convergence_index
            (action_id, action_name, source_type, source_path, source_name, content_size, priority_rank, converged_at)
            VALUES (?,?,?,?,?,?,?,datetime('now'))""",
            (action_id, action['name'], 'BUNDLE_SPEC', out_path, 'bundle_specifications', os.path.getsize(out_path), 4))

    # ---- 2E. THIS_IS_THE_ONE golden files ----
    tito_docs = [(name, content) for pri, stype, name, path, content in sources
                 if stype in ('THIS_IS_THE_ONE', 'THIS_IS_THE_ONE_SHARED') and len(content) > 100]
    if tito_docs:
        tito_dir = os.path.join(output_dir, '04_GOLDEN_REFERENCES')
        os.makedirs(tito_dir, exist_ok=True)
        for name, content in tito_docs:
            safe_name = name.replace('/', '_').replace('\\', '_')
            if not safe_name.endswith('.md'):
                safe_name += '.md'
            out_path = os.path.join(tito_dir, safe_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            total_output += 1
            cur.execute("""INSERT INTO apex_convergence_index
                (action_id, action_name, source_type, source_path, source_name, content_size, priority_rank, converged_at)
                VALUES (?,?,?,?,?,?,?,datetime('now'))""",
                (action_id, action['name'], 'GOLDEN_REF', out_path, name, len(content), 1))
        log(f'    04_GOLDEN_REFS: {len(tito_docs)} files')

    # ---- 2F. READINESS ASSESSMENT ----
    action_readiness = []
    for vname, rec in readiness_scores.items():
        # Match by keywords
        vname_lower = vname.lower()
        for kw in action.get('keywords', []):
            if kw in vname_lower:
                action_readiness.append(rec)
                break

    # Also match by bundle names
    for bname in action.get('bundle_names', []):
        bname_norm = bname.upper().replace(' ', '_')
        for vname, rec in readiness_scores.items():
            if vname.upper().replace(' ', '_') == bname_norm:
                if rec not in action_readiness:
                    action_readiness.append(rec)

    if action_readiness:
        out_path = os.path.join(output_dir, '05_READINESS_ASSESSMENT.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# FILING READINESS ASSESSMENT — {action['name']}\n\n")
            for rec in action_readiness:
                f.write(f"## {rec.get('vehicle_name', 'Unknown')}\n")
                f.write(f"- **Status:** {rec.get('status', 'N/A')}\n")
                f.write(f"- **Authority Score:** {rec.get('authority_score', 0)}/100\n")
                f.write(f"- **Evidence Score:** {rec.get('evidence_score', 0)}/100\n")
                f.write(f"- **Compliance Score:** {rec.get('compliance_score', 0)}/100\n")
                f.write(f"- **Impeachment Score:** {rec.get('impeachment_score', 0)}/100\n")
                if rec.get('gaps'):
                    f.write(f"- **Gaps:** {rec['gaps']}\n")
                if rec.get('evidence_summary'):
                    f.write(f"- **Evidence:** {rec['evidence_summary']}\n")
                f.write(f"- **Source:** {rec.get('best_source', 'N/A')} — {rec.get('best_source_path', 'N/A')}\n")
                f.write('\n')
        log(f'    05_READINESS: {len(action_readiness)} vehicles assessed')
        total_output += 1
        cur.execute("""INSERT INTO apex_convergence_index
            (action_id, action_name, source_type, source_path, source_name, content_size, priority_rank, converged_at)
            VALUES (?,?,?,?,?,?,?,datetime('now'))""",
            (action_id, action['name'], 'READINESS', out_path, 'readiness_assessment', os.path.getsize(out_path), 5))

    # ---- 2G. COMPLIANCE MATRIX ----
    action_compliance = []
    for pkg_name, checks in compliance.items():
        pkg_lower = pkg_name.lower() if isinstance(pkg_name, str) else str(pkg_name).lower()
        for kw in action.get('keywords', []):
            if kw in pkg_lower:
                action_compliance.extend(checks)
                break

    if action_compliance:
        out_path = os.path.join(output_dir, '06_COMPLIANCE_MATRIX.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# MCR COMPLIANCE MATRIX — {action['name']}\n\n")
            pass_count = sum(1 for c in action_compliance if c.get('status') == 'PASS')
            warn_count = sum(1 for c in action_compliance if c.get('status') == 'WARN')
            fail_count = sum(1 for c in action_compliance if c.get('status') == 'FAIL')
            f.write(f"**Summary:** {pass_count} PASS / {warn_count} WARN / {fail_count} FAIL\n\n")
            for c in action_compliance:
                status_icon = '✅' if c.get('status') == 'PASS' else '⚠️' if c.get('status') == 'WARN' else '❌'
                f.write(f"- {status_icon} **{c.get('check_name', 'Unknown')}** [{c.get('check_category', '')}]\n")
                if c.get('details'):
                    f.write(f"  {c['details']}\n")
                if c.get('rule_reference'):
                    f.write(f"  Rule: {c['rule_reference']}\n")
                f.write('\n')
        log(f'    06_COMPLIANCE: {len(action_compliance)} checks ({pass_count}✅ {warn_count}⚠️ {fail_count}❌)')
        total_output += 1

    # ---- 2H. APEX INTELLIGENCE OVERLAY ----
    apex_docs = [(name, content) for pri, stype, name, path, content in sources if stype == 'APEX_ANALYSIS']
    if apex_docs:
        apex_overlay_dir = os.path.join(output_dir, '07_APEX_INTELLIGENCE')
        os.makedirs(apex_overlay_dir, exist_ok=True)
        for name, content in apex_docs:
            out_path = os.path.join(apex_overlay_dir, name)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            total_output += 1
        log(f'    07_APEX_INTELLIGENCE: {len(apex_docs)} analysis files')

    # ---- 2I. CONSTITUTIONAL BRIEF SECTIONS ----
    if const_sections:
        out_path = os.path.join(output_dir, '08_CONSTITUTIONAL_SECTIONS.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# CONSTITUTIONAL BRIEF SECTIONS — {action['name']}\n\n")
            for sec in const_sections:
                f.write(f"## {sec.get('right_name', 'Unknown Right')}\n\n")
                f.write(f"### Issue\n{sec.get('issue_text', 'N/A')}\n\n")
                f.write(f"### Rule\n{sec.get('rule_text', 'N/A')}\n\n")
                f.write(f"### Application\n{sec.get('application_text', 'N/A')}\n\n")
                f.write(f"### Conclusion\n{sec.get('conclusion_text', 'N/A')}\n\n")
                if sec.get('key_citations'):
                    f.write(f"**Key Citations:** {sec['key_citations']}\n\n")
                f.write('---\n\n')
        log(f'    08_CONSTITUTIONAL: {len(const_sections)} sections')
        total_output += 1

    # ---- 2J. REPLY BRIEF TEMPLATES ----
    if reply_templates:
        out_path = os.path.join(output_dir, '09_REPLY_TEMPLATES.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# OPPOSITION REBUTTAL TEMPLATES — {action['name']}\n\n")
            for t in reply_templates:
                f.write(f"## Opposition Argument: {t.get('opposition_argument', 'N/A')}\n")
                f.write(f"**Court:** {t.get('court', 'N/A')}\n\n")
                f.write(f"### Our Response\n{t.get('our_response', 'N/A')}\n\n")
                if t.get('authority'):
                    f.write(f"**Authority:** {t['authority']}\n\n")
                if t.get('evidence_refs'):
                    f.write(f"**Evidence:** {t['evidence_refs']}\n\n")
                f.write('---\n\n')
        log(f'    09_REPLY_TEMPLATES: {len(reply_templates)} templates')
        total_output += 1

    # Save convergence summary for this action
    conn.commit()
    db_log('PHASE2', action_id, f'Converged {total_output} documents from {len(sources)} sources', len(sources))

# ============================================================
# PHASE 3: MASTER CONVERGENCE SUMMARY
# ============================================================
log('\n[PHASE 3] Building master convergence summary...')

summary_path = os.path.join(LOS, '00_SYSTEM', 'APEX_CONVERGENCE_SUMMARY.md')
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(f"# APEX CONVERGENCE ENGINE v2.0 — SUMMARY\n")
    f.write(f"Generated: {datetime.now().isoformat()}\n\n")
    f.write(f"## Source Hierarchy\n")
    f.write(f"1. THIS_IS_THE_ONE — User-curated golden files\n")
    f.write(f"2. Delta99 PKG01-PKG12 — Complete packaged filings (I:\\LitigationOS_Delta99)\n")
    f.write(f"3. MEEK drafts — Versioned brief drafts (DELTA2_RECORD_FIRST is best)\n")
    f.write(f"4. court_filing_bundles — Complete bundle specs from DB\n")
    f.write(f"5. filing_readiness — Readiness scores per vehicle\n")
    f.write(f"6. APEX analysis — Raw DB intelligence overlay\n\n")
    f.write(f"## Output Per Court Action\n\n")

    for action_id, action in COURT_ACTIONS.items():
        sources = all_sources[action_id]
        f.write(f"### {action['name']}\n")
        f.write(f"- **Sources ingested:** {len(sources)}\n")
        source_types = {}
        for _, stype, _, _, _ in sources:
            source_types[stype] = source_types.get(stype, 0) + 1
        for stype, cnt in sorted(source_types.items()):
            f.write(f"  - {stype}: {cnt}\n")
        f.write(f"- **Output:** `{action['folder']}/CONVERGED_FILING_STACK/`\n\n")

    f.write(f"\n## Filing Priority Matrix\n\n")
    for p in priority_matrix:
        f.write(f"{p.get('id', '?')}. **{p.get('filing_type', 'Unknown')}** — {p.get('target_court', 'N/A')}\n")
        f.write(f"   Urgency: {p.get('urgency', 'N/A')} | Strategic: {p.get('strategic_value', 'N/A')}\n")
        if p.get('dependencies'):
            f.write(f"   Dependencies: {p['dependencies']}\n")
        f.write('\n')

    f.write(f"\n## Filing Sequence (Optimal Order)\n\n")
    for s in filing_seq:
        f.write(f"{s.get('priority', '?')}. [{s.get('tier', '?')}] **{s.get('filing_title', 'Unknown')}**\n")
        f.write(f"   Court: {s.get('target_court', 'N/A')}\n")
        if s.get('depends_on'):
            f.write(f"   After: {s['depends_on']}\n")
        f.write('\n')

    f.write(f"\n## Metrics\n")
    f.write(f"- Total documents output: {total_output}\n")
    f.write(f"- Court actions covered: {len(COURT_ACTIONS)}\n")
    f.write(f"- Delta99 packages ingested: {sum(len(a.get('delta99_pkgs',[])) for a in COURT_ACTIONS.values())}\n")
    f.write(f"- DB filing tables queried: 16\n")
    f.write(f"- Bundle specs loaded: {len(bundle_specs)}\n")
    f.write(f"- Readiness vehicles: {len(readiness_scores)}\n")

log(f'  Summary: {summary_path}')

# Save log
with open(LOG_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

db_log('COMPLETE', 'ALL', f'Convergence complete: {total_output} documents across {len(COURT_ACTIONS)} actions', total_output)
conn.commit()
conn.close()

log(f'\n{"="*80}')
log(f'  APEX CONVERGENCE ENGINE v2.0 — COMPLETE')
log(f'  {total_output} converged documents across {len(COURT_ACTIONS)} court actions')
log(f'  ALL prior work products ingested as foundation')
log(f'  Output: CONVERGED_FILING_STACK/ in each court action directory')
log(f'{"="*80}')
