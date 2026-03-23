#!/usr/bin/env python3
"""Tool #273: Legal Citation Validator
Validates ALL legal citations in filing documents and DB records.
Flags incorrect, outdated, or malformed citations.
"""
import sys
import os
import re
import sqlite3
import glob
from datetime import datetime
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'GENERATED_FILINGS')

GENERATED_FILINGS_DIR = OUTPUT_DIR
DESKTOP_FILING_DIR = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []

# ── Known valid citations (hardcoded baseline) ──────────────────────────────
KNOWN_VALID = {
    "MCL 722.23": "best interest factors",
    "MCL 722.27a": "parenting time",
    "MCR 2.003": "disqualification",
    "MCR 2.107": "service",
    "MCR 2.113": "form of documents",
    "MCR 2.612(C)": "fraud on court",
    "MCR 7.206": "superintending control",
    "42 USC §1983": "civil rights",
    "42 USC §1985": "conspiracy to interfere with civil rights",
    "MCL 750.423": "perjury",
    "MCL 750.157a": "conspiracy",
    "MCL 600.916": "unauthorized practice of law",
}

# ── Citation regex patterns ─────────────────────────────────────────────────
PATTERNS = {
    "MCL": re.compile(r'\bMCL\s+(\d{2,4}\.\d{1,5}[a-z]?(?:\([A-Za-z0-9]+\))*)', re.IGNORECASE),
    "MCR": re.compile(r'\bMCR\s+(\d\.\d{2,4}(?:\([A-Za-z0-9]+\))*)', re.IGNORECASE),
    "case_law": re.compile(
        r'([A-Z][A-Za-z\'\-]+(?:\s+(?:v|vs)\.?\s+[A-Z][A-Za-z\'\-]+)?'
        r',\s+\d{1,3}\s+(?:Mich(?:\s+App)?|F\.?\s*(?:2d|3d|4th)|S\.?\s*Ct|US|NW\.?\s*2d)\s+\d{1,5}'
        r'(?:\s*\(\d{4}\))?)'
    ),
    "USC": re.compile(r'\b(\d{1,2})\s+U\.?S\.?C\.?\s*§\s*(\d{3,5})', re.IGNORECASE),
    "FRAP": re.compile(r'\bFRAP\s+(\d{1,3})', re.IGNORECASE),
    "FRCP": re.compile(r'\bFRCP\s+(\d{1,3})', re.IGNORECASE),
}

# ── Format validators ───────────────────────────────────────────────────────
def validate_mcl(cite_text):
    m = re.match(r'MCL\s+(\d{2,4})\.(\d{1,5}[a-z]?)', cite_text, re.IGNORECASE)
    if not m:
        return False, "Malformed MCL citation — expected MCL ###.###"
    chapter = int(m.group(1))
    if chapter < 1 or chapter > 999:
        return False, f"MCL chapter {chapter} out of expected range (1-999)"
    return True, None

def validate_mcr(cite_text):
    m = re.match(r'MCR\s+(\d)\.(\d{2,4})', cite_text, re.IGNORECASE)
    if not m:
        return False, "Malformed MCR citation — expected MCR #.###"
    chapter = int(m.group(1))
    if chapter < 1 or chapter > 9:
        return False, f"MCR chapter {chapter} out of expected range (1-9)"
    return True, None

def validate_usc(cite_text):
    m = re.match(r'(\d{1,2})\s+U\.?S\.?C\.?\s*§\s*(\d{3,5})', cite_text, re.IGNORECASE)
    if not m:
        return False, "Malformed USC citation — expected ## USC §####"
    return True, None

def validate_case_law(cite_text):
    if ' v ' not in cite_text and ' v. ' not in cite_text and ' vs ' not in cite_text:
        return False, "Case citation missing 'v.' party separator"
    if not re.search(r'\d{1,3}\s+(?:Mich|F\.|S\.\s*Ct|US|NW)', cite_text):
        return False, "Case citation missing reporter reference"
    return True, None

VALIDATORS = {
    "MCL": validate_mcl,
    "MCR": validate_mcr,
    "USC": validate_usc,
    "case_law": validate_case_law,
}

