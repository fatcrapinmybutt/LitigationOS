#!/usr/bin/env python3
"""
LitigationOS File Organization Engine v1.0
============================================
Moves loose root-level files into proper subdirectories based on
file type, name patterns, and content classification.

Rules:
- NEVER deletes files — moves only
- NEVER touches databases (.db, .sqlite)
- NEVER moves protected system files
- Logs every move to organize_log.csv
- Respects the 6 case lane boundaries (A-F)

Usage:
    python organize_engine.py --dry-run     # Preview all moves
    python organize_engine.py --execute     # Execute moves
    python organize_engine.py --category legal --execute  # Only legal docs
"""

import sys
import os
import re
import csv
import shutil
import argparse
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

ROOT = Path(r"C:\Users\andre\LitigationOS")
LOG_FILE = ROOT / "00_SYSTEM" / "organize_log.csv"

# === CLASSIFICATION RULES ===
# Each rule: (name_pattern_regex, extension_list, target_directory, description)
# Rules are evaluated in order — first match wins.

RULES = [
    # --- PROTECTED: never move ---
    # (handled by is_protected())

    # --- LEGAL FILINGS (motions, complaints, orders, affidavits) ---
    {
        'id': 'motions',
        'name_patterns': [r'(?i)motion', r'(?i)Motion_'],
        'extensions': ['.docx', '.pdf'],
        'target': 'Motions',
        'category': 'legal',
    },
    {
        'id': 'complaints',
        'name_patterns': [r'(?i)complaint', r'(?i)Amended.*Complaint', r'(?i)ORIGINAL_COMPLAINT'],
        'extensions': ['.docx', '.pdf'],
        'target': 'Complaints',
        'category': 'legal',
    },
    {
        'id': 'affidavits',
        'name_patterns': [r'(?i)affidavit', r'(?i)declaration', r'(?i)Verified_'],
        'extensions': ['.docx', '.pdf'],
        'target': 'Affidavits',
        'category': 'legal',
    },
    {
        'id': 'certificates',
        'name_patterns': [r'(?i)certificate.*service', r'(?i)proof.*service', r'(?i)Certificate_of_'],
        'extensions': ['.docx', '.pdf'],
        'target': 'Proof_Artifacts',
        'category': 'legal',
    },
    {
        'id': 'proposed_orders',
        'name_patterns': [r'(?i)proposed.*order', r'(?i)ProposedOrder'],
        'extensions': ['.docx', '.pdf'],
        'target': 'Motions',
        'category': 'legal',
    },
    {
        'id': 'exhibits',
        'name_patterns': [r'(?i)exhibit_', r'(?i)Exhibit_', r'(?i)Tabbed_Exhibit'],
        'extensions': ['.docx', '.pdf'],
        'target': 'EXHIBITS',
        'category': 'legal',
    },
    {
        'id': 'notices',
        'name_patterns': [r'(?i)notice_', r'(?i)Notice_of_', r'(?i)NOTICE'],
        'extensions': ['.docx', '.pdf'],
        'target': 'notices',
        'category': 'legal',
    },
    {
        'id': 'clerk_forms',
        'name_patterns': [r'(?i)clerk_', r'(?i)Clerk_', r'(?i)MC_326', r'(?i)mc\d+'],
        'extensions': ['.docx', '.pdf'],
        'target': '02_Court_Forms',
        'category': 'legal',
    },
    {
        'id': 'foia',
        'name_patterns': [r'(?i)FOIA', r'(?i)foia'],
        'extensions': ['.docx', '.pdf'],
        'target': 'foia',
        'category': 'legal',
    },
    {
        'id': 'subpoenas',
        'name_patterns': [r'(?i)subpoena', r'(?i)discovery', r'(?i)interrogator', r'(?i)Request_for_'],
        'extensions': ['.docx', '.pdf'],
        'target': 'Motions',
        'category': 'legal',
    },
    {
        'id': 'briefs',
        'name_patterns': [r'(?i)brief', r'(?i)Brief', r'(?i)Supplemental_Brief'],
        'extensions': ['.docx', '.pdf'],
        'target': '01_FILINGS',
        'category': 'legal',
    },

    # --- COURT FORM PDFs (scao, mc, cc, dc, foc, pc forms) ---
    {
        'id': 'court_form_pdf',
        'name_patterns': [r'^(mc|cc|dc|foc|pc|jc|dcmm)\d+', r'(?i)scao', r'(?i)MSC-pro-per'],
        'extensions': ['.pdf', '.pdf.txt'],
        'target': '02_Court_Forms',
        'category': 'legal',
    },

    # --- EVIDENCE (photos, screenshots, scans, media) ---
    {
        'id': 'evidence_photos',
        'name_patterns': [r'^IMG_', r'^20\d{6}_\d{6}', r'^Screenshot_', r'^PSX_'],
        'extensions': ['.jpg', '.jpeg', '.png', '.heic', '.gif', '.webp'],
        'target': '10_IMAGES',
        'category': 'evidence',
    },
    {
        'id': 'evidence_video',
        'name_patterns': [r'.*'],
        'extensions': ['.mp4', '.mp3', '.wav', '.mov'],
        'target': '10_IMAGES',
        'category': 'evidence',
    },
    {
        'id': 'evidence_scans',
        'name_patterns': [r'(?i)scan', r'^NoReply_', r'(?i)Scanned_'],
        'extensions': ['.pdf'],
        'target': '07_PDF',
        'category': 'evidence',
    },

    # --- DATA FILES ---
    {
        'id': 'csv_data',
        'name_patterns': [r'.*'],
        'extensions': ['.csv', '.tsv'],
        'target': '09_DATA',
        'category': 'data',
    },
    {
        'id': 'json_data',
        'name_patterns': [r'.*'],
        'extensions': ['.json', '.jsonl'],
        'target': '09_DATA',
        'category': 'data',
    },
    {
        'id': 'yaml_data',
        'name_patterns': [r'.*'],
        'extensions': ['.yaml', '.yml'],
        'target': '09_DATA',
        'category': 'data',
    },

    # --- SCRIPTS & CODE ---
    {
        'id': 'python_scripts',
        'name_patterns': [r'.*'],
        'extensions': ['.py'],
        'target': 'scripts',
        'category': 'code',
    },
    {
        'id': 'powershell_scripts',
        'name_patterns': [r'.*'],
        'extensions': ['.ps1'],
        'target': 'scripts',
        'category': 'code',
    },
    {
        'id': 'batch_scripts',
        'name_patterns': [r'.*'],
        'extensions': ['.bat', '.sh', '.cmd'],
        'target': 'scripts',
        'category': 'code',
    },
    {
        'id': 'spec_files',
        'name_patterns': [r'.*'],
        'extensions': ['.spec'],
        'target': 'scripts',
        'category': 'code',
    },

    # --- DOCUMENTS ---
    {
        'id': 'general_docx',
        'name_patterns': [r'.*'],
        'extensions': ['.docx', '.doc'],
        'target': 'Legal Documents',
        'category': 'docs',
    },
    {
        'id': 'general_pdf',
        'name_patterns': [r'.*'],
        'extensions': ['.pdf'],
        'target': '07_PDF',
        'category': 'docs',
    },
    {
        'id': 'text_files',
        'name_patterns': [r'.*'],
        'extensions': ['.txt', '.rtf'],
        'target': '08_TEXT',
        'category': 'docs',
    },
    {
        'id': 'markdown_files',
        'name_patterns': [r'.*'],
        'extensions': ['.md'],
        'target': '08_TEXT',
        'category': 'docs',
    },

    # --- IMAGES ---
    {
        'id': 'general_images',
        'name_patterns': [r'.*'],
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.heic', '.ico'],
        'target': '10_IMAGES',
        'category': 'images',
    },

    # --- ARCHIVES ---
    {
        'id': 'archives',
        'name_patterns': [r'.*'],
        'extensions': ['.zip', '.gz', '.tar', '.7z', '.rar', '.crdownload'],
        'target': '12_ARCHIVES',
        'category': 'archives',
    },

    # --- EMAIL ---
    {
        'id': 'email',
        'name_patterns': [r'.*'],
        'extensions': ['.eml', '.ics'],
        'target': '09_DATA',
        'category': 'email',
    },

    # --- PRESENTATIONS ---
    {
        'id': 'presentations',
        'name_patterns': [r'.*'],
        'extensions': ['.pptx', '.ppt'],
        'target': '09_DATA',
        'category': 'docs',
    },

    # --- SPREADSHEETS ---
    {
        'id': 'spreadsheets',
        'name_patterns': [r'.*'],
        'extensions': ['.xlsx', '.xls'],
        'target': '09_DATA',
        'category': 'data',
    },

    # --- CONFIG/SYSTEM ---
    {
        'id': 'xml_config',
        'name_patterns': [r'.*'],
        'extensions': ['.xml', '.toml', '.cfg', '.ini', '.env'],
        'target': '09_DATA',
        'category': 'config',
    },

    # --- WAVE 3.5: PREVIOUSLY UNCOVERED EXTENSIONS ---

    # Web / HTML visualizations
    {
        'id': 'html_files',
        'name_patterns': [r'.*'],
        'extensions': ['.html', '.htm', '.css'],
        'target': 'ui',
        'category': 'code',
    },

    # JavaScript / TypeScript / JSX / TSX (React components, UI code)
    {
        'id': 'js_ts_files',
        'name_patterns': [r'.*'],
        'extensions': ['.js', '.jsx', '.tsx', '.ts'],
        'target': 'ui',
        'category': 'code',
    },

    # SQL scripts
    {
        'id': 'sql_scripts',
        'name_patterns': [r'.*'],
        'extensions': ['.sql'],
        'target': 'schemas',
        'category': 'data',
    },

    # Cypher (Neo4j graph queries)
    {
        'id': 'cypher_scripts',
        'name_patterns': [r'.*'],
        'extensions': ['.cypher'],
        'target': 'cypher',
        'category': 'data',
    },

    # Graphviz DOT / ERD diagrams
    {
        'id': 'dot_diagrams',
        'name_patterns': [r'.*'],
        'extensions': ['.dot'],
        'target': 'diagrams',
        'category': 'docs',
    },

    # NSIS installer scripts
    {
        'id': 'nsi_installers',
        'name_patterns': [r'.*'],
        'extensions': ['.nsi'],
        'target': 'Builds',
        'category': 'code',
    },

    # Executable / installer / DLL binaries
    {
        'id': 'binaries',
        'name_patterns': [r'.*'],
        'extensions': ['.exe', '.msi', '.dll'],
        'target': 'Builds',
        'category': 'code',
    },

    # Jupyter notebooks
    {
        'id': 'notebooks',
        'name_patterns': [r'.*'],
        'extensions': ['.ipynb'],
        'target': 'scripts',
        'category': 'code',
    },

    # Backup / temp legal docs
    {
        'id': 'backup_legal',
        'name_patterns': [r'.*'],
        'extensions': ['.bak', '.tmd', '.tmdx', '.tct'],
        'target': 'Legal Documents',
        'category': 'legal',
    },

    # Word templates / draw files
    {
        'id': 'office_templates',
        'name_patterns': [r'.*'],
        'extensions': ['.dotx', '.odg'],
        'target': '02_Court_Forms',
        'category': 'legal',
    },

    # Language / localization files
    {
        'id': 'lang_files',
        'name_patterns': [r'.*'],
        'extensions': ['.lng'],
        'target': '09_DATA',
        'category': 'config',
    },

    # Log files
    {
        'id': 'log_files',
        'name_patterns': [r'.*'],
        'extensions': ['.log'],
        'target': '04_LOGS',
        'category': 'data',
    },

    # Config files (JSONC, code-workspace, etc.)
    {
        'id': 'jsonc_config',
        'name_patterns': [r'.*'],
        'extensions': ['.jsonc', '.code-workspace'],
        'target': 'configs',
        'category': 'config',
    },

    # Disk images / ghost files
    {
        'id': 'disk_images',
        'name_patterns': [r'.*'],
        'extensions': ['.gsd'],
        'target': '12_ARCHIVES',
        'category': 'archives',
    },

    # Split archive parts
    {
        'id': 'split_parts',
        'name_patterns': [r'.*'],
        'extensions': ['.part000', '.part001', '.part002', '.part003', '.part005',
                       '.part006', '.part008', '.part010', '.part011', '.part012'],
        'target': '12_ARCHIVES',
        'category': 'archives',
    },

    # SHA-256 checksum files
    {
        'id': 'checksum_files',
        'name_patterns': [r'.*'],
        'extensions': ['.sha256'],
        'target': '12_ARCHIVES',
        'category': 'archives',
    },

    # Restructured text / Makefiles / C headers
    {
        'id': 'build_source',
        'name_patterns': [r'.*'],
        'extensions': ['.rst', '.in', '.h', '.cpp', '.cc', '.c'],
        'target': 'Source_Code',
        'category': 'code',
    },

    # Model / tokenizer files (ML artifacts)
    {
        'id': 'ml_artifacts',
        'name_patterns': [r'.*'],
        'extensions': ['.model', '.v3'],
        'target': '09_DATA',
        'category': 'data',
    },

    # Lock files
    {
        'id': 'lock_files',
        'name_patterns': [r'.*'],
        'extensions': ['.lock'],
        'target': '09_DATA',
        'category': 'config',
    },

    # VSIX packages
    {
        'id': 'vsix_packages',
        'name_patterns': [r'.*'],
        'extensions': ['.vsixpackage', '.VSIXPackage'],
        'target': 'Builds',
        'category': 'code',
    },
]

