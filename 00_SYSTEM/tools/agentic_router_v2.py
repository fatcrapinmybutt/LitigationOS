import os, sys, shutil, re, json, time, logging
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

ROOT = Path(r"C:\Users\andre\LitigationOS")
LOG_DIR = ROOT / "12_WORKSPACE" / "LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"router_{datetime.now():%Y%m%d_%H%M%S}.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("router")

# ============================================================
# PATTERN TIERS — Priority-ordered (highest priority first)
# Each tier: (compiled_regex_on_filename, target_folder, label)
# ============================================================

# Tier 0: JUNK — delete or archive immediately
JUNK_PATTERNS = re.compile(
    r"^\.DS_Store$|^Thumbs\.db$|^desktop\.ini$|^\._\.|"
    r"^__pycache__|\.pyc$|\.pyo$|"
    r"^\$I[A-Z0-9]{7}\.|"   # Recycle bin artifacts
    r"^\.eslintrc_|^\.editorconfig_",
    re.IGNORECASE
)

# Tier 1: EVIDENCE — litigation evidence (highest functional priority)
EVIDENCE_RE = re.compile(
    r"evidence|exhibit[_\s]|police[_\s]?report|NSPD|NS\d{7}|"
    r"witness[_\s]|testimony|statement[_\s]|appclose|AppClose|"
    r"forensic|affidavit|body[_\s]?camera|allegation|recant|"
    r"drug[_\s]?screen|parenting[_\s]?time[_\s]?viol|"
    r"custody[_\s]?evidence|alienation[_\s]?evid|false[_\s]?alleg|"
    r"SHADYOAKS|shady[_\s]?oaks|sewage|mold[_\s]?|habitab|"
    r"lease[_\s]?(?:viol|billing)|housing[_\s]?viol|eviction[_\s]?|"
    r"demand[_\s]?for[_\s]?possession|noreply|NoReply|"
    r"ppo[_\s]?(?:evidence|docket|petition)|"
    r"Pigors.*Lease|scanned[_\s]?demand|"
    r"BF\d{8}|behindchildsupport|"
    r"HOA[_\s]|jeremy[_\s]?piper|TRUE[_\s]?NORTH|PARTRIDGE[_\s]?check|"
    r"kim[_\s]?(?:davis|shady)|neighbor[_\s]?HOA|"
    r"TITLE[_\s]?TO[_\s]?MOBILE|"
    r"CIVIL\s+DISPOSITION|Civil[_\s]?Disposition",
    re.IGNORECASE
)

# Evidence photos — ChatGPT uploads and dated camera photos
EVIDENCE_PHOTO_RE = re.compile(
    r"^file-[A-Za-z0-9]{20,}|"
    r"^20\d{6}_\d{6}\.\w{3}$|"
    r"^\d{10,13}\.jpg$",
    re.IGNORECASE
)

# Tier 2: COURT RECORDS
COURT_RE = re.compile(
    r"(?:court[_\s]?order|(?:^|\b)judgment|disposition[_\s]|docket[_\s]?(?:entry|event)|"
    r"transcript|hearing[_\s]?(?:transcript|minute)|(?:^|\b)ruling[_\s]|"
    r"ex[_\s]?parte[_\s]?order|custody[_\s]?order|"
    r"PPO[_\s]?order|bench[_\s]?warrant|arraign|sentenc|"
    r"(?:FOC|friend[_\s]?of[_\s]?court)[_\s]?(?:report|rec|order)|"
    r"People[_\s]?v[_\s]?Pigors)",
    re.IGNORECASE
)

