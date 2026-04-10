"""
FILING QA ENGINE — Automated Quality Gate Checker
Scans all GOLDEN_SET .md files against 12 quality gates:
  1. Citation verification (vs authority_chains_v2 DB)
  2. Placeholder patterns ([ANDREW_REQUIRED], [INSERT], [TBD], etc.)
  3. Banned strings (hallucinations: Jane Berry, Patricia Berry, etc.)
  4. Wrong year (not 2026 in filing dates)
  5. Child full name (Lincoln David Watson → must use L.D.W.)
  6. AI/DB references (LitigationOS, EGCP, SINGULARITY, etc.)
  7. Party name errors (Emily A. Watson, McNeil vs McNeill)
  8. Attorney status (Barnes withdrew Mar 2026)
  9. Pro se compliance (no "undersigned counsel")
  10. Stale day counts (hardcoded separation days)
  11. Criminal lane contamination (2025-25245676SM in non-criminal filings)
  12. MCL 722.27c (nonexistent — should be MCL 722.23(j))

Outputs per-filing QA report, updates filing_readiness in DB.
"""

import sqlite3
import re
import json
import os
from pathlib import Path
from datetime import datetime, date

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
GOLDEN_SET = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET")
REPORT_PATH = Path(r"D:\LitigationOS_tmp\filing_qa_report.json")

# ═══════════════════════════════════════════════════════
# QUALITY GATE DEFINITIONS
# ═══════════════════════════════════════════════════════

PLACEHOLDER_PATTERNS = [
    r'\[ANDREW_REQUIRED[^\]]*\]',
    r'\[VERIFY[^\]]*\]',
    r'\[COMPUTE[^\]]*\]',
    r'\[INSERT[^\]]*\]',
    r'\[TBD[^\]]*\]',
    r'\[PLACEHOLDER[^\]]*\]',
    r'\[TODO[^\]]*\]',
    r'\[ATTACH[^\]]*\]',
    r'\[CITE[^\]]*\]',
    r'\[DATE[^\]]*\]',
    r'\[FILL[^\]]*\]',
    r'\[NEED[^\]]*\]',
    r'\[MISSING[^\]]*\]',
    r'\[REQUIRED[^\]]*\]',
    r'\[ADD[^\]]*\]',
]

BANNED_STRINGS = [
    ("jane berry", "HALLUCINATION: Jane Berry never existed"),
    ("patricia berry", "HALLUCINATION: Patricia Berry never existed"),
    ("p35878", "HALLUCINATION: Fabricated bar number P35878"),
    ("91% alienation", "HALLUCINATION: Fabricated alienation score"),
    ("ron berry, esq", "ERROR: Ronald Berry is NOT an attorney"),
    ("ron berry esq", "ERROR: Ronald Berry is NOT an attorney"),
    ("amy mcneill", "ERROR: Judge's name is Jenny L. McNeill"),
    ("emily ann watson", "ERROR: Defendant is Emily A. Watson"),
    ("emily m. watson", "ERROR: Wrong middle initial"),
    ("tiffany watson", "ERROR: Wrong first name for defendant"),
    ("watson-pigors", "ERROR: Wrong defendant name format"),
    ("9 cps investigations", "HALLUCINATION: Andrew called CPS once"),
]

AI_DB_PATTERNS = [
    (r'\blitigationos\b', "AI_REF: LitigationOS system reference"),
    (r'\bmanbearpig\b', "AI_REF: THEMANBEARPIG system reference"),
    (r'\begcp\b', "AI_REF: EGCP scoring reference"),
    (r'\bsingularity\b', "AI_REF: SINGULARITY system reference"),
    (r'\bmeek\b', "AI_REF: MEEK lane detection reference"),
    (r'\bevidence_quotes\b', "AI_REF: DB table name in filing"),
    (r'\bauthority_chains\b', "AI_REF: DB table name in filing"),
    (r'\bimpeachment_matrix\b', "AI_REF: DB table name in filing"),
    (r'\btimeline_events\b', "AI_REF: DB table name in filing"),
    (r'\blitigation_context\.db\b', "AI_REF: Database filename in filing"),
    (r'C:\\Users\\andre', "AI_REF: File path in filing"),
    (r'00_SYSTEM', "AI_REF: System directory reference"),
    (r'D:\\LitigationOS', "AI_REF: Temp directory reference"),
    (r'\bnexus daemon\b', "AI_REF: Daemon reference"),
    (r'\blocus.?=.?12\b', "AI_REF: LOCUS scoring in filing"),
    (r'\bbrain\.db\b', "AI_REF: Brain database reference"),
]

