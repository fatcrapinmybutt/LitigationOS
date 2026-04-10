"""
Wave 1: Filing Pipeline Advancement Engine
==========================================
Computes EGCP scores for all 17 filings, scans GOLDEN_SET for quality,
runs QA checks, populates bates_registry, and advances filing statuses.

EGCP Scoring (0-25 each, total 0-100):
  E = Evidence density (evidence_quotes per lane)
  G = Grounds/Impeachment (impeachment_matrix coverage)
  C = Citations/Authority (authority_chains_v2 per lane)
  P = Presentation (GOLDEN_SET files, exhibit quality, QA passes)
"""
import sqlite3
import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime, date

# ── Paths ────────────────────────────────────────────────────────────────
DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
GOLDEN_SET = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET")
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# ── Lane mapping for each filing ─────────────────────────────────────────
FILING_LANE_MAP = {
    "F1":  "A",  "F2":  "B",  "F3":  "A",  "F4":  "A",
    "F5":  "F",  "F6":  "E",  "F7":  "A",  "F8":  "D",
    "F9":  "F",  "F10": "F",
    "F-1983v2": "C", "F-CUSTmod": "A", "F-JTC": "E",
    "F-DISQv2": "E", "F-MSC2": "F", "F-VAC": "A", "F-PPOterm": "D",
}

# Map GOLDEN_SET directory names to filing IDs
GOLDEN_DIR_MAP = {
    "F01_MSC_PETITION": "F1",
    "F02_FAIR_HOUSING": "F2",
    "F03_DISQUALIFICATION": "F3",
    "F04_FEDERAL_1983": "F4",
    "F05_MSC_ORIGINAL": "F5",
    "F06_JTC_COMPLAINT": "F6",
    "F08_PPO_TERMINATION": "F8",
    "F09_COA_BRIEF": "F9",
    "F10_COA_EMERGENCY": "F10",
}

# ── QA patterns ──────────────────────────────────────────────────────────
PLACEHOLDER_PATTERNS = [
    r'\[ANDREW_REQUIRED[^\]]*\]', r'\[VERIFY[^\]]*\]',
    r'\[COMPUTE[^\]]*\]', r'\[INSERT[^\]]*\]',
    r'\[TBD[^\]]*\]', r'\[PLACEHOLDER[^\]]*\]',
    r'\[TODO[^\]]*\]', r'\[ATTACH[^\]]*\]',
]
BANNED_STRINGS = [
    "jane berry", "patricia berry", "91% alienation",
    "lincoln david watson", "ron berry, esq", "amy mcneill",
    "emily ann watson", "emily m. watson", "p35878",
]
YEAR_WRONG = re.compile(r'\b202[0-4]\b')  # Wrong year (should be 2026 in filings)
CHILD_FULL_NAME = re.compile(r'lincoln\s+david', re.IGNORECASE)


