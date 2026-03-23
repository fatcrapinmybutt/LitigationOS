"""OMEGA-FLATTEN analyzer — deep litigation-relevance analysis of every file.

LitigationOS Event Horizon Δ∞
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from .classifier import detect_meek_lane, read_content_preview
from .config import (
    BATCH_SIZE,
    CHECKPOINT_INTERVAL,
    MAX_ANALYSIS_FILE_SIZE,
    PROGRESS_INTERVAL,
)

# ---------------------------------------------------------------------------
# Compiled entity-extraction regexes
# ---------------------------------------------------------------------------

_RE_NAMES = re.compile(
    r"\b([A-Z][a-z]{2,}(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]{2,})\b"
)
_RE_DATES_MDY = re.compile(
    r"\b((?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2})\b"
)
_RE_DATES_YMD = re.compile(
    r"\b((?:19|20)\d{2}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01]))\b"
)
_RE_DATES_LONG = re.compile(
    r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
_RE_CASE_NUMBERS = re.compile(r"\b(\d{4}-\d{4,6}-[A-Z]{2})\b")
_RE_DOLLAR = re.compile(r"\$[\d,]+\.?\d*")
_RE_MCL = re.compile(r"\bMCL\s+\d+\.\d+[a-z]?\b", re.IGNORECASE)
_RE_MCR = re.compile(r"\bMCR\s+\d+\.\d+[a-z]?\b", re.IGNORECASE)

# Evidence keyword indicators
_EVIDENCE_KEYWORDS = [
    "exhibit", "evidence", "affidavit", "sworn", "notarized",
    "testimony", "deposition", "interrogator", "subpoena",
    "discovery", "admission", "stipulation", "declaration",
]
_RE_EVIDENCE = re.compile(
    r"\b(?:" + "|".join(_EVIDENCE_KEYWORDS) + r")\b", re.IGNORECASE
)

# MEEK keyword regexes for density scoring
_MEEK_ALL_KEYWORDS = re.compile(
    r"\b(?:custody|parenting.time|ppo|protection.order|shady.oaks|"
    r"judicial.misconduct|jtc|disqualification|recusal|appellate|"
    r"court.of.appeals|watson|mcneill|lockout|title|"
    r"friend.of.the.court|foc|contempt|garnishment|"
    r"best.interest|domestic.violence)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def _extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract litigation-relevant entities from *text*."""
    names = list(dict.fromkeys(_RE_NAMES.findall(text)[:50]))
    dates = list(dict.fromkeys(
        _RE_DATES_MDY.findall(text) +
        _RE_DATES_YMD.findall(text) +
        _RE_DATES_LONG.findall(text)
    ))[:50]
    case_numbers = list(dict.fromkeys(_RE_CASE_NUMBERS.findall(text)))[:20]
    dollars = list(dict.fromkeys(_RE_DOLLAR.findall(text)))[:30]
    mcl_cites = list(dict.fromkeys(_RE_MCL.findall(text)))[:30]
    mcr_cites = list(dict.fromkeys(_RE_MCR.findall(text)))[:30]

    return {
        "names": names,
        "dates": dates,
        "case_numbers": case_numbers,
        "dollar_amounts": dollars,
        "mcl_citations": mcl_cites,
        "mcr_citations": mcr_cites,
    }


# ---------------------------------------------------------------------------
# Litigation scoring (0 – 10)
# ---------------------------------------------------------------------------

