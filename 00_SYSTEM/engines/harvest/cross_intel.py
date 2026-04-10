"""
Harvest Engine — Cross-Intelligence Fusion Module v1.0

Post-harvest intelligence pipeline:
  1. Detect contradictions between new evidence and existing DB quotes
  2. Update adversary and topic encyclopedias with new evidence counts
  3. Rebuild FTS5 indexes after bulk inserts
  4. Orchestrate full cross-intelligence pass

No module-level side effects. No stdout clobbering. FTS5 safety (Rule 15).
Schema-verify (Rule 16). Proper PRAGMAs (Rule 18).
"""

import logging
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Known adversary names for actor extraction (case-insensitive matching)
_KNOWN_ACTORS = frozenset({
    "emily", "watson", "emily watson", "emily a. watson",
    "mcneill", "jenny mcneill", "judge mcneill",
    "hoopes", "kenneth hoopes", "judge hoopes",
    "ladas-hoopes", "maria ladas-hoopes",
    "barnes", "jennifer barnes",
    "rusco", "pamela rusco",
    "ronald berry", "ron berry", "berry",
    "albert watson", "albert", "lori watson",
    "andrew", "pigors", "andrew pigors",
})

# Topic keywords for grouping evidence by subject area
_TOPIC_KEYWORDS = {
    "custody": {"custody", "parenting", "visitation", "child", "best interest", "factor"},
    "ppo": {"ppo", "protection order", "stalking", "harassment", "restraining"},
    "contempt": {"contempt", "jail", "incarceration", "show cause", "sentence"},
    "alienation": {"alienation", "withholding", "interference", "parental alienation"},
    "misconduct": {"judicial", "misconduct", "bias", "ex parte", "canon", "jtc"},
    "housing": {"eviction", "housing", "shady oaks", "trailer", "habitability"},
    "false_allegations": {"allegation", "fabricated", "false", "arsenic", "poisoning", "assault"},
    "medical": {"healthwest", "mental health", "medication", "locus", "psychosis", "evaluation"},
    "financial": {"employment", "job", "income", "support", "damages"},
    "recording": {"recording", "audio", "video", "sullivan", "one-party"},
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
    """Schema-verify per Rule 16: PRAGMA table_info before querying."""
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row["name"] for row in rows}
    except (sqlite3.OperationalError, KeyError):
        try:
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            return {row[1] for row in rows}
        except sqlite3.OperationalError:
            return set()


def _sanitize_fts5(query: str) -> str:
    """FTS5 safety per Rule 15: strip non-word chars except spaces, *, and quotes."""
    return re.sub(r'[^\w\s*"]', ' ', query).strip()


def _fts5_search(conn: sqlite3.Connection, fts_table: str,
                 query: str, limit: int = 50) -> list[sqlite3.Row]:
    """FTS5 search with sanitization, try/except, and LIKE fallback (Rule 15).

    Returns list of Row objects from the FTS5 content table.
    """
    sanitized = _sanitize_fts5(query)
    if not sanitized:
        return []

    # Determine the content table from FTS5 config
    content_tables = {
        "evidence_fts": "evidence_quotes",
        "timeline_fts": "master_evidence_timeline",
    }
    content_table = content_tables.get(fts_table, "evidence_quotes")

    # Stage 1: Try FTS5 MATCH
    try:
        rows = conn.execute(
            f"SELECT rowid, * FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT ?",
            (sanitized, limit)
        ).fetchall()
        if rows:
            return rows
    except sqlite3.OperationalError as exc:
        logger.warning("FTS5 MATCH failed on %s: %s — falling back to LIKE", fts_table, exc)

    # Stage 2: LIKE fallback on the content table
    if _table_exists(conn, content_table):
        cols = _get_columns(conn, content_table)
        # Pick the best text column to search
        search_col = "quote_text" if "quote_text" in cols else "description" if "description" in cols else None
        if search_col:
            try:
                like_param = f"%{sanitized[:100]}%"
                rows = conn.execute(
                    f"SELECT * FROM {content_table} WHERE {search_col} LIKE ? LIMIT ?",
                    (like_param, limit)
                ).fetchall()
                return rows
            except sqlite3.OperationalError as exc:
                logger.error("LIKE fallback failed on %s: %s", content_table, exc)

    return []