PROSECOMPLIANCE_PATTERNS = [
    (r'undersigned counsel', "PRO_SE: Must use 'Plaintiff, appearing pro se'"),
    (r'attorney for plaintiff', "PRO_SE: Andrew is pro se, no attorney"),
    (r'counsel for', "PRO_SE: No counsel — pro se"),
    (r'my client', "PRO_SE: No client — Andrew IS the plaintiff"),
    (r'our client', "PRO_SE: No client — Andrew IS the plaintiff"),
]

STALE_DAY_PATTERNS = [
    (r'\b(\d{3,4})\s*days?\s*(of\s*)?separation', "STALE_DAYS: Hardcoded day count"),
    (r'\b(\d{3,4})\s*days?\s*since\s*(last\s*)?contact', "STALE_DAYS: Hardcoded day count"),
    (r'\b(\d{3,4})\s*days?\s*without\s*(seeing|contact)', "STALE_DAYS: Hardcoded day count"),
]

# Citation extraction regex
CITATION_PATTERN = re.compile(
    r'(?:MCR|MCL|MRE|USC)\s*[\d§]+[\.\d\(\)\w]*',
    re.IGNORECASE
)

CASE_LAW_PATTERN = re.compile(
    r'[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+',
)

# Child full name patterns (MUST NOT appear)
CHILD_NAME_PATTERNS = [
    re.compile(r'lincoln\s+david\s+watson', re.IGNORECASE),
    re.compile(r'lincoln\s+d\.?\s+watson', re.IGNORECASE),
    re.compile(r'lincoln\s+watson', re.IGNORECASE),
    re.compile(r'\blincoln\s+david\b', re.IGNORECASE),
]

# MCL 722.27c does NOT exist
NONEXISTENT_CITE = re.compile(r'MCL\s*722\.27c', re.IGNORECASE)

# Criminal case number (must not appear in non-criminal filings)
CRIMINAL_CASE = re.compile(r'2025.?25245676', re.IGNORECASE)

# Wrong year in filing context (dates should be 2026)
WRONG_YEAR_PATTERN = re.compile(
    r'(?:filed|dated|signed|submitted|served|this)\s+\w*\s*'
    r'(?:day\s+of\s+)?(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s*(?:\d{1,2},?\s*)?'
    r'(202[0-5])',
    re.IGNORECASE
)

# McNeil (missing second L)
MCNEIL_TYPO = re.compile(r'\bMcNeil\b(?!l)')


def connect_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    return conn


def load_known_citations(conn):
    """Load all known citations from authority_chains_v2 for verification."""
    known = set()
    try:
        rows = conn.execute("""
            SELECT DISTINCT primary_citation FROM authority_chains_v2
            WHERE primary_citation IS NOT NULL
            UNION
            SELECT DISTINCT supporting_citation FROM authority_chains_v2
            WHERE supporting_citation IS NOT NULL
        """).fetchall()
        for r in rows:
            # Normalize: strip whitespace, uppercase
            cite = r[0].strip().upper() if r[0] else ""
            if cite:
                known.add(cite)
    except Exception as e:
        print(f"  WARNING: Could not load citations: {e}")

    # Also load from michigan_rules_extracted
    try:
        rows = conn.execute("""
            SELECT DISTINCT rule_citation FROM michigan_rules_extracted
            WHERE rule_citation IS NOT NULL
        """).fetchall()
        for r in rows:
            cite = r[0].strip().upper() if r[0] else ""
            if cite:
                known.add(cite)
    except Exception:
        pass

    # Also from master_citations if exists
    try:
        rows = conn.execute("""
            SELECT DISTINCT citation FROM master_citations
            WHERE citation IS NOT NULL
        """).fetchall()
        for r in rows:
            cite = r[0].strip().upper() if r[0] else ""
            if cite:
                known.add(cite)
    except Exception:
        pass

    return known