def _score_litigation(
    text: str,
    entities: Dict[str, List[str]],
    extension: str,
    folder: str,
) -> Tuple[float, str]:
    """Score litigation relevance 0–10 and assign evidence_value.

    Scoring rubric:
    - MEEK keyword density:    0–3 points
    - Entity richness:         0–2 points
    - Legal citation presence: 0–2 points
    - Evidence indicators:     0–2 points
    - File type bonus:         0–1 point  (PDF/DOCX)
    """
    score = 0.0

    # MEEK keyword density (0-3)
    meek_hits = len(_MEEK_ALL_KEYWORDS.findall(text[:8192]))
    if meek_hits >= 10:
        score += 3.0
    elif meek_hits >= 5:
        score += 2.0
    elif meek_hits >= 2:
        score += 1.0
    elif meek_hits >= 1:
        score += 0.5

    # Entity richness (0-2)
    entity_count = (
        len(entities.get("names", []))
        + len(entities.get("dates", []))
        + len(entities.get("case_numbers", []))
        + len(entities.get("dollar_amounts", []))
    )
    if entity_count >= 15:
        score += 2.0
    elif entity_count >= 8:
        score += 1.5
    elif entity_count >= 3:
        score += 1.0
    elif entity_count >= 1:
        score += 0.5

    # Legal citation presence (0-2)
    citations = entities.get("mcl_citations", []) + entities.get("mcr_citations", [])
    if len(citations) >= 5:
        score += 2.0
    elif len(citations) >= 2:
        score += 1.5
    elif len(citations) >= 1:
        score += 1.0

    # Evidence indicators (0-2)
    evidence_hits = len(_RE_EVIDENCE.findall(text[:8192]))
    if evidence_hits >= 5:
        score += 2.0
    elif evidence_hits >= 2:
        score += 1.5
    elif evidence_hits >= 1:
        score += 0.5

    # File type bonus (0-1)
    if extension in (".pdf", ".docx", ".doc"):
        score += 1.0
    elif folder == "LEGAL":
        score += 1.0

    score = min(score, 10.0)

    # Evidence value classification
    if score >= 7.0:
        value = "high"
    elif score >= 4.0:
        value = "medium"
    elif score >= 1.5:
        value = "low"
    else:
        value = "none"

    return round(score, 2), value


# ---------------------------------------------------------------------------
# Key quote extraction
# ---------------------------------------------------------------------------

def _extract_key_quotes(text: str, max_quotes: int = 5) -> List[str]:
    """Pull short, high-signal sentences from *text*."""
    quotes: List[str] = []
    # Split into sentences (rough)
    sentences = re.split(r"(?<=[.!?])\s+", text[:16384])

    patterns = [
        re.compile(r"\border(?:ed|ing|s)?\b", re.IGNORECASE),
        re.compile(r"\bfind(?:s|ing)?\b", re.IGNORECASE),
        re.compile(r"\bviolat", re.IGNORECASE),
        re.compile(r"\bcontempt\b", re.IGNORECASE),
        re.compile(r"\bdenied?\b", re.IGNORECASE),
        re.compile(r"\bgranted?\b", re.IGNORECASE),
        re.compile(r"\bcustody\b", re.IGNORECASE),
        re.compile(r"\bparenting.time\b", re.IGNORECASE),
        re.compile(r"\bppo\b", re.IGNORECASE),
        re.compile(r"\bsuspend", re.IGNORECASE),
    ]

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 500:
            continue
        hits = sum(1 for p in patterns if p.search(sentence))
        if hits >= 2:
            quotes.append(sentence)
            if len(quotes) >= max_quotes:
                break

    return quotes


# ---------------------------------------------------------------------------
# Determine document type
# ---------------------------------------------------------------------------