def _extract_actor(quote: dict[str, Any]) -> str:
    """Extract the primary actor from a quote dict.

    Checks dedicated fields first, then falls back to tags/category parsing.
    """
    # Direct actor fields
    for field in ("actor", "actors", "target", "person_name"):
        val = quote.get(field)
        if val and isinstance(val, str) and val.strip():
            return val.strip().lower()

    # Parse from tags (comma-separated)
    tags = quote.get("tags", "") or ""
    for tag in tags.split(","):
        tag_clean = tag.strip().lower()
        if tag_clean in _KNOWN_ACTORS:
            return tag_clean

    # Parse from category
    category = (quote.get("category", "") or "").lower()
    for actor in _KNOWN_ACTORS:
        if actor in category:
            return actor

    # Parse from quote_text — first known actor mention
    text = (quote.get("quote_text", "") or "").lower()
    for actor in sorted(_KNOWN_ACTORS, key=len, reverse=True):
        if actor in text:
            return actor

    return "unknown"


def _extract_topic(quote: dict[str, Any]) -> str:
    """Extract the primary topic from a quote dict based on keyword matching."""
    text = " ".join([
        (quote.get("quote_text", "") or ""),
        (quote.get("category", "") or ""),
        (quote.get("tags", "") or ""),
    ]).lower()

    best_topic = "general"
    best_score = 0
    for topic, keywords in _TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic


def _score_severity(quote_a_text: str, quote_b_text: str,
                    topic: str) -> str:
    """Score contradiction severity based on textual opposition signals.

    Returns: 'critical', 'high', 'medium', or 'low'.
    """
    a_lower = quote_a_text.lower()
    b_lower = quote_b_text.lower()

    # Critical: direct negation patterns (sworn vs action, never/always contradictions)
    critical_patterns = [
        ("never", "did"), ("denied", "admitted"), ("no", "yes"),
        ("innocent", "guilty"), ("false", "true"), ("safe", "dangerous"),
        ("fit", "unfit"), ("denied", "confirmed"), ("recanted", "alleged"),
        ("nothing was physical", "physical assault"),
        ("not", "was"), ("zero", "multiple"),
    ]
    critical_score = 0
    for pat_a, pat_b in critical_patterns:
        if (pat_a in a_lower and pat_b in b_lower) or (pat_b in a_lower and pat_a in b_lower):
            critical_score += 1

    if critical_score >= 2:
        return "critical"

    # High: strong factual opposition
    high_keywords = {"contradict", "opposite", "inconsistent", "denied", "admitted",
                     "recanted", "lied", "fabricated", "premeditated"}
    combined = a_lower + " " + b_lower
    high_score = sum(1 for kw in high_keywords if kw in combined)
    if critical_score >= 1 or high_score >= 2:
        return "high"

    # Medium: same topic with differing claims
    if topic in ("false_allegations", "misconduct", "contempt", "alienation"):
        return "medium"

    # Low: minor discrepancy
    return "low"