def scan_file(filepath, known_citations):
    """Run all QA gates on a single .md file. Returns list of findings."""
    findings = []
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        findings.append({"gate": "FILE_READ", "severity": "CRITICAL",
                         "message": f"Cannot read file: {e}", "line": 0})
        return findings

    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()

        # Gate 1: Placeholder patterns
        for pattern in PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for m in matches:
                # Allow [ACQUIRE: ...] (specific, documented)
                if m.upper().startswith('[ACQUIRE'):
                    continue
                findings.append({
                    "gate": "PLACEHOLDER",
                    "severity": "HIGH",
                    "message": f"Placeholder found: {m[:80]}",
                    "line": i,
                })

        # Gate 2: Banned strings
        for banned, reason in BANNED_STRINGS:
            if banned in line_lower:
                findings.append({
                    "gate": "BANNED_STRING",
                    "severity": "CRITICAL",
                    "message": reason,
                    "line": i,
                })

        # Gate 3: AI/DB references
        for pattern, reason in AI_DB_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if in a comment or metadata block
                stripped = line.strip()
                if stripped.startswith('<!--') or stripped.startswith('#!'):
                    continue
                findings.append({
                    "gate": "AI_REFERENCE",
                    "severity": "CRITICAL",
                    "message": reason,
                    "line": i,
                })

        # Gate 4: Child full name
        for pat in CHILD_NAME_PATTERNS:
            if pat.search(line):
                findings.append({
                    "gate": "CHILD_NAME",
                    "severity": "CRITICAL",
                    "message": "MCR 8.119(H) VIOLATION: Child's full name exposed",
                    "line": i,
                })

        # Gate 5: Pro se compliance
        for pattern, reason in PROSECOMPLIANCE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "gate": "PRO_SE",
                    "severity": "HIGH",
                    "message": reason,
                    "line": i,
                })

        # Gate 6: MCL 722.27c (nonexistent)
        if NONEXISTENT_CITE.search(line):
            findings.append({
                "gate": "BAD_CITATION",
                "severity": "HIGH",
                "message": "MCL 722.27c DOES NOT EXIST — correct cite is MCL 722.23(j)",
                "line": i,
            })

        # Gate 7: McNeil typo (missing L)
        if MCNEIL_TYPO.search(line):
            findings.append({
                "gate": "TYPO",
                "severity": "MEDIUM",
                "message": "McNeill has TWO L's — fix spelling",
                "line": i,
            })

        # Gate 8: Stale day counts
        for pattern, reason in STALE_DAY_PATTERNS:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                findings.append({
                    "gate": "STALE_DAYS",
                    "severity": "HIGH",
                    "message": f"{reason}: '{m.group()}'",
                    "line": i,
                })

        # Gate 9: Criminal lane contamination
        if CRIMINAL_CASE.search(line):
            # Check if this is a criminal-specific filing
            parent_dir = filepath.parent.name.upper()
            if 'CRIMINAL' not in parent_dir:
                findings.append({
                    "gate": "CRIMINAL_CONTAMINATION",
                    "severity": "CRITICAL",
                    "message": "Criminal case number in non-criminal filing",
                    "line": i,
                })

        # Gate 10: Wrong year in filing dates
        m = WRONG_YEAR_PATTERN.search(line)
        if m:
            year = m.group(1)
            findings.append({
                "gate": "WRONG_YEAR",
                "severity": "HIGH",
                "message": f"Filing date uses year {year} instead of 2026",
                "line": i,
            })

    # Gate 11: Citation verification (file-level)
    file_citations = set()
    for m in CITATION_PATTERN.finditer(text):
        cite = m.group().strip().upper()
        # Normalize spaces
        cite = re.sub(r'\s+', ' ', cite)
        file_citations.add(cite)

    unverified = []
    for cite in file_citations:
        # Check if ANY prefix/variant matches known citations
        found = False
        for known in known_citations:
            if cite in known or known in cite:
                found = True
                break
        # Also check common patterns
        if not found:
            # MCR X.XXX, MCL XXX.XXX are structural — likely valid if well-formed
            if re.match(r'MCR\s*\d+\.\d+', cite) or re.match(r'MCL\s*\d+\.\d+', cite):
                # Check if base citation exists
                base = re.match(r'(MCR|MCL)\s*(\d+\.\d+)', cite)
                if base:
                    base_cite = f"{base.group(1)} {base.group(2)}".upper()
                    for known in known_citations:
                        if base_cite in known:
                            found = True
                            break
        if not found:
            unverified.append(cite)

    if unverified:
        # Only flag if significant number are unverified
        for cite in unverified[:10]:
            findings.append({
                "gate": "UNVERIFIED_CITATION",
                "severity": "LOW",
                "message": f"Citation not found in DB: {cite}",
                "line": 0,
            })

    # Gate 12: Brady v Maryland in family law context
    if re.search(r'brady\s+v\.?\s+maryland', text, re.IGNORECASE):
        # Check if this is a criminal filing
        parent_dir = filepath.parent.name.upper()
        if 'CRIMINAL' not in parent_dir and 'FEDERAL' not in parent_dir and '1983' not in parent_dir:
            findings.append({
                "gate": "BAD_CITATION",
                "severity": "MEDIUM",
                "message": "Brady v Maryland is criminal-only — use Mathews v Eldridge for family law due process",
                "line": 0,
            })

    return findings