def _detect_document_type(text: str, folder: str) -> str:
    """Classify the document type based on content patterns."""
    text_lower = text[:4096].lower()

    type_signals = {
        "court_order": [r"\border\b", r"\bit is (?:hereby )?ordered\b", r"\bjudgment\b"],
        "motion": [r"\bmotion\s+(?:to|for)\b", r"\brelief\b", r"\bpetition\b"],
        "affidavit": [r"\baffidavit\b", r"\bsworn\b", r"\bnotary\b"],
        "brief": [r"\bbrief\b", r"\bargument\b", r"\bstatement of (?:facts|issues)\b"],
        "correspondence": [r"\bdear\b", r"\bsincerely\b", r"\bregards\b"],
        "financial": [r"\binvoice\b", r"\bstatement\b.*\bbalance\b", r"\bpayment\b"],
        "police_report": [r"\bincident\s+report\b", r"\bofficer\b", r"\bdispatch\b"],
        "medical": [r"\bdiagnos", r"\btreatment\b", r"\bpatient\b"],
        "foia_record": [r"\bfoia\b", r"\bfreedom of information\b"],
        "transcript": [r"\bq\.\s", r"\ba\.\s", r"\bthe court:\b"],
        "email": [r"\bfrom:\b", r"\bto:\b", r"\bsubject:\b", r"\bsent:\b"],
        "lease_property": [r"\blease\b", r"\btenant\b", r"\blandlord\b", r"\bproperty\b"],
    }

    best_type = "general"
    best_hits = 0

    for doc_type, patterns in type_signals.items():
        hits = sum(1 for p in patterns if re.search(p, text_lower))
        if hits > best_hits:
            best_hits = hits
            best_type = doc_type

    if best_hits == 0 and folder != "_UNKNOWN":
        # Fall back to folder-based classification
        folder_types = {
            "PDF": "document",
            "DOCX": "document",
            "EMAIL": "email",
            "IMG": "image",
            "VIDEO": "video",
            "AUDIO": "audio",
            "DB": "database",
            "CODE": "source_code",
            "PY": "source_code",
            "CSV": "spreadsheet",
            "JSON": "data_file",
            "XML": "data_file",
            "LEGAL": "legal_document",
        }
        best_type = folder_types.get(folder, "general")

    return best_type


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze_files(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    *,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Analyze all scanned/organized files on *drive* for litigation relevance.

    Parameters
    ----------
    conn:
        Connection to ``flatten.db``.
    drive:
        Drive letter (no colon).
    session_id:
        Active ``scan_sessions.id``.
    limit:
        Max files to analyze (for testing).

    Returns
    -------
    dict with keys: files_analyzed, high_value, medium_value, low_value, errors.
    """
    limit_clause = f"LIMIT {limit}" if limit else ""
    cursor = conn.execute(
        f"""SELECT id, original_path, new_path, folder, filename, extension, size_bytes
              FROM flat_files
             WHERE drive = ? AND status IN ('scanned', 'organized')
                   AND analyzed_at IS NULL
             ORDER BY id
             {limit_clause}""",
        (drive,),
    )

    files_analyzed = 0
    value_counts = {"high": 0, "medium": 0, "low": 0, "none": 0}
    errors = 0

    ff_updates: List[Tuple[float, str, str, str, str, int]] = []
    fa_inserts: List[Tuple[int, float, str, str, str, str, str, str, str, str, str, str]] = []

    t0 = time.perf_counter()
    last_progress = 0

    while True:
        rows = cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break

        for file_id, original_path, new_path, folder, filename, extension, size_bytes in rows:
            filepath = new_path or original_path

            # Read content preview (skip huge files)
            preview: Optional[str] = None
            if size_bytes <= MAX_ANALYSIS_FILE_SIZE:
                preview = read_content_preview(filepath)

            text = preview or ""

            # Entity extraction
            entities = _extract_entities(text) if text else {
                "names": [], "dates": [], "case_numbers": [],
                "dollar_amounts": [], "mcl_citations": [], "mcr_citations": [],
            }

            # Litigation scoring
            lit_score, evidence_value = _score_litigation(text, entities, extension or "", folder)

            # MEEK lane detection
            meek_lane = detect_meek_lane(filepath, text) if text else None

            # Key quotes
            key_quotes = _extract_key_quotes(text) if text else []

            # Document type
            doc_type = _detect_document_type(text, folder) if text else "unknown"

            # Evidence admissibility heuristic
            admissibility = "unknown"
            if doc_type in ("court_order", "affidavit", "transcript", "police_report"):
                admissibility = "likely_admissible"
            elif doc_type in ("email", "correspondence"):
                admissibility = "needs_authentication"
            elif doc_type in ("source_code", "database"):
                admissibility = "not_applicable"

            # Determine forge candidates
            forge_candidates: List[str] = []
            if lit_score >= 6.0:
                forge_candidates.append("timeline_extraction")
                forge_candidates.append("evidence_package")
            if entities.get("case_numbers"):
                forge_candidates.append("case_cross_reference")
            if key_quotes:
                forge_candidates.append("quote_compilation")

            entities_json = json.dumps(entities, ensure_ascii=False)
            case_lanes = meek_lane or ""

            # Collect for batch update
            ff_updates.append((
                lit_score,
                meek_lane or "",
                evidence_value,
                entities_json,
                time.strftime("%Y-%m-%dT%H:%M:%S"),
                file_id,
            ))
            fa_inserts.append((
                file_id,
                lit_score,
                case_lanes,
                json.dumps(entities.get("names", []), ensure_ascii=False),
                json.dumps(entities.get("dates", []), ensure_ascii=False),
                json.dumps(entities.get("case_numbers", []), ensure_ascii=False),
                json.dumps(entities.get("dollar_amounts", []), ensure_ascii=False),
                json.dumps(key_quotes, ensure_ascii=False),
                doc_type,
                admissibility,
                "",  # relationship_links — populated later by forge
                json.dumps(forge_candidates, ensure_ascii=False),
            ))

            value_counts[evidence_value] = value_counts.get(evidence_value, 0) + 1
            files_analyzed += 1

            # Progress
            if files_analyzed - last_progress >= PROGRESS_INTERVAL:
                elapsed = time.perf_counter() - t0
                rate = files_analyzed / elapsed if elapsed > 0 else 0
                print(
                    f"  [ANALYZE] {files_analyzed:,} analyzed "
                    f"(H:{value_counts['high']} M:{value_counts['medium']} L:{value_counts['low']}) "
                    f"— {rate:,.0f} files/sec",
                )
                last_progress = files_analyzed

        # Batch flush
        if len(ff_updates) >= CHECKPOINT_INTERVAL:
            _flush_analysis(conn, ff_updates, fa_inserts)
            ff_updates.clear()
            fa_inserts.clear()
            conn.execute(
                "UPDATE scan_sessions SET files_analyzed = ? WHERE id = ?",
                (files_analyzed, session_id),
            )
            conn.commit()

    # Final flush
    if ff_updates:
        _flush_analysis(conn, ff_updates, fa_inserts)

    conn.execute(
        "UPDATE scan_sessions SET files_analyzed = ? WHERE id = ?",
        (files_analyzed, session_id),
    )
    conn.commit()

    elapsed = time.perf_counter() - t0
    print(
        f"  [ANALYZE] COMPLETE — {files_analyzed:,} analyzed in {elapsed:.1f}s "
        f"(H:{value_counts['high']} M:{value_counts['medium']} "
        f"L:{value_counts['low']} N:{value_counts['none']})",
    )

    return {
        "files_analyzed": files_analyzed,
        "high_value": value_counts["high"],
        "medium_value": value_counts["medium"],
        "low_value": value_counts["low"],
        "none_value": value_counts["none"],
        "errors": errors,
        "elapsed_seconds": round(elapsed, 2),
    }


def _flush_analysis(
    conn: sqlite3.Connection,
    ff_updates: List[Tuple[float, str, str, str, str, int]],
    fa_inserts: List[Tuple[int, float, str, str, str, str, str, str, str, str, str, str]],
) -> None:
    """Batch update flat_files and insert file_analysis records."""
    conn.executemany(
        """UPDATE flat_files
              SET litigation_score = ?,
                  meek_lane = ?,
                  evidence_value = ?,
                  entities_json = ?,
                  analyzed_at = ?
            WHERE id = ?""",
        ff_updates,
    )
    conn.executemany(
        """INSERT OR REPLACE INTO file_analysis
               (file_id, litigation_relevance, case_lanes, entity_names,
                entity_dates, entity_case_numbers, entity_dollar_amounts,
                key_quotes, document_type, evidence_admissibility,
                relationship_links, forge_candidates)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        fa_inserts,
    )
    conn.commit()