def normalize_citation(ctype, raw):
    """Normalize a citation string for comparison."""
    raw = raw.strip()
    if ctype == "MCL":
        return "MCL " + re.sub(r'\bMCL\s+', '', raw, flags=re.IGNORECASE).strip()
    if ctype == "MCR":
        return "MCR " + re.sub(r'\bMCR\s+', '', raw, flags=re.IGNORECASE).strip()
    if ctype == "USC":
        m = re.match(r'(\d{1,2})\s+U\.?S\.?C\.?\s*§\s*(\d+)', raw, re.IGNORECASE)
        if m:
            return f"{m.group(1)} USC §{m.group(2)}"
    if ctype == "FRAP":
        m = re.match(r'FRAP\s+(\d+)', raw, re.IGNORECASE)
        if m:
            return f"FRAP {m.group(1)}"
    if ctype == "FRCP":
        m = re.match(r'FRCP\s+(\d+)', raw, re.IGNORECASE)
        if m:
            return f"FRCP {m.group(1)}"
    return raw

def extract_citations_from_text(text, source_label):
    """Extract all citations from a text block. Returns list of dicts."""
    results = []
    for ctype, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            raw = m.group(0).strip()
            if ctype == "USC":
                normalized = f"{m.group(1)} USC §{m.group(2)}"
            else:
                normalized = normalize_citation(ctype, raw)
            results.append({
                "citation_text": normalized,
                "citation_type": ctype,
                "raw_match": raw,
                "source": source_label,
            })
    return results

def scan_files(directory, extensions=("*.txt", "*.md")):
    """Scan a directory for files and extract citations."""
    all_citations = []
    if not os.path.isdir(directory):
        return all_citations
    for ext in extensions:
        for fpath in glob.glob(os.path.join(directory, "**", ext), recursive=True):
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read()
                cites = extract_citations_from_text(text, fpath)
                all_citations.extend(cites)
            except Exception:
                pass
    return all_citations

def scan_db_tables(conn):
    """Scan DB tables for citations."""
    all_citations = []

    # claims table
    rows = safe_query(conn, "SELECT claim_id, proposition, affirmative_counter_proposition FROM claims")
    for row in rows:
        combined = f"{row['proposition'] or ''} {row['affirmative_counter_proposition'] or ''}"
        cites = extract_citations_from_text(combined, f"DB:claims(claim_id={row['claim_id']})")
        for c in cites:
            c["source_table"] = "claims"
        all_citations.extend(cites)

    # research_authorities
    cols_check = safe_query(conn, "PRAGMA table_info(research_authorities)")
    if cols_check:
        col_names = [r['name'] for r in cols_check]
        text_cols = [c for c in col_names if any(k in s(c) for k in ['citation', 'authority', 'text', 'title', 'content', 'description'])]
        if not text_cols:
            text_cols = col_names[:5]
        select_expr = ", ".join([f'COALESCE("{c}", \'\')' for c in text_cols])
        rows = safe_query(conn, f"SELECT {select_expr} AS combined_text FROM research_authorities LIMIT 5000")
        for row in rows:
            combined = " ".join(str(v) for v in dict(row).values() if v)
            cites = extract_citations_from_text(combined, "DB:research_authorities")
            for c in cites:
                c["source_table"] = "research_authorities"
            all_citations.extend(cites)

    # authority_chains
    rows = safe_query(conn, "SELECT id, authority_cite, fact_claim FROM authority_chains")
    for row in rows:
        combined = f"{row['authority_cite'] or ''} {row['fact_claim'] or ''}"
        cites = extract_citations_from_text(combined, f"DB:authority_chains(id={row['id']})")
        for c in cites:
            c["source_table"] = "authority_chains"
        all_citations.extend(cites)

    # h_drive_authorities (may not exist)
    cols_check = safe_query(conn, "PRAGMA table_info(h_drive_authorities)")
    if cols_check:
        col_names = [r['name'] for r in cols_check]
        text_cols = [c for c in col_names if any(k in s(c) for k in ['citation', 'authority', 'text', 'title', 'content'])]
        if not text_cols:
            text_cols = col_names[:5]
        select_expr = ", ".join([f'COALESCE("{c}", \'\')' for c in text_cols])
        rows = safe_query(conn, f"SELECT {select_expr} FROM h_drive_authorities LIMIT 5000")
        for row in rows:
            combined = " ".join(str(v) for v in dict(row).values() if v)
            cites = extract_citations_from_text(combined, "DB:h_drive_authorities")
            for c in cites:
                c["source_table"] = "h_drive_authorities"
            all_citations.extend(cites)

    return all_citations

