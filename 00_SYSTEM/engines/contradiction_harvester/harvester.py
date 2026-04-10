"""ContradictionHarvester — Two-stage contradiction detection engine.

Stage 1: Keyword opposition scan — finds statement pairs with
opposing language (deny/admit, never/always, etc.) from evidence_quotes.

Stage 2: Scoring — evaluates each candidate pair on:
    - Temporal ordering (same actor, different dates = stronger)
    - Source reliability (court records > self-report)
    - Semantic opposition strength (keyword density)

Contradictions scoring ≥6 are persisted to contradiction_map.
"""

import sys
import os
import re
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

logger = logging.getLogger(__name__)

# ── Opposition Pairs (used in Stage 1) ────────────────────────────────────

_OPPOSITION_PAIRS = [
    (r"\bden(?:y|ied|ies|ying)\b", r"\badmit(?:s|ted|ting)?\b"),
    (r"\bnever\b", r"\balways\b"),
    (r"\bno\s+(?:contact|violence|abuse|drugs?)\b", r"\b(?:contact|violence|abuse|drugs?)\b"),
    (r"\bdid\s+not\b", r"\bdid\b"),
    (r"\bwas\s+not\b", r"\bwas\b"),
    (r"\bsafe\b", r"\bdanger(?:ous)?\b"),
    (r"\bfalse\b", r"\btrue\b"),
    (r"\bnothing\s+(?:happened|physical|wrong)\b", r"\b(?:assault|attack|hit|push|struck)\b"),
    (r"\binnocent\b", r"\bguilty\b"),
    (r"\bno\s+evidence\b", r"\bevidence\b"),
    (r"\bcooperat(?:e|ed|ing|ive)\b", r"\brefus(?:e|ed|ing|al)\b"),
    (r"\bconsent(?:ed|ing)?\b", r"\bwithout\s+consent\b"),
    (r"\bvoluntar(?:y|ily)\b", r"\bforc(?:e|ed|ing)\b"),
    (r"\bpeace(?:ful|ably)?\b", r"\bviolen(?:t|ce)\b"),
]

# Compile patterns once for performance
_COMPILED_PAIRS = [
    (re.compile(a, re.IGNORECASE), re.compile(b, re.IGNORECASE))
    for a, b in _OPPOSITION_PAIRS
]

# Source reliability weights
_SOURCE_WEIGHTS = {
    "court_order": 1.0,
    "police_report": 0.95,
    "court_filing": 0.9,
    "transcript": 0.85,
    "official_record": 0.8,
    "appclose": 0.7,
    "email": 0.65,
    "text_message": 0.6,
    "self_report": 0.5,
    "unknown": 0.4,
}


# ── Core Class ────────────────────────────────────────────────────────────