# Tier 3: FILINGS — our court filings
FILING_RE = re.compile(
    r"(?:motion[_\s]?(?:to|for|in)|brief[_\s]?(?:in|on)|"
    r"(?:verified[_\s]?)?complaint|petition[_\s]|"
    r"certificate[_\s]?of[_\s]?service|"
    r"proposed[_\s]?order|emergency[_\s]?motion|"
    r"disqualification|custody[_\s]?modification|"
    r"ppo[_\s]?termination|"
    r"MSC[_\s]?(?:original|application|complaint|ExParte)|"
    r"JTC[_\s]?(?:complaint|packet|Verified)|"
    r"COA[_\s]?(?:brief|emergency|complaint|Proposed)|"
    r"appellant[_\s]?brief|"
    r"proof[_\s]?of[_\s]?service|cover[_\s]?sheet|"
    r"filing[_\s]?(?:package|checklist)|court[_\s]?ready|"
    r"Pigors_v_Watson.*(?:COA|MSC|JTC|Order|Brief)|"
    r"Superintending[_\s]?Control|"
    r"(?:F0[1-9]|F10|PKG_F)[_\s])",
    re.IGNORECASE
)

# Dated filing pattern: 2025-XX-XX_Type_*
DATED_FILING_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}_(?:COA|MSC|JTC|Filing|Pigors|Case)",
    re.IGNORECASE
)

# Tier 4: ANALYSIS
ANALYSIS_RE = re.compile(
    r"(?:analysis|_report\b|timeline[_\s]|impeach|"
    r"contradiction|adversary|"
    r"judicial[_\s]?(?:bias|violation|pattern|misconduct|audit|intel)|"
    r"damages[_\s]?calc|best[_\s]?interest|"
    r"red[_\s]?team|assessment|(?:^|\b)audit[_\s]|"
    r"strategy|compilation|intelligence[_\s]|"
    r"narrative|scoring|gap[_\s]?analysis|"
    r"violation[_\s]?(?:pattern|compil|matrix)|"
    r"credibility|pattern[_\s]?mining|"
    r"convergence|omega[_\s]?(?:deep|judicial|key|evidence)|"
    r"wave\d{1,2}[_\s]|cross[_\s]?filing|"
    r"rebuttal|weapon|conspiracy[_\s]|"
    r"PROCESS_ARTIFACTS|EXECUTION_SUMMARY|"
    r"mining[_\s]?(?:report|output)|harvest[_\s])",
    re.IGNORECASE
)

# Tier 5: AUTHORITY
AUTHORITY_RE = re.compile(
    r"(?:(?:^|\b)MCR[_\s]|(?:^|\b)MCL[_\s]|(?:^|\b)MRE[_\s]|"
    r"court[_\s]?rule|(?:^|\b)statute|"
    r"[Bb]enchbook|canon[_\s]|SCAO|"
    r"legal[_\s]?reference|"
    r"[Mm]ichigan[_\s]?(?:court|law|rule|compiled)|"
    r"[Rr]esidential[_\s]?[Ll]andlord|"
    r"[Ss]exual[_\s]?[Aa]ssault[_\s]?[Bb]enchbook|"
    r"authority[_\s]?(?:chain|index|anchor|validation|map)|"
    r"^0{3}\d-\d{2})",  # Court rule HTML pattern: 0001-01.html
    re.IGNORECASE
)

# Tier 6: Bulk artifact patterns (npm packages, Python internals, doc hashes)
NPM_PACKAGE_RE = re.compile(r"^package_\d+(?:_\d+)?\.json$")
DOC_HASH_RE = re.compile(r"^doc_[0-9a-f]{8}_\d+(?:_hits(?:_\d+)?)?\.(?:json|txt)$")
PYTHON_INTERNAL_RE = re.compile(
    r"^__(?:init|main|pip-runner|pycache)__\.|"
    r"^_(?:abc|ast|thread|pydevd|compat|collections|io|signal|stat|weakref)\.|"
    r"\.cpython-\d{3}\.pyc$"
)