def detect_contradictions(db_path: Optional[str] = None,
                          new_quotes: Optional[list[dict[str, Any]]] = None,
                          ) -> list[dict[str, Any]]:
    """Compare new evidence quotes against existing evidence_quotes table.

    Same actor + different statement on same topic = contradiction candidate.
    Uses FTS5 search with sanitization + try/except + LIKE fallback (Rule 15).

    Args:
        db_path: Path to litigation_context.db (default: repo root).
        new_quotes: List of quote dicts with at minimum 'quote_text' and 'source_file'.

    Returns:
        List of contradiction dicts with keys:
            quote_a, quote_b, actor, topic, severity, source_a, source_b
    """
    if not new_quotes:
        logger.info("detect_contradictions: no new quotes provided")
        return []

    conn = _connect(db_path)
    contradictions: list[dict[str, Any]] = []

    try:
        # Schema-verify evidence_quotes
        if not _table_exists(conn, "evidence_quotes"):
            logger.warning("evidence_quotes table does not exist — skipping contradiction detection")
            return []

        eq_cols = _get_columns(conn, "evidence_quotes")
        if "quote_text" not in eq_cols:
            logger.warning("evidence_quotes missing quote_text column — skipping")
            return []

        has_tags = "tags" in eq_cols
        has_category = "category" in eq_cols
        has_source = "source_file" in eq_cols

        for quote in new_quotes:
            quote_text = (quote.get("quote_text") or "").strip()
            if not quote_text or len(quote_text) < 10:
                continue

            actor = _extract_actor(quote)
            topic = _extract_topic(quote)
            source_file = quote.get("source_file", "unknown")

            if actor == "unknown":
                continue

            # Search existing quotes for same actor via FTS5 or LIKE
            search_term = _sanitize_fts5(actor)
            existing_matches: list[sqlite3.Row] = []

            # Try FTS5 first on evidence_fts
            if _table_exists(conn, "evidence_fts"):
                existing_matches = _fts5_search(conn, "evidence_fts", search_term, limit=100)

            # If FTS5 returned nothing, try LIKE on evidence_quotes directly
            if not existing_matches:
                like_fields = []
                params: list[str] = []
                actor_like = f"%{actor}%"

                if has_tags:
                    like_fields.append("tags LIKE ?")
                    params.append(actor_like)
                if has_category:
                    like_fields.append("category LIKE ?")
                    params.append(actor_like)
                like_fields.append("quote_text LIKE ?")
                params.append(actor_like)

                where_clause = " OR ".join(like_fields)
                try:
                    existing_matches = conn.execute(
                        f"SELECT * FROM evidence_quotes WHERE ({where_clause}) LIMIT 100",
                        params
                    ).fetchall()
                except sqlite3.OperationalError as exc:
                    logger.error("LIKE search for actor '%s' failed: %s", actor, exc)
                    continue

            # Compare new quote against existing matches for contradictions
            for existing in existing_matches:
                try:
                    existing_text = existing["quote_text"] if isinstance(existing, sqlite3.Row) else (existing[2] if len(existing) > 2 else "")
                except (KeyError, IndexError):
                    continue

                if not existing_text or existing_text == quote_text:
                    continue

                existing_topic = _extract_topic(dict(
                    quote_text=existing_text,
                    category=_safe_row_get(existing, "category", ""),
                    tags=_safe_row_get(existing, "tags", ""),
                ))

                # Same actor + same topic + different text = contradiction candidate
                if existing_topic == topic or topic == "general" or existing_topic == "general":
                    severity = _score_severity(quote_text, existing_text, topic)

                    # Skip low-severity unless they're on a high-value topic
                    if severity == "low" and topic == "general":
                        continue

                    existing_source = _safe_row_get(existing, "source_file", "unknown")

                    contradictions.append({
                        "quote_a": quote_text[:500],
                        "quote_b": existing_text[:500] if isinstance(existing_text, str) else str(existing_text)[:500],
                        "actor": actor,
                        "topic": topic,
                        "severity": severity,
                        "source_a": str(source_file),
                        "source_b": str(existing_source),
                        "detected_at": datetime.now().isoformat(),
                    })

        # Deduplicate contradictions (same pair shouldn't appear twice)
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for c in contradictions:
            key = f"{c['actor']}|{c['quote_a'][:80]}|{c['quote_b'][:80]}"
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        # Persist new contradictions to contradiction_map
        if deduped and _table_exists(conn, "contradiction_map"):
            cm_cols = _get_columns(conn, "contradiction_map")
            required = {"source_a", "source_b", "contradiction_text", "severity"}
            if required.issubset(cm_cols):
                has_claim_id = "claim_id" in cm_cols
                has_lane = "lane" in cm_cols
                for c in deduped:
                    contradiction_text = f"[{c['actor']}] A: {c['quote_a'][:200]} vs B: {c['quote_b'][:200]}"
                    try:
                        if has_claim_id and has_lane:
                            conn.execute(
                                "INSERT INTO contradiction_map "
                                "(claim_id, source_a, source_b, contradiction_text, severity, lane) "
                                "VALUES (?, ?, ?, ?, ?, ?)",
                                (c["topic"], c["source_a"], c["source_b"],
                                 contradiction_text, c["severity"], "")
                            )
                        else:
                            conn.execute(
                                "INSERT INTO contradiction_map "
                                "(source_a, source_b, contradiction_text, severity) "
                                "VALUES (?, ?, ?, ?)",
                                (c["source_a"], c["source_b"],
                                 contradiction_text, c["severity"])
                            )
                    except sqlite3.OperationalError as exc:
                        logger.error("Failed to insert contradiction: %s", exc)

                conn.commit()
                logger.info("Persisted %d contradictions to contradiction_map", len(deduped))

        logger.info("Detected %d contradictions from %d new quotes", len(deduped), len(new_quotes))
        return deduped

    except Exception as exc:
        logger.error("detect_contradictions failed: %s", exc, exc_info=True)
        return contradictions
    finally:
        conn.close()