class ContradictionHarvester:
    """Two-stage contradiction detection engine.

    Usage:
        harvester = ContradictionHarvester()
        results = harvester.harvest("Emily Watson", lane="A")
        harvester.persist(results)
    """

    MIN_PERSIST_SCORE = 6.0
    MAX_QUOTE_LENGTH = 2000

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── Lazy Connection ───────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def _connect(self) -> sqlite3.Connection:
        if self._db_path:
            path = self._db_path
        else:
            try:
                from shared import get_db_path
                path = str(get_db_path("litigation_context"))
            except ImportError:
                path = os.path.join(
                    r"C:\Users\andre\LitigationOS", "litigation_context.db"
                )
        conn = sqlite3.connect(path, timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── Harvest ───────────────────────────────────────────────────────

    def harvest(
        self,
        target: str,
        lane: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Harvest contradictions for a specific target (person/entity).

        Args:
            target: Person or entity name to search for
            lane: Optional lane filter (A-F, CRIMINAL)
            limit: Max quotes to load for analysis

        Returns:
            List of scored contradiction dicts with structure:
                {source_a, text_a, source_b, text_b, score, pairs_matched, target, lane}
        """
        quotes = self._load_quotes(target, lane, limit)
        if len(quotes) < 2:
            logger.info("Need ≥2 quotes for target '%s' (found %d)", target, len(quotes))
            return []

        # Stage 1: Find opposition candidates
        candidates = self._stage1_opposition_scan(quotes)
        logger.info("Stage 1: %d opposition candidates for '%s'", len(candidates), target)

        if not candidates:
            return []

        # Stage 2: Score each candidate
        scored = []
        for c in candidates:
            score_data = self._stage2_score(c)
            if score_data["score"] >= 3.0:  # Keep moderate+ for review
                scored.append(score_data)

        scored.sort(key=lambda x: x["score"], reverse=True)
        logger.info("Stage 2: %d scored contradictions for '%s'", len(scored), target)
        return scored

    def _load_quotes(
        self,
        target: str,
        lane: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Load evidence quotes mentioning the target."""
        clauses = ["is_duplicate = 0"]
        params: list = []

        # Search target in source_file, quote_text, and tags
        target_clean = re.sub(r'[^\w\s]', '', target).strip()
        if not target_clean:
            return []

        clauses.append(
            "(source_file LIKE ? OR quote_text LIKE ? OR tags LIKE ?)"
        )
        pattern = f"%{target_clean}%"
        params.extend([pattern, pattern, pattern])

        if lane:
            clauses.append("lane = ?")
            params.append(lane)

        params.append(limit)
        where = " AND ".join(clauses)

        # Verify evidence_quotes schema first
        try:
            cols = {
                row[1]
                for row in self.conn.execute("PRAGMA table_info(evidence_quotes)")
            }
        except sqlite3.OperationalError:
            logger.error("evidence_quotes table not accessible")
            return []

        select_cols = ["id", "source_file", "quote_text", "page_number",
                       "category", "lane", "created_at"]
        valid_cols = [c for c in select_cols if c in cols]

        rows = self.conn.execute(
            f"""SELECT {', '.join(valid_cols)}
                FROM evidence_quotes
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?""",
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    # ── Stage 1: Keyword Opposition Scan ──────────────────────────────

    def _stage1_opposition_scan(
        self,
        quotes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find pairs of quotes with opposing language.

        Compares each quote pair against compiled opposition regex patterns.
        """
        candidates = []
        seen_pairs = set()

        for i in range(len(quotes)):
            text_a = (quotes[i].get("quote_text") or "")[:self.MAX_QUOTE_LENGTH]
            if not text_a.strip():
                continue

            for j in range(i + 1, len(quotes)):
                text_b = (quotes[j].get("quote_text") or "")[:self.MAX_QUOTE_LENGTH]
                if not text_b.strip():
                    continue

                # Skip duplicate pairs
                pair_key = (
                    min(quotes[i].get("id", i), quotes[j].get("id", j)),
                    max(quotes[i].get("id", i), quotes[j].get("id", j)),
                )
                if pair_key in seen_pairs:
                    continue

                pairs_matched = self._count_opposition_matches(text_a, text_b)
                if pairs_matched > 0:
                    seen_pairs.add(pair_key)
                    candidates.append({
                        "quote_a": quotes[i],
                        "quote_b": quotes[j],
                        "text_a": text_a,
                        "text_b": text_b,
                        "pairs_matched": pairs_matched,
                    })

        return candidates

    def _count_opposition_matches(self, text_a: str, text_b: str) -> int:
        """Count how many opposition pairs match across texts A and B."""
        count = 0
        for pattern_a, pattern_b in _COMPILED_PAIRS:
            # Check A matches pattern_a AND B matches pattern_b
            if pattern_a.search(text_a) and pattern_b.search(text_b):
                count += 1
            # Also check reverse (A matches B-pattern, B matches A-pattern)
            if pattern_b.search(text_a) and pattern_a.search(text_b):
                count += 1
        return count

    # ── Stage 2: Scoring ──────────────────────────────────────────────

    def _stage2_score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Score a contradiction candidate (0-10).

        Components:
            - Opposition strength (0-4): from number of matching pairs
            - Source reliability (0-3): higher if from official sources
            - Temporal gap (0-3): bonus if statements from different dates
        """
        qa = candidate["quote_a"]
        qb = candidate["quote_b"]

        # Opposition strength (0-4)
        pairs = candidate["pairs_matched"]
        opposition_score = min(4.0, pairs * 1.5)

        # Source reliability (0-3)
        source_a_type = self._classify_source(qa.get("source_file", ""))
        source_b_type = self._classify_source(qb.get("source_file", ""))
        weight_a = _SOURCE_WEIGHTS.get(source_a_type, 0.4)
        weight_b = _SOURCE_WEIGHTS.get(source_b_type, 0.4)
        source_score = (weight_a + weight_b) / 2.0 * 3.0

        # Temporal gap (0-3)
        date_a = qa.get("created_at", "")
        date_b = qb.get("created_at", "")
        temporal_score = 0.0
        if date_a and date_b and date_a != date_b:
            temporal_score = 1.5
            # Bigger gap = more damaging
            try:
                da = datetime.fromisoformat(date_a[:19])
                db = datetime.fromisoformat(date_b[:19])
                gap_days = abs((da - db).days)
                if gap_days > 30:
                    temporal_score = 2.5
                if gap_days > 180:
                    temporal_score = 3.0
            except (ValueError, TypeError):
                temporal_score = 1.0

        total = round(opposition_score + source_score + temporal_score, 1)
        total = min(10.0, total)

        lane = qa.get("lane") or qb.get("lane") or ""

        return {
            "source_a": qa.get("source_file", "unknown"),
            "text_a": candidate["text_a"][:500],
            "source_b": qb.get("source_file", "unknown"),
            "text_b": candidate["text_b"][:500],
            "score": total,
            "opposition_score": opposition_score,
            "source_score": round(source_score, 2),
            "temporal_score": temporal_score,
            "pairs_matched": pairs,
            "target": "",  # filled by caller
            "lane": lane,
        }

    def _classify_source(self, source_file: str) -> str:
        """Classify a source file path into a reliability category."""
        lower = source_file.lower()
        if "court" in lower or "order" in lower or "judgment" in lower:
            return "court_order"
        if "police" in lower or "nspd" in lower or "ns20" in lower:
            return "police_report"
        if "motion" in lower or "filing" in lower or "complaint" in lower:
            return "court_filing"
        if "transcript" in lower or "hearing" in lower:
            return "transcript"
        if "appclose" in lower:
            return "appclose"
        if "email" in lower or "gmail" in lower:
            return "email"
        if "text" in lower or "sms" in lower or "message" in lower:
            return "text_message"
        return "unknown"

    # ── Persistence ───────────────────────────────────────────────────

    def persist(self, results: List[Dict[str, Any]], target: str = "") -> int:
        """Persist high-scoring contradictions to contradiction_map.

        Only inserts contradictions with score >= MIN_PERSIST_SCORE.
        Uses INSERT OR IGNORE to avoid duplicates.

        Returns: Number of rows inserted.
        """
        # Verify contradiction_map schema
        try:
            cols = {
                row[1]
                for row in self.conn.execute("PRAGMA table_info(contradiction_map)")
            }
        except sqlite3.OperationalError:
            logger.error("contradiction_map table not accessible")
            return 0

        required = {"claim_id", "source_a", "source_b", "contradiction_text", "severity", "lane"}
        if not required.issubset(cols):
            logger.error("contradiction_map missing columns: %s", required - cols)
            return 0

        inserted = 0
        for r in results:
            if r["score"] < self.MIN_PERSIST_SCORE:
                continue

            severity = "high" if r["score"] >= 8.0 else "medium"
            contradiction_text = (
                f"[A] {r['text_a'][:250]} vs [B] {r['text_b'][:250]}"
            )
            claim_id = f"CH-{target[:20]}-{inserted + 1}"

            try:
                self.conn.execute(
                    """INSERT OR IGNORE INTO contradiction_map
                       (claim_id, source_a, source_b, contradiction_text, severity, lane)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (claim_id, r["source_a"][:200], r["source_b"][:200],
                     contradiction_text, severity, r["lane"]),
                )
                inserted += 1
            except sqlite3.Error as e:
                logger.error("Failed to insert contradiction: %s", e)

        if inserted > 0:
            self.conn.commit()
            logger.info("Persisted %d contradictions for '%s'", inserted, target)
        return inserted

    # ── Batch Scan ────────────────────────────────────────────────────

    def scan_all_adversaries(
        self,
        adversaries: Optional[List[str]] = None,
        lane: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Scan multiple adversaries for contradictions.

        Args:
            adversaries: List of names to scan. If None, extracts distinct
                         actors from evidence_quotes source_file patterns.
            lane: Optional lane filter

        Returns:
            Dict mapping adversary name → list of scored contradictions
        """
        if adversaries is None:
            adversaries = self._extract_actors()

        all_results: Dict[str, List[Dict[str, Any]]] = {}
        for name in adversaries:
            results = self.harvest(name, lane=lane)
            # Tag results with target name
            for r in results:
                r["target"] = name
            if results:
                all_results[name] = results
                logger.info("%s: %d contradictions found", name, len(results))

        return all_results

    def _extract_actors(self) -> List[str]:
        """Extract known adversary names from the database."""
        # Use a curated list since actor extraction from source_file is unreliable
        return [
            "Emily Watson",
            "Emily",
            "Watson",
            "Albert Watson",
            "Albert",
            "McNeill",
            "Rusco",
            "Ronald Berry",
            "Hoopes",
        ]

    # ── Statistics ────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return contradiction_map statistics."""
        row = self.conn.execute(
            """SELECT
                (SELECT COUNT(*) FROM contradiction_map) AS total,
                (SELECT COUNT(DISTINCT claim_id) FROM contradiction_map) AS unique_claims,
                (SELECT COUNT(*) FROM contradiction_map WHERE severity='high') AS high,
                (SELECT COUNT(*) FROM contradiction_map WHERE severity='critical') AS critical
            """
        ).fetchone()

        lane_rows = self.conn.execute(
            """SELECT lane, COUNT(*) AS cnt
               FROM contradiction_map
               GROUP BY lane
               ORDER BY cnt DESC"""
        ).fetchall()

        return {
            "total": row[0] or 0,
            "unique_claims": row[1] or 0,
            "high_severity": row[2] or 0,
            "critical_severity": row[3] or 0,
            "by_lane": {r[0]: r[1] for r in lane_rows if r[0]},
        }
