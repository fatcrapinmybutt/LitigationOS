"""
LitigationOS Smart Functional Router v1.0
Analyzes filenames and routes to correct canonical folder.
Priority-ordered: Evidence > Court > Filings > Analysis > Authority > Code > Data > Media > Reference > Archive
"""
import os, sys, shutil, re, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\Users\andre\LitigationOS")

# === ROUTING RULES (priority-ordered) ===

EVIDENCE_PATTERNS = re.compile(r"""
    (?:evidence|exhibit|police|NSPD|NS\d{7}|witness|testimony|
    statement|appclose|forensic|affidavit|ppo[_\s]?evid|
    body[_\s]?camera|allegation|recant|drug[_\s]?screen|
    parenting[_\s]?time[_\s]?violation|custody[_\s]?evidence|
    alienation[_\s]?evidence|false[_\s]?allegation|
    SHADYOAKS|shady[_\s]?oaks|sewage|mold|habitab|
    lease[_\s]?viol|housing[_\s]?viol|eviction|
    demand[_\s]?for[_\s]?possession|
    AppClose|noreply|NoReply)
""", re.IGNORECASE | re.VERBOSE)

EVIDENCE_PHOTO_PATTERNS = re.compile(r"""
    ^file-[A-Za-z0-9]{10,}|
    ^20\d{6}_\d{6}\.jpg|
    (?:sewage|mold|damage|photo|scan|conv\s?\d)
""", re.IGNORECASE | re.VERBOSE)

COURT_PATTERNS = re.compile(r"""
    (?:court[_\s]?order|judgment|disposition|docket[_\s]?entry|
    transcript|hearing[_\s]?transcript|ruling|
    ex[_\s]?parte[_\s]?order|custody[_\s]?order|
    PPO[_\s]?order|PPO[_\s]?(?:docket|petition)|
    people[_\s]?v[_\s]?pigors|
    FOC[_\s]?(?:report|recommendation|order)|
    friend[_\s]?of[_\s]?court|
    bench[_\s]?warrant|arraign|sentenc)
""", re.IGNORECASE | re.VERBOSE)

FILING_PATTERNS = re.compile(r"""
    (?:motion[_\s]?(?:to|for)|brief[_\s]?(?:in|on)|
    complaint|petition|
    certificate[_\s]?of[_\s]?service|
    proposed[_\s]?order|
    emergency[_\s]?motion|
    disqualification|
    custody[_\s]?modification|
    ppo[_\s]?termination|
    MSC[_\s]?(?:original|application|complaint)|
    JTC[_\s]?(?:complaint|packet)|
    COA[_\s]?(?:brief|emergency)|
    appellant[_\s]?brief|
    IRAC|statement[_\s]?of[_\s]?facts|
    relief[_\s]?requested|
    proof[_\s]?of[_\s]?service|
    cover[_\s]?sheet|
    verified[_\s]?complaint|
    amended[_\s]?complaint|
    filing[_\s]?package|court[_\s]?ready|
    F0[1-9]|F10|PKG_F)
""", re.IGNORECASE | re.VERBOSE)

ANALYSIS_PATTERNS = re.compile(r"""
    (?:analysis|_report|timeline|impeach|
    contradiction|adversary|judicial[_\s]?(?:bias|violation|pattern|misconduct)|
    damages[_\s]?calc|best[_\s]?interest|
    red[_\s]?team|assessment|audit|
    strategy|compilation|intelligence|
    narrative|scoring|gap[_\s]?analysis|
    violation[_\s]?(?:pattern|compilation|matrix)|
    credibility|pattern[_\s]?mining|
    convergence|omega[_\s]?(?:deep|judicial|key|evidence)|
    wave\d{1,2}|cross[_\s]?filing|
    rebuttal|weapon|conspiracy|
    McNeill|Berry|Barnes)
""", re.IGNORECASE | re.VERBOSE)

AUTHORITY_PATTERNS = re.compile(r"""
    (?:^MCR[_\s]|^MCL[_\s]|^MRE[_\s]|
    court[_\s]?rule|statute|
    benchbook|canon|SCAO|
    legal[_\s]?reference|
    michigan[_\s]?(?:court|law|rule|compiled)|
    residential[_\s]?landlord|
    sexual[_\s]?assault[_\s]?benchbook|
    court[_\s]?form|form[_\s]?(?:MC|FOC|CC|DC)|
    Benchbook|authority[_\s]?(?:chain|index|anchor|validation))
""", re.IGNORECASE | re.VERBOSE)