def sub_route_evidence(name):
    nl = name.lower()
    if any(k in nl for k in ['shady', 'housing', 'lease', 'evict', 'sewage', 'mold',
                              'habitab', 'demand_for_possession', 'hoa', 'piper',
                              'true_north', 'true north', 'partridge', 'kim_davis',
                              'kim davis', 'kim shady', 'title_to_mobile', 'title to mobile']):
        return "01_EVIDENCE/HOUSING"
    if any(k in nl for k in ['police', 'nspd', 'ns20', 'ns25', 'body_camera']):
        return "01_EVIDENCE/POLICE"
    if any(k in nl for k in ['ppo']):
        return "01_EVIDENCE/PPO"
    if any(k in nl for k in ['exhibit', 'bates']):
        return "01_EVIDENCE/EXHIBITS"
    if any(k in nl for k in ['appclose', 'noreply', 'correspondence', 'email']):
        return "01_EVIDENCE/CORRESPONDENCE"
    if any(k in nl for k in ['forensic', 'metadata']):
        return "01_EVIDENCE/FORENSIC"
    return "01_EVIDENCE/CUSTODY"

def sub_route_filing(name):
    nl = name.lower()
    if any(k in nl for k in ['f01', 'emergency_tro', 'tro']):
        return "05_FILINGS/F01_EMERGENCY_TRO"
    if any(k in nl for k in ['f02', 'shady_oaks_complaint']):
        return "05_FILINGS/F02_SHADY_OAKS"
    if any(k in nl for k in ['f03', 'disqualif']):
        return "05_FILINGS/F03_DISQUALIFICATION"
    if any(k in nl for k in ['f04', '1983', 'federal']):
        return "05_FILINGS/F04_FEDERAL_1983"
    if any(k in nl for k in ['f05', 'msc', 'superintend']):
        return "05_FILINGS/F05_MSC_ORIGINAL"
    if any(k in nl for k in ['f06', 'jtc']):
        return "05_FILINGS/F06_JTC_COMPLAINT"
    if any(k in nl for k in ['f07', 'custody_mod']):
        return "05_FILINGS/F07_CUSTODY_MOD"
    if any(k in nl for k in ['f08', 'ppo_termin']):
        return "05_FILINGS/F08_PPO_TERMINATION"
    if any(k in nl for k in ['f09', 'coa_brief', 'appellant']):
        return "05_FILINGS/F09_COA_BRIEF"
    if any(k in nl for k in ['f10', 'coa_emergency']):
        return "05_FILINGS/F10_COA_EMERGENCY"
    if any(k in nl for k in ['court_ready']):
        return "05_FILINGS/COURT_READY"
    return "05_FILINGS/DRAFTS"

def sub_route_analysis(name):
    nl = name.lower()
    if any(k in nl for k in ['timeline', 'chronolog']):
        return "04_ANALYSIS/TIMELINES"
    if any(k in nl for k in ['impeach']):
        return "04_ANALYSIS/IMPEACHMENT"
    if any(k in nl for k in ['contradiction']):
        return "04_ANALYSIS/CONTRADICTIONS"
    if any(k in nl for k in ['adversary', 'watson', 'barnes', 'opposing']):
        return "04_ANALYSIS/ADVERSARY"
    if any(k in nl for k in ['judicial', 'mcneill', 'berry', 'bias', 'canon']):
        return "04_ANALYSIS/JUDICIAL"
    if any(k in nl for k in ['damage', 'compensation']):
        return "04_ANALYSIS/DAMAGES"
    if any(k in nl for k in ['best_interest', 'bif_', 'factor_']):
        return "04_ANALYSIS/BEST_INTEREST"
    if any(k in nl for k in ['red_team', 'vulnerab']):
        return "04_ANALYSIS/RED_TEAM"
    if re.search(r'wave\d', nl):
        return "04_ANALYSIS/WAVES"
    return "04_ANALYSIS"