def _safe_row_get(row: Any, key: str, default: str = "") -> str:
    """Safely extract a field from a sqlite3.Row or tuple."""
    try:
        if isinstance(row, sqlite3.Row):
            return row[key] or default
        return default
    except (KeyError, IndexError):
        return default


def update_encyclopedias(db_path: Optional[str] = None,
                         harvest_results: Optional[list[dict[str, Any]]] = None,
                         ) -> dict[str, Any]:
    """Update adversary_encyclopedia and topic_encyclopedia with new evidence counts.

    Args:
        db_path: Path to litigation_context.db.
        harvest_results: List of harvest result dicts (evidence atoms).

    Returns:
        Dict with 'adversary_updates' and 'topic_updates' counts.
    """
    result = {"adversary_updates": 0, "topic_updates": 0, "errors": []}

    if not harvest_results:
        logger.info("update_encyclopedias: no harvest results provided")
        return result

    conn = _connect(db_path)
    try:
        # --- Adversary Encyclopedia ---
        if _table_exists(conn, "adversary_encyclopedia"):
            ae_cols = _get_columns(conn, "adversary_encyclopedia")
            if "person_name" in ae_cols and "evidence_count" in ae_cols:
                # Count actor mentions across harvest results
                actor_counts: Counter[str] = Counter()
                for hr in harvest_results:
                    actor = _extract_actor(hr)
                    if actor and actor != "unknown":
                        actor_counts[actor] += 1

                has_last_updated = "last_updated" in ae_cols

                for actor_name, count in actor_counts.items():
                    try:
                        # Check if adversary exists
                        existing = conn.execute(
                            "SELECT id, evidence_count FROM adversary_encyclopedia "
                            "WHERE LOWER(person_name) = ?",
                            (actor_name.lower(),)
                        ).fetchone()

                        if existing:
                            old_count = existing["evidence_count"] or 0
                            new_count = old_count + count
                            if has_last_updated:
                                conn.execute(
                                    "UPDATE adversary_encyclopedia "
                                    "SET evidence_count = ?, last_updated = datetime('now') "
                                    "WHERE id = ?",
                                    (new_count, existing["id"])
                                )
                            else:
                                conn.execute(
                                    "UPDATE adversary_encyclopedia "
                                    "SET evidence_count = ? WHERE id = ?",
                                    (new_count, existing["id"])
                                )
                            result["adversary_updates"] += 1
                        else:
                            # Insert new adversary entry
                            conn.execute(
                                "INSERT INTO adversary_encyclopedia "
                                "(person_name, evidence_count) VALUES (?, ?)",
                                (actor_name.title(), count)
                            )
                            result["adversary_updates"] += 1

                    except sqlite3.OperationalError as exc:
                        msg = f"Failed to update adversary '{actor_name}': {exc}"
                        logger.error(msg)
                        result["errors"].append(msg)

                conn.commit()
                logger.info("Updated %d adversary encyclopedia entries", result["adversary_updates"])
            else:
                logger.warning("adversary_encyclopedia missing required columns (person_name/evidence_count)")
        else:
            logger.warning("adversary_encyclopedia table does not exist")

        # --- Topic Encyclopedia ---
        if _table_exists(conn, "topic_encyclopedia"):
            te_cols = _get_columns(conn, "topic_encyclopedia")
            if "topic" in te_cols and "evidence_count" in te_cols:
                topic_counts: Counter[str] = Counter()
                for hr in harvest_results:
                    topic = _extract_topic(hr)
                    if topic and topic != "general":
                        topic_counts[topic] += 1

                has_last_updated = "last_updated" in te_cols

                for topic_name, count in topic_counts.items():
                    try:
                        existing = conn.execute(
                            "SELECT id, evidence_count FROM topic_encyclopedia "
                            "WHERE LOWER(topic) = ?",
                            (topic_name.lower(),)
                        ).fetchone()

                        if existing:
                            old_count = existing["evidence_count"] or 0
                            new_count = old_count + count
                            if has_last_updated:
                                conn.execute(
                                    "UPDATE topic_encyclopedia "
                                    "SET evidence_count = ?, last_updated = datetime('now') "
                                    "WHERE id = ?",
                                    (new_count, existing["id"])
                                )
                            else:
                                conn.execute(
                                    "UPDATE topic_encyclopedia "
                                    "SET evidence_count = ? WHERE id = ?",
                                    (new_count, existing["id"])
                                )
                            result["topic_updates"] += 1
                        else:
                            conn.execute(
                                "INSERT INTO topic_encyclopedia "
                                "(topic, evidence_count) VALUES (?, ?)",
                                (topic_name, count)
                            )
                            result["topic_updates"] += 1

                    except sqlite3.OperationalError as exc:
                        msg = f"Failed to update topic '{topic_name}': {exc}"
                        logger.error(msg)
                        result["errors"].append(msg)

                conn.commit()
                logger.info("Updated %d topic encyclopedia entries", result["topic_updates"])
            else:
                logger.warning("topic_encyclopedia missing required columns (topic/evidence_count)")
        else:
            logger.warning("topic_encyclopedia table does not exist")

        return result

    except Exception as exc:
        logger.error("update_encyclopedias failed: %s", exc, exc_info=True)
        result["errors"].append(str(exc))
        return result
    finally:
        conn.close()