# Files that must NEVER be moved
PROTECTED_FILES = {
    'litigation_context.db', 'flatten_manifest.db', 'drive_inventory.db',
    'copilot-instructions.md', 'AGENTS.md', 'LICENSE', 'README.md',
    'CONTRIBUTING.md', 'CODE_OF_CONDUCT.md', 'CHANGELOG.md',
    '.gitignore', '.gitattributes', 'desktop.ini', 'gitattributes',
    'COMMIT_EDITMSG', 'HEAD', 'FETCH_HEAD', 'description', 'index',
    'master.code-workspace', 'Makefile',
    'LICENSE (2)',
}

PROTECTED_EXTENSIONS = {'.db', '.db-shm', '.db-wal', '.sqlite', '.lnk'}

PROTECTED_PREFIXES = ['dedup_manifest', 'jobqueue', 'history.', 'test_litigation']


def is_protected(filepath: Path) -> bool:
    """Files that must never be moved."""
    name = filepath.name
    if name in PROTECTED_FILES:
        return True
    if filepath.suffix.lower() in PROTECTED_EXTENSIONS:
        return True
    for prefix in PROTECTED_PREFIXES:
        if name.startswith(prefix):
            return True
    # Don't move hidden/git files
    if name.startswith('.'):
        return True
    return False