def route_file(filepath):
    """Route a single file. Returns (target_folder, label) or None to skip."""
    name = filepath.name
    ext = filepath.suffix.lower()
    
    # === TIER 0: Junk → Archive ===
    if JUNK_PATTERNS.search(name):
        return "11_ARCHIVES/JUNK", "junk"
    
    # === TIER 1: Evidence ===
    if EVIDENCE_RE.search(name):
        return sub_route_evidence(name), "evidence"
    if EVIDENCE_PHOTO_RE.search(name) and ext in {'.jpg','.jpeg','.png','.gif','.bmp'}:
        return "01_EVIDENCE/PHOTOS", "evidence_photo"
    
    # === TIER 2: Court records ===
    if COURT_RE.search(name):
        nl = name.lower()
        if any(k in nl for k in ['judgment', 'disposition']):
            return "03_COURT/JUDGMENTS", "judgment"
        if any(k in nl for k in ['transcript', 'hearing']):
            return "03_COURT/TRANSCRIPTS", "transcript"
        if any(k in nl for k in ['docket']):
            return "03_COURT/DOCKET", "docket"
        if any(k in nl for k in ['foc', 'friend_of_court']):
            return "03_COURT/FOC", "foc"
        if any(k in nl for k in ['criminal', 'people_v', 'arraign']):
            return "03_COURT/CRIMINAL", "criminal"
        return "03_COURT/ORDERS", "court_order"
    
    # === TIER 3: Filings ===
    if FILING_RE.search(name) or DATED_FILING_RE.search(name):
        return sub_route_filing(name), "filing"
    
    # === TIER 4: Analysis ===
    if ANALYSIS_RE.search(name):
        return sub_route_analysis(name), "analysis"
    
    # === TIER 5: Authority ===
    if AUTHORITY_RE.search(name):
        nl = name.lower()
        if 'benchbook' in nl:
            return "02_AUTHORITY/BENCHBOOKS", "benchbook"
        if re.match(r'^0{3}\d-\d{2}', name):
            return "02_AUTHORITY/MCR", "court_rule_html"
        if any(k in nl for k in ['authority', 'case_law']):
            return "02_AUTHORITY/CASE_LAW", "authority"
        return "02_AUTHORITY", "authority"
    
    # === TIER 6: Bulk artifact patterns ===
    if NPM_PACKAGE_RE.match(name):
        return "11_ARCHIVES/NPM", "npm_package"
    if DOC_HASH_RE.match(name):
        return None, "data_stay"  # Already in 06_DATA, keep there
    if PYTHON_INTERNAL_RE.search(name):
        return "11_ARCHIVES/PYTHON", "python_internal"
    
    # === TIER 7: Extension-based fallback ===
    if ext in {'.py', '.js', '.ts', '.jsx', '.tsx', '.bat', '.ps1', '.sh',
               '.spec', '.cmake', '.c', '.cpp', '.h', '.go', '.rs', '.java'}:
        return "07_CODE", "code"
    if ext in {'.pyc', '.pyo', '.traineddata', '.zdct', '.sav'}:
        return "11_ARCHIVES", "artifact"
    if ext in {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar'}:
        return "11_ARCHIVES", "archive"
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico',
               '.bmp', '.tiff', '.mp4', '.wav', '.mp3'}:
        return "08_MEDIA", "media"
    if ext in {'.db', '.sqlite'}:
        return "06_DATA", "database"
    if ext == '.md':
        nl = name.lower()
        if any(k in nl for k in ['readme', 'guide', 'manual', 'faq', 'tutorial', 'index', 'start_here', 'how_to']):
            return "09_REFERENCE", "documentation"
        return None, "md_stay"  # Keep in current location
    if ext == '.txt':
        nl = name.lower()
        if any(k in nl for k in ['log', 'stderr', 'stdout', 'progress']):
            return "12_WORKSPACE/LOGS", "log"
        return None, "txt_stay"
    if ext in {'.html', '.htm'}:
        return None, "html_stay"  # Keep in reference
    if ext in {'.rst', '.test', '.pxd', '.map', '.d.ts.map', '.js.map'}:
        return "11_ARCHIVES", "dev_artifact"
    if ext in {'.csv', '.jsonl', '.xlsx', '.json', '.xml', '.yml', '.yaml',
               '.toml', '.sql', '.cfg', '.ini', '.conf'}:
        return None, "data_stay"  # Keep in data
    if ext in {'.pdf', '.docx', '.odt', '.rtf'}:
        return None, "doc_stay"  # Needs content analysis we can't do
    
    # === TIER 8: No extension or unknown ===
    if not ext:
        return "11_ARCHIVES/MISC", "no_extension"
    return None, "unknown_stay"