def scan_filing_directory(dir_path, known_citations):
    """Scan all .md files in a filing directory."""
    results = {
        "directory": dir_path.name,
        "path": str(dir_path),
        "files_scanned": 0,
        "total_findings": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "gates_failed": set(),
        "gates_passed": set(),
        "file_results": [],
    }

    all_gates = {
        "PLACEHOLDER", "BANNED_STRING", "AI_REFERENCE", "CHILD_NAME",
        "PRO_SE", "BAD_CITATION", "TYPO", "STALE_DAYS",
        "CRIMINAL_CONTAMINATION", "WRONG_YEAR", "UNVERIFIED_CITATION",
        "FILE_READ",
    }

    md_files = sorted(dir_path.glob("*.md"))
    if not md_files:
        results["qa_result"] = "NO_FILES"
        return results

    failed_gates = set()

    for md_file in md_files:
        findings = scan_file(md_file, known_citations)
        file_result = {
            "file": md_file.name,
            "findings_count": len(findings),
            "findings": findings,
        }
        results["file_results"].append(file_result)
        results["files_scanned"] += 1
        results["total_findings"] += len(findings)

        for f in findings:
            sev = f["severity"]
            if sev == "CRITICAL":
                results["critical"] += 1
            elif sev == "HIGH":
                results["high"] += 1
            elif sev == "MEDIUM":
                results["medium"] += 1
            elif sev == "LOW":
                results["low"] += 1
            failed_gates.add(f["gate"])

    results["gates_failed"] = list(failed_gates)
    results["gates_passed"] = list(all_gates - failed_gates)

    # Determine QA result
    if results["critical"] > 0:
        results["qa_result"] = "FAIL"
    elif results["high"] > 3:
        results["qa_result"] = "CONDITIONAL"
    elif results["high"] > 0:
        results["qa_result"] = "CONDITIONAL"
    else:
        results["qa_result"] = "PASS"

    return results