def rebuild_fts5_indexes(db_path: Optional[str] = None) -> dict[str, str]:
    """Rebuild FTS5 indexes after bulk inserts.

    Rebuilds evidence_fts and timeline_fts using the 'rebuild' command.

    Args:
        db_path: Path to litigation_context.db.

    Returns:
        Dict mapping index name to 'success' or error message.
    """
    results: dict[str, str] = {}
    conn = _connect(db_path)

    try:
        fts_tables = {
            "evidence_fts": "INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')",
            "timeline_fts": "INSERT INTO timeline_fts(timeline_fts) VALUES('rebuild')",
        }

        for fts_name, rebuild_sql in fts_tables.items():
            if not _table_exists(conn, fts_name):
                results[fts_name] = "table_not_found"
                logger.warning("FTS5 table %s does not exist — skipping rebuild", fts_name)
                continue

            try:
                conn.execute(rebuild_sql)
                conn.commit()
                results[fts_name] = "success"
                logger.info("Rebuilt FTS5 index: %s", fts_name)
            except sqlite3.OperationalError as exc:
                results[fts_name] = f"error: {exc}"
                logger.error("Failed to rebuild %s: %s", fts_name, exc)

        return results

    except Exception as exc:
        logger.error("rebuild_fts5_indexes failed: %s", exc, exc_info=True)
        return {"error": str(exc)}
    finally:
        conn.close()