def process_zone(zone_path, dry_run=True):
    """Process all root-level files in a zone. Returns metrics."""
    source = ROOT / zone_path
    if not source.exists():
        log.error(f"Zone {zone_path} does not exist")
        return {}
    
    files = [f for f in source.iterdir() if f.is_file()]
    total = len(files)
    log.info(f"Processing {zone_path}: {total} root files")
    
    moves = defaultdict(list)
    stays = Counter()
    errors = []
    moved_count = 0
    
    for i, f in enumerate(files):
        if i % 5000 == 0 and i > 0:
            log.info(f"  Progress: {i}/{total} ({i*100//total}%)")
        
        try:
            result = route_file(f)
            if result is None:
                stays["null_route"] += 1
                continue
            target, label = result
            if target is None:
                stays[label] += 1
                continue
            
            # Don't move if already in target top-level folder
            current_top = zone_path.split('/')[0]
            target_top = target.split('/')[0]
            if current_top == target_top:
                stays[f"already_{target_top}"] += 1
                continue
            
            target_dir = ROOT / target
            target_file = target_dir / f.name
            
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                if target_file.exists():
                    target_file = target_dir / f"dup_{f.name}"
                try:
                    shutil.move(str(f), str(target_file))
                    moved_count += 1
                except Exception as e:
                    errors.append((str(f), str(e)))
            else:
                moved_count += 1
            
            moves[target].append(f.name)
        except Exception as e:
            errors.append((str(f), str(e)))
    
    # Report
    log.info(f"\n{'='*60}")
    log.info(f"{'DRY RUN' if dry_run else 'EXECUTED'} — {zone_path}")
    log.info(f"{'='*60}")
    log.info(f"Total files: {total}")
    log.info(f"To move: {moved_count}")
    log.info(f"Staying: {sum(stays.values())}")
    log.info(f"Errors: {len(errors)}")
    
    log.info(f"\nRouting breakdown:")
    for target in sorted(moves.keys()):
        count = len(moves[target])
        samples = moves[target][:3]
        log.info(f"  → {target}: {count} files")
        for s in samples:
            log.info(f"      {s}")
        if count > 3:
            log.info(f"      ... +{count-3} more")
    
    if stays:
        log.info(f"\nStaying in place:")
        for reason, count in stays.most_common(10):
            log.info(f"  {reason}: {count}")
    
    if errors:
        log.info(f"\nErrors ({len(errors)}):")
        for path, err in errors[:5]:
            log.info(f"  {path}: {err}")
    
    return {"moved": moved_count, "stayed": sum(stays.values()), "errors": len(errors), "total": total}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LitigationOS Agentic Router v2.0")
    parser.add_argument("zone", help="Zone to process (e.g., 06_DATA, 04_ANALYSIS, ROOT)")
    parser.add_argument("--execute", action="store_true", help="Actually move files (default: dry run)")
    args = parser.parse_args()
    
    zone = args.zone
    dry_run = not args.execute
    
    if zone == "ROOT":
        # Special handling for root — only process files, not dirs
        source = ROOT
        files = [f for f in source.iterdir() if f.is_file()]
        # Filter out protected root files
        PROTECTED = {'_CANON.md', 'README.md', 'pyproject.toml', 'requirements.txt',
                     'mcp.json', '.gitignore', '.gitattributes', '.gitconfig',
                     'litigationos.config.jsonc', 'master.code-workspace',
                     'litigation_context.db', 'litigationos.db'}
        total = len(files)
        moved = 0
        for f in files:
            if f.name in PROTECTED:
                continue
            result = route_file(f)
            if result is None:
                continue
            target, label = result
            if target is None:
                continue
            target_dir = ROOT / target
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                dst = target_dir / f.name
                if dst.exists():
                    dst = target_dir / f"dup_{f.name}"
                try:
                    shutil.move(str(f), str(dst))
                    moved += 1
                except:
                    pass
            else:
                moved += 1
        log.info(f"ROOT: {moved}/{total} files {'would be' if dry_run else ''} moved")
    else:
        metrics = process_zone(zone, dry_run=dry_run)
        print(json.dumps(metrics, indent=2))