def connect_db():
    """Connect with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def safe_count(conn, sql, params=()):
    """Safe count query with error handling."""
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else 0
    except Exception as e:
        print(f"  ⚠ Query error: {e}")
        return 0


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: Compute Evidence Counts Per Lane
# ═══════════════════════════════════════════════════════════════════════
def compute_evidence_counts(conn):
    """Count evidence_quotes per lane (excluding duplicates)."""
    rows = conn.execute("""
        SELECT lane, COUNT(*) as cnt
        FROM evidence_quotes
        WHERE is_duplicate = 0 AND lane IS NOT NULL AND lane != ''
        GROUP BY lane
    """).fetchall()
    return {r[0]: r[1] for r in rows}


def compute_authority_counts(conn):
    """Count authority_chains_v2 per lane."""
    rows = conn.execute("""
        SELECT lane, COUNT(*) as cnt
        FROM authority_chains_v2
        WHERE lane IS NOT NULL AND lane != ''
        GROUP BY lane
    """).fetchall()
    return {r[0]: r[1] for r in rows}


def compute_impeachment_counts(conn, filing_id):
    """Count impeachment_matrix entries relevant to a filing.
    impeachment_matrix.filing_relevance is comma-separated filing IDs."""
    try:
        cnt = conn.execute("""
            SELECT COUNT(*) FROM impeachment_matrix
            WHERE filing_relevance LIKE '%' || ? || '%'
        """, (filing_id,)).fetchone()[0]
        return cnt
    except Exception:
        return 0


def compute_contradiction_counts(conn, lane):
    """Count contradictions for a lane (via lane column or text search)."""
    # Check if lane column exists
    cols = {r[1] for r in conn.execute("PRAGMA table_info(contradiction_map)")}
    if "lane" in cols:
        return safe_count(conn, "SELECT COUNT(*) FROM contradiction_map WHERE lane = ?", (lane,))
    else:
        return safe_count(conn, "SELECT COUNT(*) FROM contradiction_map")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: Scan GOLDEN_SET for Presentation Quality
# ═══════════════════════════════════════════════════════════════════════
def scan_golden_set():
    """Scan GOLDEN_SET directories for file counts and exhibit quality."""
    results = {}
    if not GOLDEN_SET.exists():
        print(f"  ⚠ GOLDEN_SET not found at {GOLDEN_SET}")
        return results

    for dir_name, filing_id in GOLDEN_DIR_MAP.items():
        dir_path = GOLDEN_SET / dir_name
        if not dir_path.exists():
            results[filing_id] = {"md_files": 0, "pdf_files": 0, "exhibits": 0,
                                   "total_words": 0, "qa_issues": []}
            continue

        md_files = list(dir_path.glob("*.md"))
        pdf_dir = dir_path / "PDF"
        pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []

        # Count exhibits in EXHIBITS/ or APPENDIX/ subdirs
        exhibit_dirs = ["EXHIBITS", "APPENDIX"]
        exhibit_count = 0
        for ed in exhibit_dirs:
            ed_path = dir_path / ed
            if ed_path.exists():
                exhibit_count += len(list(ed_path.glob("*")))

        # Count total words across .md files
        total_words = 0
        qa_issues = []
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
                words = len(content.split())
                total_words += words

                # QA checks on each file
                for pat in PLACEHOLDER_PATTERNS:
                    matches = re.findall(pat, content)
                    if matches:
                        qa_issues.append(f"PLACEHOLDER in {md_file.name}: {len(matches)} found")

                for banned in BANNED_STRINGS:
                    if banned in content.lower():
                        qa_issues.append(f"BANNED STRING '{banned}' in {md_file.name}")

                if CHILD_FULL_NAME.search(content):
                    qa_issues.append(f"CHILD FULL NAME in {md_file.name}")

            except Exception as e:
                qa_issues.append(f"READ ERROR {md_file.name}: {e}")

        results[filing_id] = {
            "md_files": len(md_files),
            "pdf_files": len(pdf_files),
            "exhibits": exhibit_count,
            "total_words": total_words,
            "qa_issues": qa_issues,
            "dir_path": str(dir_path),
        }

    return results


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: Compute EGCP Scores
# ═══════════════════════════════════════════════════════════════════════
def compute_egcp(filing_id, lane, evidence_counts, authority_counts,
                 impeachment_count, golden_data, conn):
    """
    Compute EGCP score (0-100) for a filing.
    E (0-25): Evidence density for the lane
    G (0-25): Grounds/impeachment coverage
    C (0-25): Citation/authority chain density
    P (0-25): Presentation quality (files, exhibits, QA)
    """
    # E — Evidence (0-25)
    ev_count = evidence_counts.get(lane, 0)
    if ev_count >= 10000:
        e_score = 25
    elif ev_count >= 5000:
        e_score = 22
    elif ev_count >= 1000:
        e_score = 18
    elif ev_count >= 500:
        e_score = 14
    elif ev_count >= 100:
        e_score = 10
    elif ev_count >= 10:
        e_score = 5
    else:
        e_score = 2

    # G — Grounds/Impeachment (0-25)
    if impeachment_count >= 1000:
        g_score = 25
    elif impeachment_count >= 500:
        g_score = 22
    elif impeachment_count >= 100:
        g_score = 18
    elif impeachment_count >= 50:
        g_score = 14
    elif impeachment_count >= 10:
        g_score = 10
    elif impeachment_count >= 1:
        g_score = 5
    else:
        g_score = 0

    # C — Citations (0-25)
    auth_count = authority_counts.get(lane, 0)
    # Also count "ALL" lane authorities as supplemental
    auth_count += authority_counts.get("ALL", 0) // 6  # Distribute across 6 lanes
    if auth_count >= 10000:
        c_score = 25
    elif auth_count >= 5000:
        c_score = 22
    elif auth_count >= 1000:
        c_score = 18
    elif auth_count >= 500:
        c_score = 14
    elif auth_count >= 100:
        c_score = 10
    elif auth_count >= 10:
        c_score = 5
    else:
        c_score = 2

    # P — Presentation (0-25)
    gd = golden_data.get(filing_id, {})
    md_files = gd.get("md_files", 0)
    exhibits = gd.get("exhibits", 0)
    qa_issues = gd.get("qa_issues", [])
    total_words = gd.get("total_words", 0)

    p_score = 0
    if md_files >= 5:
        p_score += 8
    elif md_files >= 3:
        p_score += 5
    elif md_files >= 1:
        p_score += 3

    if exhibits >= 10:
        p_score += 8
    elif exhibits >= 5:
        p_score += 5
    elif exhibits >= 1:
        p_score += 3

    if total_words >= 10000:
        p_score += 6
    elif total_words >= 5000:
        p_score += 4
    elif total_words >= 1000:
        p_score += 2

    # QA penalty: -1 per issue (max -5)
    qa_penalty = min(5, len(qa_issues))
    p_score = max(0, p_score - qa_penalty)

    # Cap P at 25
    p_score = min(25, p_score)

    total = e_score + g_score + c_score + p_score
    return {
        "E": e_score, "G": g_score, "C": c_score, "P": p_score,
        "total": total,
        "evidence_count": ev_count,
        "impeachment_count": impeachment_count,
        "authority_count": auth_count,
        "exhibit_count": exhibits,
        "word_count": total_words,
        "qa_issues": len(qa_issues),
        "qa_details": qa_issues[:10],
    }


def determine_status(egcp_total, current_status):
    """Determine filing status based on EGCP score.
    Never regress status (only advance forward)."""
    STATUS_ORDER = ["ingested", "draft", "qa_review", "service_ready", "final_review", "complete"]

    if egcp_total >= 90:
        new_status = "service_ready"
    elif egcp_total >= 70:
        new_status = "qa_review"
    elif egcp_total >= 40:
        new_status = "draft"
    else:
        new_status = "ingested"

    # Never regress
    cur_idx = STATUS_ORDER.index(current_status) if current_status in STATUS_ORDER else 0
    new_idx = STATUS_ORDER.index(new_status) if new_status in STATUS_ORDER else 0

    if new_idx > cur_idx:
        return new_status
    return current_status


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: Populate Bates Registry
# ═══════════════════════════════════════════════════════════════════════
def populate_bates_registry(conn, golden_data):
    """Scan GOLDEN_SET exhibits and assign Bates numbers to bates_registry."""
    # Check current count
    current_count = safe_count(conn, "SELECT COUNT(*) FROM bates_registry")
    print(f"\n{'='*60}")
    print(f"PHASE 4: Bates Registry Population")
    print(f"  Current rows: {current_count}")

    bates_entries = []
    bates_counter = {}  # per-lane counter

    for dir_name, filing_id in GOLDEN_DIR_MAP.items():
        dir_path = GOLDEN_SET / dir_name
        if not dir_path.exists():
            continue

        lane = FILING_LANE_MAP.get(filing_id, "X")

        # Scan exhibits
        for subdir in ["EXHIBITS", "APPENDIX"]:
            exhibit_dir = dir_path / subdir
            if not exhibit_dir.exists():
                continue

            for exhibit_file in sorted(exhibit_dir.iterdir()):
                if exhibit_file.is_file():
                    # Initialize counter for this lane
                    if lane not in bates_counter:
                        bates_counter[lane] = current_count + 1

                    bates_num = f"PIGORS-{lane}-{bates_counter[lane]:06d}"
                    bates_counter[lane] += 1

                    # Determine exhibit ID from filename
                    exhibit_id = exhibit_file.stem
                    document_id = str(exhibit_file)

                    bates_entries.append((
                        bates_num,
                        exhibit_id,
                        1,  # page_number (first page)
                        document_id,
                        filing_id,
                    ))

        # Also scan PDFs
        pdf_dir = dir_path / "PDF"
        if pdf_dir.exists():
            for pdf_file in sorted(pdf_dir.glob("*.pdf")):
                if lane not in bates_counter:
                    bates_counter[lane] = current_count + 1

                bates_num = f"PIGORS-{lane}-{bates_counter[lane]:06d}"
                bates_counter[lane] += 1

                bates_entries.append((
                    bates_num,
                    pdf_file.stem,
                    1,
                    str(pdf_file),
                    filing_id,
                ))

    # Insert into bates_registry
    if bates_entries:
        conn.executemany("""
            INSERT OR IGNORE INTO bates_registry
            (bates_number, exhibit_id, page_number, document_id, filing_id)
            VALUES (?, ?, ?, ?, ?)
        """, bates_entries)
        conn.commit()

    new_count = safe_count(conn, "SELECT COUNT(*) FROM bates_registry")
    inserted = new_count - current_count
    print(f"  Inserted: {inserted} new Bates entries")
    print(f"  Total now: {new_count}")
    print(f"  Lanes covered: {sorted(bates_counter.keys())}")

    return inserted


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: Update filing_readiness Table
# ═══════════════════════════════════════════════════════════════════════
def update_filing_readiness(conn, all_scores):
    """Update filing_readiness with computed EGCP scores and status."""
    updated = 0
    for filing_id, score_data in all_scores.items():
        egcp = score_data["egcp"]
        new_status = score_data["new_status"]

        conn.execute("""
            UPDATE filing_readiness SET
                readiness_score = ?,
                exhibit_count = ?,
                authority_count = ?,
                word_count = ?,
                placeholder_count = ?,
                status = ?,
                updated_at = datetime('now')
            WHERE filing_id = ?
        """, (
            egcp["total"],
            egcp["exhibit_count"],
            egcp["authority_count"],
            egcp["word_count"],
            egcp["qa_issues"],
            new_status,
            filing_id,
        ))

        # Also try matching by vehicle_name patterns
        if conn.execute("SELECT changes()").fetchone()[0] == 0:
            # Try partial match on vehicle_name
            conn.execute("""
                UPDATE filing_readiness SET
                    readiness_score = ?,
                    exhibit_count = ?,
                    authority_count = ?,
                    word_count = ?,
                    placeholder_count = ?,
                    status = ?,
                    updated_at = datetime('now')
                WHERE filing_id = ? OR vehicle_name LIKE '%' || ? || '%'
            """, (
                egcp["total"],
                egcp["exhibit_count"],
                egcp["authority_count"],
                egcp["word_count"],
                egcp["qa_issues"],
                new_status,
                filing_id, filing_id,
            ))

        rows_affected = conn.execute("SELECT changes()").fetchone()[0]
        updated += rows_affected

    conn.commit()
    return updated


def update_filing_packages(conn, all_scores):
    """Update filing_packages status based on EGCP scores."""
    updated = 0
    for filing_id, score_data in all_scores.items():
        new_status = score_data["new_status"]

        conn.execute("""
            UPDATE filing_packages SET status = ?
            WHERE filing_id = ? AND status = 'ingested'
        """, (new_status, filing_id))

        rows_affected = conn.execute("SELECT changes()").fetchone()[0]
        updated += rows_affected

    conn.commit()
    return updated


# ═══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  WAVE 1: FILING PIPELINE ADVANCEMENT ENGINE")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = connect_db()

    # ── Phase 1: Evidence & Authority Counts ──────────────────────────
    print(f"\n{'='*60}")
    print("PHASE 1: Evidence & Authority Intelligence")
    evidence_counts = compute_evidence_counts(conn)
    authority_counts = compute_authority_counts(conn)

    print(f"  Evidence lanes: {len(evidence_counts)}")
    for lane in sorted(evidence_counts, key=evidence_counts.get, reverse=True)[:8]:
        print(f"    {lane}: {evidence_counts[lane]:>8,} quotes")

    print(f"  Authority lanes: {len(authority_counts)}")
    for lane in sorted(authority_counts, key=authority_counts.get, reverse=True)[:8]:
        print(f"    {lane}: {authority_counts[lane]:>8,} chains")

    # ── Phase 2: Scan GOLDEN_SET ──────────────────────────────────────
    print(f"\n{'='*60}")
    print("PHASE 2: GOLDEN_SET Quality Scan")
    golden_data = scan_golden_set()
    for fid, gd in sorted(golden_data.items()):
        qa_flag = f" ⚠ {len(gd['qa_issues'])} QA issues" if gd.get("qa_issues") else " ✅"
        print(f"  {fid}: {gd['md_files']} md, {gd['pdf_files']} pdf, "
              f"{gd['exhibits']} exhibits, {gd['total_words']:,} words{qa_flag}")

    # ── Phase 3: Compute EGCP Scores ──────────────────────────────────
    print(f"\n{'='*60}")
    print("PHASE 3: EGCP Score Computation")

    # Get current filing_readiness data
    filings = conn.execute("""
        SELECT filing_id, vehicle_name, status, readiness_score, lane
        FROM filing_readiness
    """).fetchall()

    all_scores = {}
    for filing_id, vehicle_name, current_status, current_score, db_lane in filings:
        lane = db_lane or FILING_LANE_MAP.get(filing_id, "A")
        impeachment_count = compute_impeachment_counts(conn, filing_id)

        egcp = compute_egcp(
            filing_id, lane, evidence_counts, authority_counts,
            impeachment_count, golden_data, conn
        )

        new_status = determine_status(egcp["total"], current_status)
        status_change = f" → {new_status}" if new_status != current_status else ""

        all_scores[filing_id] = {
            "vehicle_name": vehicle_name,
            "lane": lane,
            "current_status": current_status,
            "new_status": new_status,
            "egcp": egcp,
        }

        print(f"  {filing_id:12s} │ E={egcp['E']:2d} G={egcp['G']:2d} "
              f"C={egcp['C']:2d} P={egcp['P']:2d} │ TOTAL={egcp['total']:3d} │ "
              f"{current_status}{status_change}")

    # ── Phase 4: Populate Bates Registry ──────────────────────────────
    bates_inserted = populate_bates_registry(conn, golden_data)

    # ── Phase 5: Update Database ──────────────────────────────────────
    print(f"\n{'='*60}")
    print("PHASE 5: Database Updates")

    readiness_updated = update_filing_readiness(conn, all_scores)
    print(f"  filing_readiness rows updated: {readiness_updated}")

    packages_updated = update_filing_packages(conn, all_scores)
    print(f"  filing_packages rows advanced: {packages_updated}")

    # ── Verification ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("VERIFICATION: Post-Update Status")

    rows = conn.execute("""
        SELECT filing_id, vehicle_name, status, readiness_score,
               exhibit_count, authority_count, word_count, placeholder_count
        FROM filing_readiness
        ORDER BY readiness_score DESC
    """).fetchall()

    print(f"\n  {'Filing':<14s} {'Status':<15s} {'Score':>5s} {'Exh':>5s} "
          f"{'Auth':>7s} {'Words':>7s} {'QA':>4s}")
    print(f"  {'─'*14} {'─'*15} {'─'*5} {'─'*5} {'─'*7} {'─'*7} {'─'*4}")

    status_counts = {}
    for fid, vname, status, score, exh, auth, words, qa in rows:
        status_counts[status] = status_counts.get(status, 0) + 1
        print(f"  {fid:<14s} {status:<15s} {score:>5.0f} {exh:>5d} "
              f"{auth:>7d} {words:>7d} {qa:>4d}")

    print(f"\n  Status Distribution:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"    {status}: {count}")

    # Bates registry verification
    bates_total = safe_count(conn, "SELECT COUNT(*) FROM bates_registry")
    bates_by_filing = conn.execute("""
        SELECT filing_id, COUNT(*) as cnt
        FROM bates_registry
        GROUP BY filing_id
        ORDER BY filing_id
    """).fetchall()

    print(f"\n  Bates Registry: {bates_total} total entries")
    for fid, cnt in bates_by_filing:
        print(f"    {fid}: {cnt} stamped")

    # ── Summary Report ────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("  WAVE 1 PIPELINE ADVANCEMENT — SUMMARY")
    print(f"{'='*70}")

    total_filings = len(all_scores)
    advanced = sum(1 for s in all_scores.values() if s["new_status"] != s["current_status"])
    avg_egcp = sum(s["egcp"]["total"] for s in all_scores.values()) / max(1, total_filings)

    print(f"  Filings scored:     {total_filings}")
    print(f"  Filings advanced:   {advanced}")
    print(f"  Average EGCP:       {avg_egcp:.1f}/100")
    print(f"  Bates entries:      {bates_total} (added {bates_inserted})")
    print(f"  Total QA issues:    {sum(s['egcp']['qa_issues'] for s in all_scores.values())}")

    # Compute separation days dynamically
    sep_date = date(2025, 7, 29)
    days = (date.today() - sep_date).days
    print(f"\n  ⏱ Father-son separation: {days} days ({days//7} weeks)")
    print(f"  ⚡ Every filing advanced = one step closer to reunion")

    conn.close()

    # Save report to file
    report_path = Path(r"D:\LitigationOS_tmp\pipeline_advancement_report.json")
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_filings": total_filings,
        "filings_advanced": advanced,
        "average_egcp": round(avg_egcp, 1),
        "bates_entries": bates_total,
        "separation_days": days,
        "scores": {
            fid: {
                "vehicle": s["vehicle_name"],
                "lane": s["lane"],
                "old_status": s["current_status"],
                "new_status": s["new_status"],
                "egcp": s["egcp"],
            }
            for fid, s in all_scores.items()
        },
    }
    report_path.write_text(json.dumps(report, indent=2, default=str))
    print(f"\n  Report saved: {report_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