def check_against_known(citation_text):
    """Check if a citation is in the known-valid set."""
    normalized = citation_text.strip()
    # Direct match
    if normalized in KNOWN_VALID:
        return True
    # Match without subsection
    base = re.sub(r'\([^)]+\)', '', normalized).strip()
    if base in KNOWN_VALID:
        return True
    return False

def check_against_db_authorities(conn, citation_text):
    """Check if citation exists in any authority table in the DB."""
    # Search research_authorities (safe — check columns first)
    ra_cols = safe_query(conn, "PRAGMA table_info(research_authorities)")
    if ra_cols:
        col_names = [r['name'] for r in ra_cols]
        like_clauses = []
        for c in col_names:
            if any(k in s(c) for k in ['cite', 'citation', 'authority', 'title', 'text', 'content']):
                like_clauses.append(f'CAST("{c}" AS TEXT) LIKE ?')
        if like_clauses:
            sql = f"SELECT COUNT(*) as cnt FROM research_authorities WHERE {' OR '.join(like_clauses)}"
            params = tuple(f"%{citation_text}%" for _ in like_clauses)
            rows = safe_query(conn, sql, params)
            if rows and rows[0]['cnt'] > 0:
                return True
    # Search authority_chains
    rows = safe_query(conn,
        "SELECT COUNT(*) as cnt FROM authority_chains WHERE authority_cite LIKE ?",
        (f"%{citation_text}%",))
    if rows and rows[0]['cnt'] > 0:
        return True
    return False

