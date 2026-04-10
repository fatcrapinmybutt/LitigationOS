"""
Harvest Engine — Report Generator v1.0

Generates comprehensive Markdown harvest reports to 04_ANALYSIS/:
  1. Before/after row count snapshots for key tables
  2. Full harvest session reports with lane breakdown, adversary/authority stats
  3. Drive-specific evidence density reports

No module-level side effects. No stdout clobbering. Proper PRAGMAs (Rule 18).
Schema-verify (Rule 16). Type hints, logging, pathlib throughout.
"""

import logging
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
_DEFAULT_OUTPUT = Path(r"C:\Users\andre\LitigationOS\04_ANALYSIS")

# Tables to snapshot for before/after comparison
_SNAPSHOT_TABLES = (
    "evidence_quotes",
    "timeline_events",
    "impeachment_matrix",
    "contradiction_map",
    "judicial_violations",
    "authority_chains_v2",
    "documents",
    "adversary_encyclopedia",
    "topic_encyclopedia",
)

# Lane display names
_LANE_NAMES = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Federal (42 USC §1983)",
    "D": "PPO (2023-5907-PP)",
    "E": "Judicial Misconduct",
    "F": "Appellate (COA 366810)",
    "CRIMINAL": "Criminal (2025-25245676SM)",
}


def _connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open DB connection with mandatory PRAGMAs (Rule 18)."""
    path = Path(db_path) if db_path else _DEFAULT_DB
    conn = sqlite3.connect(str(path), timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if a table exists in the database."""
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return row[0] > 0


def _get_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Schema-verify per Rule 16."""
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row["name"] for row in rows}
    except (sqlite3.OperationalError, KeyError):
        try:
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            return {row[1] for row in rows}
        except sqlite3.OperationalError:
            return set()


def _safe_count(conn: sqlite3.Connection, table: str) -> int:
    """Safely count rows in a table, returning 0 if table doesn't exist."""
    if not _table_exists(conn, table):
        return 0
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError as exc:
        logger.warning("Could not count rows in %s: %s", table, exc)
        return 0


def get_before_counts(db_path: Optional[str] = None) -> dict[str, int]:
    """Snapshot row counts for key tables BEFORE a harvest run.

    Uses a single consolidated query with subqueries for efficiency.

    Args:
        db_path: Path to litigation_context.db.

    Returns:
        Dict mapping table name to row count.
    """
    conn = _connect(db_path)
    try:
        # Build consolidated COUNT query for all existing tables
        existing_tables = [t for t in _SNAPSHOT_TABLES if _table_exists(conn, t)]
        counts: dict[str, int] = {}

        if existing_tables:
            # Single query with subqueries for all tables
            subqueries = ", ".join(
                f"(SELECT COUNT(*) FROM [{t}]) AS [{t}]" for t in existing_tables
            )
            try:
                row = conn.execute(f"SELECT {subqueries}").fetchone()
                for i, table in enumerate(existing_tables):
                    counts[table] = row[i] if row else 0
            except sqlite3.OperationalError:
                # Fallback to individual counts if consolidated query fails
                for table in existing_tables:
                    counts[table] = _safe_count(conn, table)

        # Add zero for any tables that don't exist
        for table in _SNAPSHOT_TABLES:
            if table not in counts:
                counts[table] = 0

        counts["snapshot_time"] = 0  # placeholder for timestamp serialization
        logger.info("Before-counts snapshot: %s", {k: v for k, v in counts.items() if k != "snapshot_time"})
        return counts

    except Exception as exc:
        logger.error("get_before_counts failed: %s", exc, exc_info=True)
        return {t: 0 for t in _SNAPSHOT_TABLES}
    finally:
        conn.close()


def get_after_counts(db_path: Optional[str] = None) -> dict[str, int]:
    """Snapshot row counts for key tables AFTER a harvest run.

    Identical to get_before_counts — called at a different point in time.

    Args:
        db_path: Path to litigation_context.db.

    Returns:
        Dict mapping table name to row count.
    """
    return get_before_counts(db_path)