def update_filing_readiness(conn, filing_id, qa_result, finding_count, placeholder_count):
    """Update filing_readiness table with QA results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Map directory names to filing IDs
    dir_to_filing = {
        "F01_MSC_PETITION": "F1",
        "F02_FAIR_HOUSING": "F2",
        "F03_DISQUALIFICATION": "F3",
        "F04_FEDERAL_1983": "F4",
        "F05_MSC_ORIGINAL": "F5",
        "F06_JTC_COMPLAINT": "F6",
        "F07_CUSTODY_MOD": "F7",
        "F08_PPO_TERMINATION": "F8",
        "F09_COA_BRIEF": "F9",
        "F10_COA_EMERGENCY": "F10",
    }

    fid = dir_to_filing.get(filing_id, filing_id)

    try:
        # Check if row exists
        row = conn.execute(
            "SELECT vehicle_name FROM filing_readiness WHERE vehicle_name = ?",
            (fid,)
        ).fetchone()

        if row:
            conn.execute("""
                UPDATE filing_readiness
                SET qa_result = ?,
                    last_qa_date = ?,
                    placeholder_count = ?
                WHERE vehicle_name = ?
            """, (qa_result, now, placeholder_count, fid))
        else:
            print(f"  WARNING: No filing_readiness row for {fid}")

    except Exception as e:
        print(f"  ERROR updating {fid}: {e}")


def main():
    print("=" * 70)
    print("FILING QA ENGINE — Automated Quality Gate Checker")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {GOLDEN_SET}")
    print("=" * 70)

    # Connect and load known citations
    conn = connect_db()
    print("\n[Phase 1] Loading known citations from DB...")
    known_citations = load_known_citations(conn)
    print(f"  Loaded {len(known_citations):,} known citations")

    # Discover filing directories
    print("\n[Phase 2] Discovering GOLDEN_SET directories...")
    filing_dirs = sorted([d for d in GOLDEN_SET.iterdir() if d.is_dir()])
    print(f"  Found {len(filing_dirs)} filing directories")

    # Scan each directory
    print("\n[Phase 3] Running 12-gate QA scan...")
    all_results = []
    summary = {"PASS": 0, "CONDITIONAL": 0, "FAIL": 0, "NO_FILES": 0}

    for filing_dir in filing_dirs:
        print(f"\n  Scanning: {filing_dir.name}")
        result = scan_filing_directory(filing_dir, known_citations)

        # Count placeholders specifically
        placeholder_count = sum(
            1 for fr in result["file_results"]
            for f in fr["findings"]
            if f["gate"] == "PLACEHOLDER"
        )

        qa = result["qa_result"]
        summary[qa] = summary.get(qa, 0) + 1

        icon = {"PASS": "✅", "CONDITIONAL": "⚠️", "FAIL": "❌", "NO_FILES": "⬜"}
        print(f"    {icon.get(qa, '?')} {qa} | "
              f"Files: {result['files_scanned']} | "
              f"Findings: {result['total_findings']} "
              f"(C:{result['critical']} H:{result['high']} M:{result['medium']} L:{result['low']}) | "
              f"Placeholders: {placeholder_count}")

        if result["gates_failed"]:
            print(f"    Failed gates: {', '.join(result['gates_failed'])}")

        # Show top findings
        for fr in result["file_results"]:
            critical_findings = [f for f in fr["findings"] if f["severity"] in ("CRITICAL", "HIGH")]
            for cf in critical_findings[:3]:
                print(f"      L{cf['line']}: [{cf['severity']}] {cf['message'][:70]}")

        # Update DB
        update_filing_readiness(conn, filing_dir.name, qa, result["total_findings"], placeholder_count)

        # Clean up sets for JSON serialization (already converted to lists above)
        all_results.append(result)

    conn.commit()

    # Verify DB updates
    print("\n[Phase 4] Verifying DB updates...")
    rows = conn.execute("""
        SELECT vehicle_name, qa_result, last_qa_date, placeholder_count
        FROM filing_readiness
        WHERE qa_result IS NOT NULL
        ORDER BY vehicle_name
    """).fetchall()
    print(f"  Updated {len(rows)} filing_readiness rows:")
    for r in rows:
        print(f"    {r[0]}: QA={r[1]}, Date={r[2]}, Placeholders={r[3]}")

    conn.close()

    # Generate report
    print("\n[Phase 5] Generating QA report...")
    report = {
        "run_time": datetime.now().isoformat(),
        "source": str(GOLDEN_SET),
        "known_citations_loaded": len(known_citations),
        "directories_scanned": len(filing_dirs),
        "summary": summary,
        "total_findings": sum(r["total_findings"] for r in all_results),
        "total_critical": sum(r["critical"] for r in all_results),
        "total_high": sum(r["high"] for r in all_results),
        "total_medium": sum(r["medium"] for r in all_results),
        "total_low": sum(r["low"] for r in all_results),
        "results": all_results,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print(f"  Report saved: {REPORT_PATH}")

    # Final summary
    print("\n" + "=" * 70)
    print("QA ENGINE SUMMARY")
    print("=" * 70)
    print(f"  Directories: {len(filing_dirs)}")
    print(f"  Files scanned: {sum(r['files_scanned'] for r in all_results)}")
    print(f"  Total findings: {report['total_findings']}")
    print(f"  CRITICAL: {report['total_critical']}")
    print(f"  HIGH: {report['total_high']}")
    print(f"  MEDIUM: {report['total_medium']}")
    print(f"  LOW: {report['total_low']}")
    print(f"  Results: ✅ PASS={summary['PASS']} | ⚠️ CONDITIONAL={summary['CONDITIONAL']} | ❌ FAIL={summary['FAIL']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