def classify_file(filepath: Path) -> dict | None:
    """Classify a file and return the matching rule, or None.
    
    Handles compound suffixes like .png_MISC_NO_CONTENT by trying
    the primary suffix first, then scanning for known extensions in the name.
    """
    ext = filepath.suffix.lower()
    name = filepath.name

    # First pass: exact extension match
    for rule in RULES:
        if ext not in rule['extensions']:
            continue
        for pattern in rule['name_patterns']:
            if re.search(pattern, name):
                return rule

    # Second pass: scan for known extension embedded in name
    # Handles files like "screenshot.png_MISC_NO_CONTENT_09_19_2024"
    all_known_exts = set()
    for rule in RULES:
        all_known_exts.update(rule['extensions'])
    
    name_lower = name.lower()
    for known_ext in sorted(all_known_exts, key=len, reverse=True):
        if known_ext in name_lower:
            for rule in RULES:
                if known_ext not in rule['extensions']:
                    continue
                for pattern in rule['name_patterns']:
                    if re.search(pattern, name):
                        return rule

    # Third pass: extensionless files — classify by name content
    if not ext or ext == '':
        name_up = name.upper()
        if any(kw in name_up for kw in ['COMPLAINT', 'MOTION', 'NOTICE', 'ORDER', 'AFFIDAVIT']):
            return {'id': 'extensionless_legal', 'target': 'Legal Documents', 'category': 'legal'}
        if any(kw in name_up for kw in ['SCREENSHOT', 'IMG_', 'PHOTO']):
            return {'id': 'extensionless_image', 'target': '10_IMAGES', 'category': 'images'}
        if any(kw in name_up for kw in ['CONV', 'CHAT', 'EMAIL', 'EXPARTE']):
            return {'id': 'extensionless_text', 'target': '08_TEXT', 'category': 'docs'}

    return None