def generate_harvest_report(db_path: Optional[str] = None,
                            harvest_stats: Optional[dict[str, Any]] = None,
                            output_dir: Optional[str] = None,
                            ) -> str:
    """Generate a comprehensive Markdown harvest report.

    Creates a detailed report with before/after counts, lane breakdown,
    adversary mentions, authority findings, key quotes, gap analysis,
    and recommendations.

    Args:
        db_path: Path to litigation_context.db.
        harvest_stats: Dict containing harvest session statistics. Expected keys:
            - session_id: str
            - before_counts: dict[str, int]
            - after_counts: dict[str, int]
            - files_processed: int
            - evidence_atoms: int
            - by_lane: dict[str, int]
            - top_adversaries: list[dict] (optional)
            - top_authorities: list[dict] (optional)
            - contradictions: list[dict] (optional)
            - errors: list[str] (optional)
            - drive: str (optional)
            - duration_seconds: float (optional)
        output_dir: Directory for the report file. Default: 04_ANALYSIS/.

    Returns:
        Absolute path to the generated report file.
    """
    if harvest_stats is None:
        harvest_stats = {}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = harvest_stats.get("session_id", f"harvest_{timestamp}")
    out_path = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
    out_path.mkdir(parents=True, exist_ok=True)
    report_file = out_path / f"HARVEST_REPORT_{timestamp}.md"

    # Collect data from harvest_stats
    before = harvest_stats.get("before_counts", {})
    after = harvest_stats.get("after_counts", {})
    files_processed = harvest_stats.get("files_processed", 0)
    evidence_atoms = harvest_stats.get("evidence_atoms", 0)
    by_lane = harvest_stats.get("by_lane", {})
    contradictions = harvest_stats.get("contradictions", [])
    errors = harvest_stats.get("errors", [])
    drive = harvest_stats.get("drive", "unknown")
    duration = harvest_stats.get("duration_seconds", 0.0)

    # If before/after counts weren't provided, query current state
    conn = None
    if not after:
        try:
            conn = _connect(db_path)
            for table in _SNAPSHOT_TABLES:
                after[table] = _safe_count(conn, table)
        except Exception as exc:
            logger.error("Failed to get after-counts for report: %s", exc)
        finally:
            if conn:
                conn.close()
                conn = None

    # Query additional intelligence from the DB for the report
    top_adversaries = harvest_stats.get("top_adversaries", [])
    top_authorities = harvest_stats.get("top_authorities", [])
    key_quotes = harvest_stats.get("key_quotes", [])

    if not top_adversaries or not top_authorities or not key_quotes:
        try:
            conn = _connect(db_path)
            if not top_adversaries:
                top_adversaries = _query_top_adversaries(conn)
            if not top_authorities:
                top_authorities = _query_top_authorities(conn)
            if not key_quotes:
                key_quotes = _query_key_quotes(conn)
        except Exception as exc:
            logger.error("Failed to query intelligence for report: %s", exc)
        finally:
            if conn:
                conn.close()

    # Build the report
    now = datetime.now()
    sep_days = (now.date() - datetime(2025, 7, 29).date()).days

    lines: list[str] = []
    lines.append(f"# Harvest Intelligence Report")
    lines.append("")
    lines.append(f"**Session:** `{session_id}`  ")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Drive/Source:** {drive}  ")
    lines.append(f"**Duration:** {duration:.1f}s  ")
    lines.append(f"**Father-Son Separation:** {sep_days} days (since Jul 29, 2025)  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Before/After Row Counts
    lines.append("## 1. Database Impact — Before/After Row Counts")
    lines.append("")
    lines.append("| Table | Before | After | Δ New |")
    lines.append("|-------|--------|-------|-------|")
    total_delta = 0
    for table in _SNAPSHOT_TABLES:
        b = before.get(table, 0)
        a = after.get(table, 0)
        delta = a - b
        total_delta += delta
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        lines.append(f"| `{table}` | {b:,} | {a:,} | **{delta_str}** |")
    lines.append(f"| **TOTAL** | | | **+{total_delta}** |")
    lines.append("")

    # Section 2: Processing Summary
    lines.append("## 2. Processing Summary")
    lines.append("")
    lines.append(f"- **Files Processed:** {files_processed:,}")
    lines.append(f"- **Evidence Atoms Extracted:** {evidence_atoms:,}")
    lines.append(f"- **Contradictions Detected:** {len(contradictions)}")
    lines.append(f"- **Errors Encountered:** {len(errors)}")
    lines.append("")

    # Section 3: Lane Breakdown
    lines.append("## 3. Findings by Litigation Lane")
    lines.append("")
    if by_lane:
        lines.append("| Lane | Description | Evidence Count |")
        lines.append("|------|-------------|----------------|")
        for lane, count in sorted(by_lane.items(), key=lambda x: x[1], reverse=True):
            lane_desc = _LANE_NAMES.get(lane, lane)
            lines.append(f"| **{lane}** | {lane_desc} | {count:,} |")
    else:
        lines.append("*No lane-specific breakdown available for this harvest.*")
    lines.append("")

    # Section 4: Top Adversary Mentions
    lines.append("## 4. Top Adversary Mentions")
    lines.append("")
    if top_adversaries:
        lines.append("| # | Adversary | Evidence Count | Threat Level |")
        lines.append("|---|-----------|----------------|--------------|")
        for i, adv in enumerate(top_adversaries[:15], 1):
            name = adv.get("person_name", "Unknown")
            count = adv.get("evidence_count", 0)
            threat = adv.get("threat_level", "—")
            lines.append(f"| {i} | {name} | {count:,} | {threat} |")
    else:
        lines.append("*No adversary data available.*")
    lines.append("")

    # Section 5: Top Authorities Found
    lines.append("## 5. Top Authorities Found")
    lines.append("")
    if top_authorities:
        lines.append("| # | Citation | Occurrences | Source Type |")
        lines.append("|---|----------|-------------|-------------|")
        for i, auth in enumerate(top_authorities[:15], 1):
            citation = auth.get("primary_citation", "Unknown")
            count = auth.get("count", 0)
            src_type = auth.get("source_type", "—")
            lines.append(f"| {i} | `{citation}` | {count:,} | {src_type} |")
    else:
        lines.append("*No authority data available.*")
    lines.append("")

    # Section 6: Key Quotes Discovered
    lines.append("## 6. Key Quotes Discovered (Top 10 by Impeachment Value)")
    lines.append("")
    if key_quotes:
        for i, kq in enumerate(key_quotes[:10], 1):
            quote = kq.get("quote_text", "")[:300]
            source = kq.get("source_file", "unknown")
            imp_val = kq.get("impeachment_value", 0)
            category = kq.get("category", "—")
            lines.append(f"### {i}. [{category}] (Impeachment: {imp_val}/10)")
            lines.append(f"> {quote}")
            lines.append(f"")
            lines.append(f"*Source: `{source}`*")
            lines.append("")
    else:
        lines.append("*No high-value quotes found in this harvest.*")
    lines.append("")

    # Section 7: Contradictions Detected
    lines.append("## 7. Contradictions Detected")
    lines.append("")
    if contradictions:
        severity_counts: Counter[str] = Counter()
        for c in contradictions:
            severity_counts[c.get("severity", "unknown")] += 1

        lines.append(f"**Total:** {len(contradictions)} — ")
        sev_parts = [f"{sev}: {cnt}" for sev, cnt in sorted(severity_counts.items())]
        lines.append(", ".join(sev_parts))
        lines.append("")

        for i, c in enumerate(contradictions[:20], 1):
            lines.append(f"**{i}. [{c.get('severity', '?').upper()}] {c.get('actor', 'unknown')} — {c.get('topic', 'unknown')}**")
            lines.append(f"- **A:** {c.get('quote_a', '')[:200]}")
            lines.append(f"- **B:** {c.get('quote_b', '')[:200]}")
            lines.append(f"- Sources: `{c.get('source_a', '?')}` vs `{c.get('source_b', '?')}`")
            lines.append("")
    else:
        lines.append("*No contradictions detected in this harvest.*")
    lines.append("")

    # Section 8: Gap Analysis
    lines.append("## 8. Gap Analysis — What's Still Missing")
    lines.append("")
    gap_items = _compute_gap_analysis(after)
    for gap in gap_items:
        lines.append(f"- {gap}")
    lines.append("")

    # Section 9: Errors
    if errors:
        lines.append("## 9. Errors Encountered")
        lines.append("")
        for err in errors[:50]:
            lines.append(f"- `{err}`")
        lines.append("")

    # Section 10: Recommendations
    lines.append(f"## {'10' if errors else '9'}. Recommendations for Next Harvest")
    lines.append("")
    recommendations = _generate_recommendations(by_lane, contradictions, after, files_processed)
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by LitigationOS Harvest Engine v1.0 at {now.isoformat()}*")

    # Write report
    report_content = "\n".join(lines)
    report_file.write_text(report_content, encoding="utf-8")
    logger.info("Harvest report written to %s (%d lines)", report_file, len(lines))

    return str(report_file)


def generate_drive_report(drive_letter: str,
                          stats: Optional[dict[str, Any]] = None,
                          output_dir: Optional[str] = None,
                          ) -> str:
    """Generate a drive-specific harvest report.

    Shows file type breakdown, evidence density by category, and
    drive-specific statistics.

    Args:
        drive_letter: Drive letter (e.g., 'G', 'I', 'D').
        stats: Dict with drive-specific statistics. Expected keys:
            - total_files: int
            - files_by_type: dict[str, int] (extension -> count)
            - files_by_category: dict[str, int]
            - evidence_density: float (evidence files / total files)
            - total_size_mb: float
            - errors: list[str]
            - duration_seconds: float
        output_dir: Directory for the report file.

    Returns:
        Absolute path to the generated report file.
    """
    if stats is None:
        stats = {}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
    out_path.mkdir(parents=True, exist_ok=True)
    report_file = out_path / f"DRIVE_{drive_letter.upper()}_REPORT_{timestamp}.md"

    total_files = stats.get("total_files", 0)
    files_by_type = stats.get("files_by_type", {})
    files_by_category = stats.get("files_by_category", {})
    evidence_density = stats.get("evidence_density", 0.0)
    total_size_mb = stats.get("total_size_mb", 0.0)
    errors = stats.get("errors", [])
    duration = stats.get("duration_seconds", 0.0)

    now = datetime.now()
    sep_days = (now.date() - datetime(2025, 7, 29).date()).days

    lines: list[str] = []
    lines.append(f"# Drive {drive_letter.upper()}:\\ — Harvest Report")
    lines.append("")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Duration:** {duration:.1f}s  ")
    lines.append(f"**Separation Days:** {sep_days}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- **Total Files Scanned:** {total_files:,}")
    lines.append(f"- **Total Size:** {total_size_mb:,.1f} MB")
    lines.append(f"- **Evidence Density:** {evidence_density:.1%}")
    lines.append(f"- **Errors:** {len(errors)}")
    lines.append("")

    # File Type Breakdown
    lines.append("## File Type Breakdown")
    lines.append("")
    if files_by_type:
        lines.append("| Extension | Count | % of Total |")
        lines.append("|-----------|-------|------------|")
        for ext, count in sorted(files_by_type.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_files * 100) if total_files > 0 else 0
            lines.append(f"| `.{ext}` | {count:,} | {pct:.1f}% |")
    else:
        lines.append("*No file type data available.*")
    lines.append("")

    # Evidence by Category
    lines.append("## Evidence Density by Category")
    lines.append("")
    if files_by_category:
        lines.append("| Category | Files Found | Density |")
        lines.append("|----------|-------------|---------|")
        for cat, count in sorted(files_by_category.items(), key=lambda x: x[1], reverse=True):
            density = "█" * min(count // 5, 20)
            lines.append(f"| {cat} | {count:,} | {density} |")
    else:
        lines.append("*No category classification data available.*")
    lines.append("")

    # Drive Priority Assessment
    lines.append("## Drive Priority Assessment")
    lines.append("")
    _DRIVE_DESCRIPTIONS = {
        "C": "Primary OS + active databases (NVMe SSD)",
        "D": "DB archives, evidence trove (USB)",
        "F": "Backups, index files (USB Flash 58 GB)",
        "G": "Evidence storage (USB Flash 58 GB)",
        "I": "Sorted evidence, organized files (SD Card ~30 GB)",
        "J": "Centralization target (USB 2 TB, exFAT)",
    }
    desc = _DRIVE_DESCRIPTIONS.get(drive_letter.upper(), "Unknown drive")
    lines.append(f"**{drive_letter.upper()}:\\** — {desc}")
    lines.append("")

    if evidence_density > 0.5:
        lines.append("⚡ **HIGH DENSITY** — This drive is evidence-rich. Priority: CRITICAL")
    elif evidence_density > 0.2:
        lines.append("📊 **MEDIUM DENSITY** — Moderate evidence content. Priority: HIGH")
    elif evidence_density > 0.05:
        lines.append("📁 **LOW DENSITY** — Sparse evidence. Priority: MEDIUM")
    else:
        lines.append("📦 **MINIMAL** — Few evidence files detected. Priority: LOW")
    lines.append("")

    # Errors
    if errors:
        lines.append("## Errors")
        lines.append("")
        for err in errors[:30]:
            lines.append(f"- `{err}`")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by LitigationOS Harvest Engine v1.0 at {now.isoformat()}*")

    report_content = "\n".join(lines)
    report_file.write_text(report_content, encoding="utf-8")
    logger.info("Drive report written to %s (%d lines)", report_file, len(lines))

    return str(report_file)


def _query_top_adversaries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Query the adversary_encyclopedia for top adversaries by evidence count."""
    if not _table_exists(conn, "adversary_encyclopedia"):
        return []

    cols = _get_columns(conn, "adversary_encyclopedia")
    required = {"person_name", "evidence_count"}
    if not required.issubset(cols):
        return []

    has_threat = "threat_level" in cols
    select_cols = "person_name, evidence_count"
    if has_threat:
        select_cols += ", threat_level"

    try:
        rows = conn.execute(
            f"SELECT {select_cols} FROM adversary_encyclopedia "
            "ORDER BY evidence_count DESC LIMIT 15"
        ).fetchall()
        results = []
        for row in rows:
            entry: dict[str, Any] = {
                "person_name": row["person_name"],
                "evidence_count": row["evidence_count"] or 0,
            }
            if has_threat:
                entry["threat_level"] = row["threat_level"] or "—"
            results.append(entry)
        return results
    except sqlite3.OperationalError as exc:
        logger.error("Failed to query adversary_encyclopedia: %s", exc)
        return []


def _query_top_authorities(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Query authority_chains_v2 for most-cited authorities."""
    if not _table_exists(conn, "authority_chains_v2"):
        return []

    cols = _get_columns(conn, "authority_chains_v2")
    if "primary_citation" not in cols:
        return []

    has_source_type = "source_type" in cols
    try:
        if has_source_type:
            rows = conn.execute(
                "SELECT primary_citation, COUNT(*) as cnt, "
                "MAX(source_type) as source_type "
                "FROM authority_chains_v2 "
                "GROUP BY primary_citation ORDER BY cnt DESC LIMIT 15"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT primary_citation, COUNT(*) as cnt "
                "FROM authority_chains_v2 "
                "GROUP BY primary_citation ORDER BY cnt DESC LIMIT 15"
            ).fetchall()

        results = []
        for row in rows:
            entry: dict[str, Any] = {
                "primary_citation": row["primary_citation"],
                "count": row["cnt"],
            }
            if has_source_type:
                entry["source_type"] = row["source_type"] or "—"
            results.append(entry)
        return results
    except sqlite3.OperationalError as exc:
        logger.error("Failed to query authority_chains_v2: %s", exc)
        return []


def _query_key_quotes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Query impeachment_matrix for highest-value quotes."""
    if not _table_exists(conn, "impeachment_matrix"):
        return []

    cols = _get_columns(conn, "impeachment_matrix")
    required = {"quote_text", "impeachment_value"}
    if not required.issubset(cols):
        return []

    has_source = "source_file" in cols
    has_category = "category" in cols
    select_parts = ["quote_text", "impeachment_value"]
    if has_source:
        select_parts.append("source_file")
    if has_category:
        select_parts.append("category")

    try:
        rows = conn.execute(
            f"SELECT {', '.join(select_parts)} FROM impeachment_matrix "
            "WHERE quote_text IS NOT NULL AND quote_text != '' "
            "ORDER BY impeachment_value DESC LIMIT 10"
        ).fetchall()

        results = []
        for row in rows:
            entry: dict[str, Any] = {
                "quote_text": row["quote_text"],
                "impeachment_value": row["impeachment_value"] or 0,
            }
            if has_source:
                entry["source_file"] = row["source_file"] or "unknown"
            if has_category:
                entry["category"] = row["category"] or "—"
            results.append(entry)
        return results
    except sqlite3.OperationalError as exc:
        logger.error("Failed to query impeachment_matrix: %s", exc)
        return []


def _compute_gap_analysis(after_counts: dict[str, int]) -> list[str]:
    """Identify evidence gaps based on current table row counts."""
    gaps: list[str] = []

    eq_count = after_counts.get("evidence_quotes", 0)
    if eq_count < 1000:
        gaps.append(f"⚠️ evidence_quotes has only {eq_count:,} rows — needs aggressive harvesting")

    im_count = after_counts.get("impeachment_matrix", 0)
    if im_count < 500:
        gaps.append(f"⚠️ impeachment_matrix has only {im_count:,} rows — run impeachment extraction pass")

    cm_count = after_counts.get("contradiction_map", 0)
    if cm_count < 100:
        gaps.append(f"⚠️ contradiction_map has only {cm_count:,} rows — cross-intel pass needed")

    jv_count = after_counts.get("judicial_violations", 0)
    if jv_count < 500:
        gaps.append(f"⚠️ judicial_violations has only {jv_count:,} rows — needs judicial evidence sweep")

    ac_count = after_counts.get("authority_chains_v2", 0)
    if ac_count < 1000:
        gaps.append(f"⚠️ authority_chains_v2 has only {ac_count:,} rows — needs authority harvest")

    doc_count = after_counts.get("documents", 0)
    if doc_count < 100:
        gaps.append(f"⚠️ documents index has only {doc_count:,} entries — many source files may be un-indexed")

    ae_count = after_counts.get("adversary_encyclopedia", 0)
    if ae_count < 5:
        gaps.append("⚠️ adversary_encyclopedia is sparse — needs profiling pass for key adversaries")

    te_count = after_counts.get("topic_encyclopedia", 0)
    if te_count < 5:
        gaps.append("⚠️ topic_encyclopedia is sparse — needs topic mapping pass")

    if not gaps:
        gaps.append("✅ All tables have substantial data — no critical gaps detected")

    return gaps


def _generate_recommendations(by_lane: dict[str, int],
                              contradictions: list[dict[str, Any]],
                              after_counts: dict[str, int],
                              files_processed: int,
                              ) -> list[str]:
    """Generate actionable recommendations for the next harvest."""
    recs: list[str] = []

    # Lane coverage recommendations
    all_lanes = {"A", "B", "C", "D", "E", "F", "CRIMINAL"}
    covered_lanes = set(by_lane.keys()) if by_lane else set()
    missing_lanes = all_lanes - covered_lanes
    if missing_lanes:
        lane_strs = [f"{l} ({_LANE_NAMES.get(l, l)})" for l in sorted(missing_lanes)]
        recs.append(f"🔍 **Missing lanes:** {', '.join(lane_strs)} — target these in next harvest")

    # Contradiction follow-up
    critical = [c for c in contradictions if c.get("severity") in ("critical", "high")]
    if critical:
        recs.append(f"⚡ **{len(critical)} critical/high contradictions** detected — review for impeachment use")

    # Volume recommendations
    if files_processed < 100:
        recs.append("📁 Low file count — consider scanning additional drives (I:\\, D:\\, G:\\)")
    elif files_processed > 5000:
        recs.append("✅ High-volume harvest — focus next run on quality over quantity (deep analysis)")

    # Table-specific recommendations
    eq = after_counts.get("evidence_quotes", 0)
    im = after_counts.get("impeachment_matrix", 0)
    ratio = im / eq if eq > 0 else 0
    if ratio < 0.02:
        recs.append(f"📊 Impeachment-to-evidence ratio is low ({ratio:.1%}) — run impeachment extraction")

    # Critical exhibits check
    recs.append("🎯 **Priority:** Locate NS2505044, HealthWest eval, Officer Randall report, AppClose 305+ incidents")

    # Drive scanning recommendation
    recs.append("💾 **Next drives:** I:\\ (sorted evidence), D:\\ (DB archives), J:\\ (2TB cold storage)")

    if not recs:
        recs.append("✅ Harvest pipeline is healthy — continue regular scanning schedule")

    return recs