CODE_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.bat', '.ps1', '.sh', '.spec', '.cmake', '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.java'}
DATA_EXTENSIONS = {'.db', '.sqlite', '.csv', '.jsonl', '.json', '.xlsx', '.xml', '.yml', '.yaml', '.toml', '.sql', '.cfg', '.ini', '.conf'}
MEDIA_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.bmp', '.tiff', '.mp4', '.wav', '.mp3', '.avi'}
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.pyc', '.pyo', '.traineddata', '.zdct', '.sav'}
DOC_EXTENSIONS = {'.html', '.htm', '.rst', '.odt'}

def route_file(filepath):
    """Determine the canonical destination for a file. Returns (target_folder, reason)."""
    name = filepath.name
    ext = filepath.suffix.lower()
    name_lower = name.lower()
    
    # === PRIORITY 1: Evidence ===
    if EVIDENCE_PATTERNS.search(name):
        # Sub-route within evidence
        if any(k in name_lower for k in ['shady', 'housing', 'lease', 'evict', 'sewage', 'mold', 'habitab', 'demand_for_possession']):
            return "01_EVIDENCE/HOUSING", "housing evidence"
        if any(k in name_lower for k in ['police', 'nspd', 'ns20', 'body_camera']):
            return "01_EVIDENCE/POLICE", "police report"
        if any(k in name_lower for k in ['ppo']):
            return "01_EVIDENCE/PPO", "PPO evidence"
        if any(k in name_lower for k in ['exhibit', 'bates']):
            return "01_EVIDENCE/EXHIBITS", "exhibit"
        if any(k in name_lower for k in ['appclose', 'noreply', 'correspondence', 'email', 'letter']):
            return "01_EVIDENCE/CORRESPONDENCE", "correspondence"
        if any(k in name_lower for k in ['forensic', 'metadata', 'hash']):
            return "01_EVIDENCE/FORENSIC", "forensic"
        if ext in MEDIA_EXTENSIONS:
            return "01_EVIDENCE/PHOTOS", "evidence photo"
        return "01_EVIDENCE/CUSTODY", "custody evidence"
    
    # Evidence photos by naming pattern
    if EVIDENCE_PHOTO_PATTERNS.search(name):
        return "01_EVIDENCE/PHOTOS", "evidence photo pattern"
    
    # === PRIORITY 2: Court records ===
    if COURT_PATTERNS.search(name):
        if any(k in name_lower for k in ['judgment', 'disposition']):
            return "03_COURT/JUDGMENTS", "judgment"
        if any(k in name_lower for k in ['transcript', 'hearing']):
            return "03_COURT/TRANSCRIPTS", "transcript"
        if any(k in name_lower for k in ['docket']):
            return "03_COURT/DOCKET", "docket"
        if any(k in name_lower for k in ['ppo']):
            return "03_COURT/PPO", "PPO order"
        if any(k in name_lower for k in ['criminal', 'people_v', 'arraign', 'sentenc']):
            return "03_COURT/CRIMINAL", "criminal"
        if any(k in name_lower for k in ['foc', 'friend_of_court']):
            return "03_COURT/FOC", "FOC"
        return "03_COURT/ORDERS", "court order"
    
    # === PRIORITY 3: Filings ===
    if FILING_PATTERNS.search(name):
        if any(k in name_lower for k in ['f01', 'emergency_tro', 'tro']):
            return "05_FILINGS/F01_EMERGENCY_TRO", "F01"
        if any(k in name_lower for k in ['f02', 'shady_oaks_complaint']):
            return "05_FILINGS/F02_SHADY_OAKS", "F02"
        if any(k in name_lower for k in ['f03', 'disqualif']):
            return "05_FILINGS/F03_DISQUALIFICATION", "F03"
        if any(k in name_lower for k in ['f04', '1983', 'federal_complaint']):
            return "05_FILINGS/F04_FEDERAL_1983", "F04"
        if any(k in name_lower for k in ['f05', 'msc_original', 'superintend']):
            return "05_FILINGS/F05_MSC_ORIGINAL", "F05"
        if any(k in name_lower for k in ['f06', 'jtc']):
            return "05_FILINGS/F06_JTC_COMPLAINT", "F06"
        if any(k in name_lower for k in ['f07', 'custody_mod']):
            return "05_FILINGS/F07_CUSTODY_MOD", "F07"
        if any(k in name_lower for k in ['f08', 'ppo_termin']):
            return "05_FILINGS/F08_PPO_TERMINATION", "F08"
        if any(k in name_lower for k in ['f09', 'coa_brief', 'appellant_brief']):
            return "05_FILINGS/F09_COA_BRIEF", "F09"
        if any(k in name_lower for k in ['f10', 'coa_emergency']):
            return "05_FILINGS/F10_COA_EMERGENCY", "F10"
        if any(k in name_lower for k in ['court_ready', 'ready_to_file']):
            return "05_FILINGS/COURT_READY", "court ready"
        if any(k in name_lower for k in ['template']):
            return "05_FILINGS/TEMPLATES", "template"
        return "05_FILINGS/DRAFTS", "filing draft"
    
    # === PRIORITY 4: Analysis ===
    if ANALYSIS_PATTERNS.search(name):
        if any(k in name_lower for k in ['timeline', 'chronolog']):
            return "04_ANALYSIS/TIMELINES", "timeline"
        if any(k in name_lower for k in ['impeach', 'cross_exam']):
            return "04_ANALYSIS/IMPEACHMENT", "impeachment"
        if any(k in name_lower for k in ['contradiction']):
            return "04_ANALYSIS/CONTRADICTIONS", "contradiction"
        if any(k in name_lower for k in ['adversary', 'watson_', 'barnes', 'opposing']):
            return "04_ANALYSIS/ADVERSARY", "adversary intel"
        if any(k in name_lower for k in ['judicial', 'mcneill', 'berry', 'bias', 'canon_viol']):
            return "04_ANALYSIS/JUDICIAL", "judicial analysis"
        if any(k in name_lower for k in ['damage', 'compensation']):
            return "04_ANALYSIS/DAMAGES", "damages"
        if any(k in name_lower for k in ['best_interest', 'bif_', 'factor_']):
            return "04_ANALYSIS/BEST_INTEREST", "best interest"
        if any(k in name_lower for k in ['red_team', 'vulnerab']):
            return "04_ANALYSIS/RED_TEAM", "red team"
        if re.search(r'wave\d', name_lower):
            return "04_ANALYSIS/WAVES", "wave analysis"
        return "04_ANALYSIS", "analysis"
    
    # === PRIORITY 5: Authority ===
    if AUTHORITY_PATTERNS.search(name):
        if any(k in name_lower for k in ['benchbook']):
            return "02_AUTHORITY/BENCHBOOKS", "benchbook"
        if any(k in name_lower for k in ['mcr ', 'mcr_', 'court_rule']):
            return "02_AUTHORITY/MCR", "MCR"
        if any(k in name_lower for k in ['mcl ', 'mcl_', 'compiled_law']):
            return "02_AUTHORITY/MCL", "MCL"
        if any(k in name_lower for k in ['mre ', 'mre_']):
            return "02_AUTHORITY/MRE", "MRE"
        if any(k in name_lower for k in ['form', 'scao']):
            return "02_AUTHORITY/FORMS", "form"
        if any(k in name_lower for k in ['canon']):
            return "02_AUTHORITY/CANONS", "canon"
        if any(k in name_lower for k in ['authority']):
            return "02_AUTHORITY/CASE_LAW", "authority"
        return "02_AUTHORITY", "authority"
    
    # === PRIORITY 6: Extension-based routing (lower priority) ===
    if ext in CODE_EXTENSIONS:
        return "07_CODE", "code file"
    
    if ext in ARCHIVE_EXTENSIONS:
        return "11_ARCHIVES", "archive"
    
    if ext in MEDIA_EXTENSIONS:
        return "08_MEDIA", "media file"
    
    if ext in {'.db', '.sqlite'}:
        return "06_DATA", "database"
    
    if ext in {'.csv', '.jsonl', '.xlsx'}:
        return "06_DATA", "structured data"
    
    if ext == '.json':
        # JSON could be data or config - check name
        if any(k in name_lower for k in ['schema', 'config', 'manifest', 'index', 'inventory', 'catalog']):
            return "06_DATA", "data manifest"
        if any(k in name_lower for k in ['evidence', 'claim', 'authority', 'timeline']):
            return "06_DATA", "litigation data"
        return "06_DATA", "json data"
    
    if ext in {'.html', '.htm'}:
        return "09_REFERENCE", "html reference"
    
    if ext == '.md':
        # Markdown - could be analysis, reference, or filing
        if any(k in name_lower for k in ['readme', 'guide', 'doc', 'manual', 'faq', 'tutorial', 'index', 'start_here']):
            return "09_REFERENCE", "documentation"
        return "04_ANALYSIS", "analysis doc"
    
    if ext == '.txt':
        # Text - context-dependent
        if any(k in name_lower for k in ['log', 'stderr', 'stdout', 'progress']):
            return "12_WORKSPACE/LOGS", "log file"
        if any(k in name_lower for k in ['extract', 'ocr', 'scan']):
            return "01_EVIDENCE", "extracted text"
        return "06_DATA", "text data"
    
    if ext == '.pdf':
        # PDF - need content hints from name
        if any(k in name_lower for k in ['order', 'judgment', 'ruling']):
            return "03_COURT/ORDERS", "court PDF"
        if any(k in name_lower for k in ['motion', 'brief', 'complaint', 'petition']):
            return "05_FILINGS/DRAFTS", "filing PDF"
        if any(k in name_lower for k in ['evidence', 'exhibit', 'police']):
            return "01_EVIDENCE", "evidence PDF"
        return "06_DATA", "PDF data"
    
    if ext == '.docx':
        if any(k in name_lower for k in ['motion', 'brief', 'complaint', 'order']):
            return "05_FILINGS/DRAFTS", "filing docx"
        return "06_DATA", "docx data"
    
    if ext in {'.xml', '.yml', '.yaml', '.toml', '.cfg', '.ini', '.conf', '.sql'}:
        return "06_DATA", "config/data"
    
    if ext in DOC_EXTENSIONS:
        return "09_REFERENCE", "document"
    
    # === FALLBACK ===
    if not ext:
        return "11_ARCHIVES", "no extension"
    
    return "06_DATA", "unclassified"