def run_cross_intelligence(db_path: Optional[str] = None,
                           harvest_results: Optional[list[dict[str, Any]]] = None,
                           ) -> dict[str, Any]:
    """Orchestrate full cross-intelligence pass after a harvest run.

    Calls detect_contradictions, update_encyclopedias, and rebuild_fts5_indexes
    in sequence.

    Args:
        db_path: Path to litigation_context.db.
        harvest_results: List of harvest result dicts (evidence atoms with
            at minimum 'quote_text' and 'source_file').

    Returns:
        Comprehensive summary dict with results from each sub-operation.
    """
    started_at = datetime.now()
    summary: dict[str, Any] = {
        "started_at": started_at.isoformat(),
        "input_count": len(harvest_results) if harvest_results else 0,
        "contradictions": [],
        "encyclopedia_updates": {},
        "fts5_rebuild": {},
        "errors": [],
        "completed_at": None,
        "duration_seconds": 0.0,
    }

    if not harvest_results:
        logger.info("run_cross_intelligence: no harvest results to process")
        summary["completed_at"] = datetime.now().isoformat()
        return summary

    db_str = str(db_path) if db_path else None

    # Phase 1: Detect contradictions
    logger.info("Cross-intel Phase 1: Detecting contradictions from %d results...", len(harvest_results))
    try:
        new_quotes = [
            hr for hr in harvest_results
            if hr.get("quote_text") and len(hr.get("quote_text", "")) >= 10
        ]
        contradictions = detect_contradictions(db_str, new_quotes)
        summary["contradictions"] = contradictions
        logger.info("Phase 1 complete: %d contradictions detected", len(contradictions))
    except Exception as exc:
        msg = f"Phase 1 (contradictions) failed: {exc}"
        logger.error(msg, exc_info=True)
        summary["errors"].append(msg)

    # Phase 2: Update encyclopedias
    logger.info("Cross-intel Phase 2: Updating encyclopedias...")
    try:
        enc_result = update_encyclopedias(db_str, harvest_results)
        summary["encyclopedia_updates"] = enc_result
        logger.info("Phase 2 complete: %d adversary + %d topic updates",
                     enc_result.get("adversary_updates", 0),
                     enc_result.get("topic_updates", 0))
    except Exception as exc:
        msg = f"Phase 2 (encyclopedias) failed: {exc}"
        logger.error(msg, exc_info=True)
        summary["errors"].append(msg)

    # Phase 3: Rebuild FTS5 indexes
    logger.info("Cross-intel Phase 3: Rebuilding FTS5 indexes...")
    try:
        fts_result = rebuild_fts5_indexes(db_str)
        summary["fts5_rebuild"] = fts_result
        logger.info("Phase 3 complete: %s", fts_result)
    except Exception as exc:
        msg = f"Phase 3 (FTS5 rebuild) failed: {exc}"
        logger.error(msg, exc_info=True)
        summary["errors"].append(msg)

    completed_at = datetime.now()
    summary["completed_at"] = completed_at.isoformat()
    summary["duration_seconds"] = round((completed_at - started_at).total_seconds(), 2)

    severity_counts: Counter[str] = Counter()
    for c in summary.get("contradictions", []):
        severity_counts[c.get("severity", "unknown")] += 1
    summary["contradiction_severity_breakdown"] = dict(severity_counts)

    logger.info(
        "Cross-intelligence complete in %.1fs: %d contradictions, %d encyclopedia updates, FTS5: %s",
        summary["duration_seconds"],
        len(summary["contradictions"]),
        summary["encyclopedia_updates"].get("adversary_updates", 0)
        + summary["encyclopedia_updates"].get("topic_updates", 0),
        summary["fts5_rebuild"],
    )

    return summary
