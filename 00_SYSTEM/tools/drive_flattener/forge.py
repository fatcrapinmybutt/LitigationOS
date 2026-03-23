"""OMEGA-FLATTEN forge — condense, merge, and synthesize evidence products.

LitigationOS Event Horizon Δ∞
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .classifier import read_content_preview
from .config import MEEK_PATTERNS, PROGRESS_INTERVAL


def forge_drive(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
) -> Dict[str, Any]:
    """Run all forge operations on *drive*.

    1. Evidence consolidation — group high-value files by MEEK lane
    2. Timeline extraction — scan for date+event patterns
    3. Entity consolidation — merge entity extractions into master index
    4. Statistics generation — comprehensive drive analysis report

    Returns
    -------
    dict with keys: outputs_created, evidence_packages, timeline_events, entities_total.
    """
    t0 = time.perf_counter()
    index_dir = os.path.join(f"{drive}:\\_INDEX")
    os.makedirs(index_dir, exist_ok=True)

    outputs_created = 0

    # 1. Evidence by lane
    print("  [FORGE] Evidence consolidation by MEEK lane …")
    evidence_result = _forge_evidence_by_lane(conn, drive, index_dir)
    outputs_created += 1

    # 2. Timeline extraction
    print("  [FORGE] Timeline extraction …")
    timeline_result = _forge_timeline(conn, drive, index_dir)
    outputs_created += 1

    # 3. Entity index
    print("  [FORGE] Entity consolidation …")
    entity_result = _forge_entity_index(conn, drive, index_dir)
    outputs_created += 1

    # 4. Drive analysis report
    print("  [FORGE] Generating drive analysis report …")
    report_result = _forge_drive_report(conn, drive, index_dir, session_id)
    outputs_created += 1

    # 5. Top evidence
    print("  [FORGE] Top evidence compilation …")
    top_result = _forge_top_evidence(conn, drive, index_dir)
    outputs_created += 1

    # Record forge outputs in DB
    _record_outputs(conn, drive, index_dir, {
        "EVIDENCE_BY_LANE.json": ("evidence_by_lane", evidence_result.get("lane_summary", "")),
        "TIMELINE.csv": ("timeline", f"{timeline_result.get('events', 0)} events"),
        "ENTITY_INDEX.json": ("entity_index", f"{entity_result.get('entities_total', 0)} entities"),
        "DRIVE_ANALYSIS_REPORT.md": ("drive_report", "comprehensive analysis"),
        "TOP_EVIDENCE.md": ("top_evidence", f"{top_result.get('count', 0)} files"),
    })

    elapsed = time.perf_counter() - t0
    print(
        f"  [FORGE] COMPLETE — {outputs_created} outputs created in {elapsed:.1f}s",
    )

    return {
        "outputs_created": outputs_created,
        "evidence_packages": evidence_result.get("lanes_with_files", 0),
        "timeline_events": timeline_result.get("events", 0),
        "entities_total": entity_result.get("entities_total", 0),
        "elapsed_seconds": round(elapsed, 2),
    }


# ---------------------------------------------------------------------------
# Forge 1: Evidence by MEEK lane
# ---------------------------------------------------------------------------

def _forge_evidence_by_lane(
    conn: sqlite3.Connection,
    drive: str,
    index_dir: str,
) -> Dict[str, Any]:
    """Group evidence files by MEEK lane."""
    rows = conn.execute(
        """SELECT ff.id, ff.original_path, ff.new_path, ff.folder, ff.filename,
                  ff.litigation_score, ff.meek_lane, ff.evidence_value, ff.size_bytes,
                  fa.document_type, fa.key_quotes
             FROM flat_files ff
             LEFT JOIN file_analysis fa ON fa.file_id = ff.id
            WHERE ff.drive = ? AND ff.is_duplicate = 0
                  AND ff.litigation_score > 0
            ORDER BY ff.meek_lane, ff.litigation_score DESC""",
        (drive,),
    ).fetchall()

    lanes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    unassigned: List[Dict[str, Any]] = []

    for row in rows:
        fid, orig, newp, folder, fname, lscore, lane, evalue, sz, dtype, quotes = row
        entry = {
            "file_id": fid,
            "path": newp or orig,
            "folder": folder,
            "filename": fname,
            "litigation_score": lscore,
            "evidence_value": evalue,
            "size_bytes": sz,
            "document_type": dtype or "unknown",
            "key_quotes": json.loads(quotes) if quotes else [],
        }
        if lane:
            lanes[lane].append(entry)
        else:
            unassigned.append(entry)

    # Build output with lane labels
    output: Dict[str, Any] = {}
    for meek_key, meek_info in MEEK_PATTERNS.items():
        lane_letter = meek_info["lane"]
        label = meek_info["label"]
        output[lane_letter] = {
            "label": label,
            "meek_key": meek_key,
            "file_count": len(lanes.get(lane_letter, [])),
            "files": lanes.get(lane_letter, [])[:200],  # cap per lane
        }

    if unassigned:
        output["UNASSIGNED"] = {
            "label": "No MEEK lane detected",
            "file_count": len(unassigned),
            "files": unassigned[:200],
        }

    out_path = os.path.join(index_dir, "EVIDENCE_BY_LANE.json")
    _write_json(out_path, output)

    lanes_with = sum(1 for v in output.values() if v.get("file_count", 0) > 0)
    lane_summary = ", ".join(
        f"{k}: {v['file_count']}" for k, v in output.items() if v.get("file_count", 0) > 0
    )

    return {"lanes_with_files": lanes_with, "lane_summary": lane_summary}


# ---------------------------------------------------------------------------
# Forge 2: Timeline extraction
# ---------------------------------------------------------------------------

_RE_DATE_EVENT = re.compile(
    r"(?:(?:on|dated?|filed?|entered?|signed?|issued?|received?|served?)\s+)?"
    r"((?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}"
    r"|(?:19|20)\d{2}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])"
    r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4})"
    r"\s*[,:\-—–]?\s*(.{10,200}?)(?:\.|$)",
    re.IGNORECASE | re.MULTILINE,
)


def _forge_timeline(
    conn: sqlite3.Connection,
    drive: str,
    index_dir: str,
) -> Dict[str, Any]:
    """Extract date+event patterns from all text files."""
    rows = conn.execute(
        """SELECT ff.id, ff.new_path, ff.original_path, ff.filename, ff.meek_lane
             FROM flat_files ff
            WHERE ff.drive = ? AND ff.is_duplicate = 0
                  AND ff.folder IN ('PDF','DOCX','MD','TXT','HTML','LEGAL','EMAIL')
                  AND ff.size_bytes < 10485760
            ORDER BY ff.litigation_score DESC
            LIMIT 5000""",
        (drive,),
    ).fetchall()

    events: List[Dict[str, str]] = []
    processed = 0

    for fid, newp, orig, fname, lane in rows:
        filepath = newp or orig
        text = read_content_preview(filepath, max_bytes=32768)
        if not text:
            continue

        for match in _RE_DATE_EVENT.finditer(text):
            date_str = match.group(1).strip()
            event_text = match.group(2).strip()
            if len(event_text) < 15:
                continue
            events.append({
                "date": date_str,
                "event": event_text[:300],
                "source_file": fname,
                "source_path": filepath,
                "meek_lane": lane or "",
                "file_id": str(fid),
            })

        processed += 1
        if processed % PROGRESS_INTERVAL == 0:
            print(f"    … {processed:,} files scanned, {len(events):,} events extracted")

    # Sort events by date (best effort — mixed formats)
    events.sort(key=lambda e: e["date"])

    # Write CSV
    out_path = os.path.join(index_dir, "TIMELINE.csv")
    try:
        with open(out_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["date", "event", "source_file", "source_path", "meek_lane", "file_id"],
            )
            writer.writeheader()
            writer.writerows(events)
    except (PermissionError, OSError) as exc:
        print(f"  [FORGE] WARNING: Could not write timeline: {exc}")

    return {"events": len(events), "files_scanned": processed}


# ---------------------------------------------------------------------------
# Forge 3: Entity consolidation
# ---------------------------------------------------------------------------

def _forge_entity_index(
    conn: sqlite3.Connection,
    drive: str,
    index_dir: str,
) -> Dict[str, Any]:
    """Merge entity extractions into a master index."""
    rows = conn.execute(
        """SELECT fa.file_id, fa.entity_names, fa.entity_dates,
                  fa.entity_case_numbers, fa.entity_dollar_amounts,
                  ff.filename, ff.meek_lane
             FROM file_analysis fa
             JOIN flat_files ff ON ff.id = fa.file_id
            WHERE ff.drive = ? AND ff.is_duplicate = 0""",
        (drive,),
    ).fetchall()

    all_names: Dict[str, List[str]] = defaultdict(list)
    all_dates: Dict[str, List[str]] = defaultdict(list)
    all_cases: Dict[str, List[str]] = defaultdict(list)
    all_dollars: Dict[str, List[str]] = defaultdict(list)

    for fid, names_j, dates_j, cases_j, dollars_j, fname, lane in rows:
        source = fname
        for name in _safe_load_list(names_j):
            all_names[name].append(source)
        for date in _safe_load_list(dates_j):
            all_dates[date].append(source)
        for case in _safe_load_list(cases_j):
            all_cases[case].append(source)
        for dollar in _safe_load_list(dollars_j):
            all_dollars[dollar].append(source)

    # Build consolidated index
    index = {
        "names": {
            name: {"count": len(sources), "sources": list(set(sources))[:10]}
            for name, sources in sorted(all_names.items(), key=lambda x: -len(x[1]))[:500]
        },
        "dates": {
            date: {"count": len(sources), "sources": list(set(sources))[:10]}
            for date, sources in sorted(all_dates.items(), key=lambda x: -len(x[1]))[:500]
        },
        "case_numbers": {
            case: {"count": len(sources), "sources": list(set(sources))[:10]}
            for case, sources in sorted(all_cases.items(), key=lambda x: -len(x[1]))[:100]
        },
        "dollar_amounts": {
            dollar: {"count": len(sources), "sources": list(set(sources))[:10]}
            for dollar, sources in sorted(all_dollars.items(), key=lambda x: -len(x[1]))[:200]
        },
        "summary": {
            "unique_names": len(all_names),
            "unique_dates": len(all_dates),
            "unique_case_numbers": len(all_cases),
            "unique_dollar_amounts": len(all_dollars),
            "total_files_with_entities": len(rows),
        },
    }

    out_path = os.path.join(index_dir, "ENTITY_INDEX.json")
    _write_json(out_path, index)

    total = len(all_names) + len(all_dates) + len(all_cases) + len(all_dollars)
    return {"entities_total": total}


# ---------------------------------------------------------------------------
# Forge 4: Drive analysis report
# ---------------------------------------------------------------------------

def _forge_drive_report(
    conn: sqlite3.Connection,
    drive: str,
    index_dir: str,
    session_id: int,
) -> Dict[str, Any]:
    """Generate comprehensive drive analysis report."""
    # Aggregate stats via single query
    agg = conn.execute(
        """SELECT
               (SELECT COUNT(*) FROM flat_files WHERE drive = :d) AS total_files,
               (SELECT COALESCE(SUM(size_bytes), 0) FROM flat_files WHERE drive = :d) AS total_size,
               (SELECT COUNT(*) FROM flat_files WHERE drive = :d AND is_duplicate = 1) AS dupes,
               (SELECT COALESCE(SUM(size_bytes), 0) FROM flat_files WHERE drive = :d AND is_duplicate = 1) AS dupe_size,
               (SELECT COUNT(*) FROM flat_files WHERE drive = :d AND evidence_value = 'high') AS high_ev,
               (SELECT COUNT(*) FROM flat_files WHERE drive = :d AND evidence_value = 'medium') AS med_ev,
               (SELECT COUNT(*) FROM flat_files WHERE drive = :d AND evidence_value = 'low') AS low_ev,
               (SELECT COUNT(*) FROM flat_files WHERE drive = :d AND evidence_value = 'none') AS no_ev
        """,
        {"d": drive},
    ).fetchone()

    total_files, total_size, dupes, dupe_size, high_ev, med_ev, low_ev, no_ev = agg

    # Files by folder
    folder_stats = conn.execute(
        """SELECT folder, COUNT(*) AS cnt, COALESCE(SUM(size_bytes), 0) AS sz
             FROM flat_files
            WHERE drive = ? AND is_duplicate = 0
            GROUP BY folder
            ORDER BY cnt DESC""",
        (drive,),
    ).fetchall()

    # MEEK lane distribution
    lane_stats = conn.execute(
        """SELECT meek_lane, COUNT(*) AS cnt
             FROM flat_files
            WHERE drive = ? AND meek_lane IS NOT NULL AND meek_lane != ''
                  AND is_duplicate = 0
            GROUP BY meek_lane
            ORDER BY cnt DESC""",
        (drive,),
    ).fetchall()

    # Litigation score distribution
    score_dist = conn.execute(
        """SELECT
               CASE
                   WHEN litigation_score >= 8 THEN '8-10 (Critical)'
                   WHEN litigation_score >= 6 THEN '6-8 (High)'
                   WHEN litigation_score >= 4 THEN '4-6 (Medium)'
                   WHEN litigation_score >= 2 THEN '2-4 (Low)'
                   ELSE '0-2 (Minimal)'
               END AS bucket,
               COUNT(*) AS cnt
             FROM flat_files
            WHERE drive = ? AND is_duplicate = 0
            GROUP BY bucket
            ORDER BY bucket DESC""",
        (drive,),
    ).fetchall()

    # Build report
    lines = [
        f"# OMEGA-FLATTEN Drive Analysis Report — {drive}:",
        f"",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Session ID:** {session_id}",
        f"",
        f"## Overview",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total files | {total_files:,} |",
        f"| Total size | {total_size / (1024**3):.2f} GB |",
        f"| Duplicates found | {dupes:,} |",
        f"| Duplicate size | {dupe_size / (1024**2):.1f} MB |",
        f"| High-value evidence | {high_ev:,} |",
        f"| Medium-value evidence | {med_ev:,} |",
        f"| Low-value evidence | {low_ev:,} |",
        f"| Non-evidence | {no_ev:,} |",
        f"",
        f"## Files by Folder",
        f"",
        f"| Folder | Files | Size |",
        f"|--------|-------|------|",
    ]

    for folder, cnt, sz in folder_stats:
        sz_str = f"{sz / (1024**2):.1f} MB" if sz < 1024**3 else f"{sz / (1024**3):.2f} GB"
        lines.append(f"| {folder} | {cnt:,} | {sz_str} |")

    lines.extend([
        f"",
        f"## MEEK Lane Distribution",
        f"",
        f"| Lane | Files |",
        f"|------|-------|",
    ])

    for lane, cnt in lane_stats:
        label = ""
        for mk, mv in MEEK_PATTERNS.items():
            if mv["lane"] == lane:
                label = f" ({mv['label']})"
                break
        lines.append(f"| {lane}{label} | {cnt:,} |")

    lines.extend([
        f"",
        f"## Litigation Score Distribution",
        f"",
        f"| Score Range | Files |",
        f"|-------------|-------|",
    ])

    for bucket, cnt in score_dist:
        lines.append(f"| {bucket} | {cnt:,} |")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by OMEGA-FLATTEN v1.0 — LitigationOS Event Horizon Δ∞*")
    lines.append("")

    out_path = os.path.join(index_dir, "DRIVE_ANALYSIS_REPORT.md")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
    except (PermissionError, OSError) as exc:
        print(f"  [FORGE] WARNING: Could not write report: {exc}")

    return {"total_files": total_files}


# ---------------------------------------------------------------------------
# Forge 5: Top evidence compilation
# ---------------------------------------------------------------------------

def _forge_top_evidence(
    conn: sqlite3.Connection,
    drive: str,
    index_dir: str,
) -> Dict[str, Any]:
    """Compile the top 50 highest-value evidence files."""
    rows = conn.execute(
        """SELECT ff.id, ff.new_path, ff.original_path, ff.filename, ff.folder,
                  ff.litigation_score, ff.evidence_value, ff.meek_lane, ff.size_bytes,
                  fa.document_type, fa.key_quotes, fa.entity_case_numbers
             FROM flat_files ff
             LEFT JOIN file_analysis fa ON fa.file_id = ff.id
            WHERE ff.drive = ? AND ff.is_duplicate = 0
                  AND ff.litigation_score > 0
            ORDER BY ff.litigation_score DESC
            LIMIT 50""",
        (drive,),
    ).fetchall()

    lines = [
        f"# Top Evidence Files — Drive {drive}:",
        f"",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Files listed:** {len(rows)}",
        f"",
    ]

    for rank, row in enumerate(rows, 1):
        fid, newp, orig, fname, folder, lscore, evalue, lane, sz, dtype, quotes_j, cases_j = row
        filepath = newp or orig
        sz_str = f"{sz / 1024:.0f} KB" if sz < 1024 * 1024 else f"{sz / (1024**2):.1f} MB"

        lines.append(f"### {rank}. {fname}")
        lines.append(f"")
        lines.append(f"- **Score:** {lscore}/10 | **Value:** {evalue} | **Lane:** {lane or 'N/A'}")
        lines.append(f"- **Type:** {dtype or 'unknown'} | **Folder:** {folder} | **Size:** {sz_str}")
        lines.append(f"- **Path:** `{filepath}`")

        cases = _safe_load_list(cases_j)
        if cases:
            lines.append(f"- **Case numbers:** {', '.join(cases[:5])}")

        quotes = _safe_load_list(quotes_j)
        if quotes:
            lines.append(f"- **Key quotes:**")
            for q in quotes[:3]:
                lines.append(f'  > "{q}"')

        lines.append("")

    lines.append("---")
    lines.append("*Generated by OMEGA-FLATTEN v1.0 — LitigationOS Event Horizon Δ∞*")
    lines.append("")

    out_path = os.path.join(index_dir, "TOP_EVIDENCE.md")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
    except (PermissionError, OSError) as exc:
        print(f"  [FORGE] WARNING: Could not write top evidence: {exc}")

    return {"count": len(rows)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_load_list(json_str: Optional[str]) -> List[str]:
    """Safely parse a JSON string that should be a list."""
    if not json_str:
        return []
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return [str(x) for x in data]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _write_json(path: str, data: Any) -> None:
    """Write JSON with error handling."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
    except (PermissionError, OSError) as exc:
        print(f"  [FORGE] WARNING: Could not write {path}: {exc}")


def _record_outputs(
    conn: sqlite3.Connection,
    drive: str,
    index_dir: str,
    outputs: Dict[str, Tuple[str, str]],
) -> None:
    """Record forge outputs in the DB."""
    rows = [
        (os.path.join(index_dir, filename), output_type, description, "")
        for filename, (output_type, description) in outputs.items()
    ]
    conn.executemany(
        """INSERT INTO forge_outputs (output_path, output_type, description, case_lane)
           VALUES (?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