def scan_and_route(source_dir, dry_run=True):
    """Scan files in source_dir and route them. Returns routing plan."""
    source = ROOT / source_dir
    if not source.exists():
        return {}
    
    plan = defaultdict(list)
    files = [f for f in source.iterdir() if f.is_file()]
    
    for f in files:
        target, reason = route_file(f)
        target_full = str(ROOT / target)
        # Don't move if already in correct location
        current_folder = source_dir.split('/')[0]
        target_folder = target.split('/')[0]
        if current_folder == target_folder and '/' not in target:
            continue  # Already in right top-level folder
        plan[target].append((str(f), reason))
    
    return dict(plan)


def execute_plan(plan, dry_run=False):
    """Execute the routing plan."""
    moved = 0
    errors = 0
    for target, files in plan.items():
        target_path = ROOT / target
        target_path.mkdir(parents=True, exist_ok=True)
        for src_path, reason in files:
            src = Path(src_path)
            dst = target_path / src.name
            if dst.exists():
                dst = target_path / f"dup_{src.name}"
            if not dry_run:
                try:
                    shutil.move(str(src), str(dst))
                    moved += 1
                except Exception as e:
                    errors += 1
            else:
                moved += 1
    return moved, errors


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    source = sys.argv[2] if len(sys.argv) > 2 else "06_DATA"
    
    plan = scan_and_route(source)
    
    total = sum(len(v) for v in plan.values())
    print(f"\n{'='*60}")
    print(f"ROUTING PLAN for {source}: {total} files to reroute")
    print(f"{'='*60}")
    
    for target in sorted(plan.keys()):
        files = plan[target]
        print(f"\n  → {target}: {len(files)} files")
        for src, reason in files[:3]:
            print(f"      {Path(src).name} ({reason})")
        if len(files) > 3:
            print(f"      ... and {len(files)-3} more")
    
    if mode == "execute":
        print(f"\nEXECUTING moves...")
        moved, errors = execute_plan(plan, dry_run=False)
        print(f"DONE: {moved} moved, {errors} errors")
    else:
        print(f"\nDRY RUN — use 'execute' to apply")