def init_log():
    """Initialize the organization log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'action', 'source', 'destination',
                'rule_id', 'category', 'size_bytes'
            ])


def log_action(action, source, destination, rule_id, category, size):
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(), action, str(source),
            str(destination), rule_id, category, size
        ])


def run_organize(dry_run=True, category_filter=None, limit=0):
    """Main organization execution."""
    init_log()

    print(f"\n{'='*60}")
    print(f"LitigationOS File Organization Engine v1.0")
    print(f"Source: {ROOT} (root-level files only)")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE — moving files'}")
    if category_filter:
        print(f"Category filter: {category_filter}")
    print(f"{'='*60}\n")

    # Get root-level files only
    files = [f for f in ROOT.iterdir() if f.is_file() and not is_protected(f)]
    print(f"Eligible files: {len(files)}")

    classified = 0
    moved = 0
    unclassified = []
    errors = 0
    by_target = {}

    for f in files:
        rule = classify_file(f)
        if not rule:
            unclassified.append(f)
            continue

        if category_filter and rule['category'] != category_filter:
            continue

        classified += 1
        target_dir = ROOT / rule['target']
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f.name

        # Handle collision
        if target_path.exists():
            stem = f.stem
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_org{counter}{f.suffix}"
                counter += 1

        by_target[rule['target']] = by_target.get(rule['target'], 0) + 1

        if limit and moved >= limit:
            break

        try:
            size = f.stat().st_size
            if dry_run:
                log_action('DRY_MOVE', f, target_path, rule['id'], rule['category'], size)
            else:
                shutil.move(str(f), str(target_path))
                log_action('MOVED', f, target_path, rule['id'], rule['category'], size)
            moved += 1
        except (OSError, PermissionError) as e:
            errors += 1
            log_action('ERROR', f, 'N/A', rule['id'], rule['category'], 0)
            print(f"  [ERROR] {f.name}: {e}")

    print(f"\n--- Files by target directory ---")
    for target, count in sorted(by_target.items(), key=lambda x: -x[1]):
        print(f"  {target:30s} → {count:4d} files")

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Total eligible:     {len(files)}")
    print(f"  Classified:         {classified}")
    print(f"  {'Would move' if dry_run else 'Moved'}:           {moved}")
    print(f"  Unclassified:       {len(unclassified)}")
    print(f"  Errors:             {errors}")
    print(f"  Log: {LOG_FILE}")
    print(f"{'='*60}\n")

    if unclassified and len(unclassified) <= 50:
        print("--- Unclassified files (remaining in root) ---")
        for f in sorted(unclassified, key=lambda x: x.suffix):
            print(f"  {f.suffix:8s} {f.name}")

    return moved, len(unclassified), errors


def main():
    parser = argparse.ArgumentParser(description='LitigationOS File Organization Engine')
    parser.add_argument('--dry-run', action='store_true', help='Preview without moving')
    parser.add_argument('--execute', action='store_true', help='Execute moves')
    parser.add_argument('--category', type=str, help='Filter by category (legal, evidence, data, code, docs, images, archives)')
    parser.add_argument('--limit', type=int, default=0, help='Max files to move')
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.error("Specify --dry-run or --execute")

    run_organize(
        dry_run=args.dry_run,
        category_filter=args.category,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