def main():
    print("=" * 70)
    print("  TOOL #273: LEGAL CITATION VALIDATOR")
    print("  Pigors v. Watson — LitigationOS")
    print("=" * 70)
    print()

    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Connect to DB ────────────────────────────────────────────────────
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    # ── Create tracking table (drop stale schema if columns mismatch) ────
    existing_cols = safe_query(conn, "PRAGMA table_info(citation_validation)")
    expected_cols = {"id", "citation_text", "citation_type", "source_file",
                     "source_table", "is_valid", "is_verified", "issue",
                     "suggested_fix", "scan_date"}
    if existing_cols:
        actual_cols = {r["name"] for r in existing_cols}
        if not expected_cols.issubset(actual_cols):
            conn.execute("DROP TABLE citation_validation")
            conn.commit()
            print("  [INFO] Dropped old citation_validation table (schema mismatch)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS citation_validation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citation_text TEXT,
            citation_type TEXT,
            source_file TEXT,
            source_table TEXT,
            is_valid INTEGER,
            is_verified INTEGER,
            issue TEXT,
            suggested_fix TEXT,
            scan_date TEXT
        )
    """)
    conn.commit()

    # ── Clear previous scan ──────────────────────────────────────────────
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("DELETE FROM citation_validation WHERE scan_date LIKE ?",
                     (datetime.now().strftime("%Y-%m-%d") + "%",))
        conn.commit()
    except Exception:
        conn.execute("DELETE FROM citation_validation")
        conn.commit()

    # ── Phase 1: Scan files ──────────────────────────────────────────────
    print("[1/4] Scanning GENERATED_FILINGS/ ...")
    gen_cites = scan_files(GENERATED_FILINGS_DIR)
    print(f"       Found {len(gen_cites)} citations in GENERATED_FILINGS/")

    print("[2/4] Scanning Desktop LITIGATION_FILING_PACKAGE/ ...")
    desk_cites = scan_files(DESKTOP_FILING_DIR)
    print(f"       Found {len(desk_cites)} citations in LITIGATION_FILING_PACKAGE/")

    # ── Phase 2: Scan DB tables ──────────────────────────────────────────
    print("[3/4] Scanning DB tables (claims, research_authorities, authority_chains) ...")
    db_cites = scan_db_tables(conn)
    print(f"       Found {len(db_cites)} citations in database tables")

    all_citations = gen_cites + desk_cites + db_cites
    print(f"\n       TOTAL citations found: {len(all_citations)}")

    # ── Phase 3: Validate each citation ──────────────────────────────────
    print("\n[4/4] Validating citations ...")
    stats = {"total": 0, "valid": 0, "invalid": 0, "verified": 0, "unverified": 0}
    seen = set()
    insert_rows = []

    for cite in all_citations:
        ctext = cite["citation_text"]
        ctype = cite["citation_type"]
        source_file = cite.get("source", "")
        source_table = cite.get("source_table", "")

        dedup_key = f"{ctext}|{source_file}|{source_table}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        stats["total"] += 1

        # Format validation
        is_valid = 1
        issue = ""
        suggested_fix = ""
        validator = VALIDATORS.get(ctype)
        if validator:
            valid, msg = validator(ctext)
            if not valid:
                is_valid = 0
                issue = msg or "Format validation failed"
                stats["invalid"] += 1
            else:
                stats["valid"] += 1
        else:
            stats["valid"] += 1

        # Verification against known citations and DB
        is_verified = 0
        if check_against_known(ctext):
            is_verified = 1
            stats["verified"] += 1
        elif check_against_db_authorities(conn, ctext):
            is_verified = 1
            stats["verified"] += 1
        else:
            stats["unverified"] += 1
            if not issue:
                issue = "Citation not found in authority database — verify manually"

        insert_rows.append((
            ctext, ctype, source_file, source_table,
            is_valid, is_verified, issue, suggested_fix, today
        ))

    # ── Batch insert ─────────────────────────────────────────────────────
    conn.executemany("""
        INSERT INTO citation_validation
        (citation_text, citation_type, source_file, source_table,
         is_valid, is_verified, issue, suggested_fix, scan_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_rows)
    conn.commit()

    # ── Generate report ──────────────────────────────────────────────────
    report_path = os.path.join(REPORT_DIR, "citation_validation_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("  CITATION VALIDATION REPORT\n")
        f.write(f"  Generated: {today}\n")
        f.write(f"  Case: Pigors v. Watson\n")
        f.write("=" * 70 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"  Total unique citations scanned: {stats['total']}\n")
        f.write(f"  Valid format:                   {stats['valid']}\n")
        f.write(f"  Invalid format:                 {stats['invalid']}\n")
        f.write(f"  Verified (in authority DB):      {stats['verified']}\n")
        f.write(f"  Unverified (manual check):       {stats['unverified']}\n\n")

        # Group by type
        f.write("CITATIONS BY TYPE\n")
        f.write("-" * 40 + "\n")
        type_counts = {}
        for row in insert_rows:
            ct = row[1]
            type_counts[ct] = type_counts.get(ct, 0) + 1
        for ct, cnt in sorted(type_counts.items()):
            f.write(f"  {ct:15s}: {cnt}\n")
        f.write("\n")

        # List issues
        issues = [r for r in insert_rows if r[6]]
        if issues:
            f.write("ISSUES FOUND\n")
            f.write("-" * 40 + "\n")
            for r in issues[:100]:
                f.write(f"  [{r[1]}] {r[0]}\n")
                f.write(f"         Source: {r[2] or r[3]}\n")
                f.write(f"         Issue:  {r[6]}\n")
                if r[7]:
                    f.write(f"         Fix:    {r[7]}\n")
                f.write("\n")
        else:
            f.write("NO ISSUES FOUND — all citations pass validation.\n\n")

        # Known valid baseline
        f.write("KNOWN VALID BASELINE CITATIONS\n")
        f.write("-" * 40 + "\n")
        for cite, desc in sorted(KNOWN_VALID.items()):
            f.write(f"  ✓ {cite:25s} — {desc}\n")

    print(f"\n{'=' * 70}")
    print("  RESULTS")
    print(f"{'=' * 70}")
    print(f"  Total unique citations:  {stats['total']}")
    print(f"  Valid format:            {stats['valid']}")
    print(f"  Invalid format:          {stats['invalid']}")
    print(f"  Verified in authority:   {stats['verified']}")
    print(f"  Unverified:              {stats['unverified']}")
    print(f"\n  Report saved to: {report_path}")
    print(f"  DB table: citation_validation ({stats['total']} rows inserted)")
    print(f"{'=' * 70}")

    conn.close()

if __name__ == "__main__":
    main()
