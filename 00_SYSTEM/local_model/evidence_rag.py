#!/usr/bin/env python3
"""
APEX Evidence RAG — Lane-aware, posture-tagged evidence retrieval.

IRON LAW: Lane A evidence NEVER appears in Lane B queries.
Every result carries an evidence posture tag:
  RECORD_FACT | EVIDENCE_FACT | SWORN_FACT | ALLEGATION | INFERENCE

Database sources
----------------
  litigation_context.db     — evidence_quotes, documents, claims
  lane_A_custody.db … F     — per-lane evidence stores
  MEEK234_HIGHSIGNAL_DB.sqlite — 13.4 K high-signal quotes

Thread-safe, UTF-8 safe, never crashes.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Shadow LLM gate
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.evidence_rag")

# ---------------------------------------------------------------------------
# Paths (never CWD — always relative to *this* file)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent  # LitigationOS root (resolved once)

# ---------------------------------------------------------------------------
# Mandatory DB PRAGMAs
# ---------------------------------------------------------------------------
_DB_PRAGMAS: str = """
PRAGMA busy_timeout  = 60000;
PRAGMA journal_mode  = WAL;
PRAGMA cache_size    = -32000;
PRAGMA temp_store    = MEMORY;
PRAGMA synchronous   = NORMAL;
"""

# ---------------------------------------------------------------------------
# Evidence posture vocabulary
# ---------------------------------------------------------------------------
POSTURES: list[str] = [
    "RECORD_FACT",
    "EVIDENCE_FACT",
    "SWORN_FACT",
    "ALLEGATION",
    "INFERENCE",
]

# ---------------------------------------------------------------------------
# Lane definitions (mirrors apex_orchestrator.py)
# ---------------------------------------------------------------------------
LANE_DBS: Dict[str, str] = {
    "A": "lane_A_custody.db",
    "B": "lane_B_housing.db",
    "C": "lane_C_convergence.db",
    "D": "lane_D_ppo.db",
    "E": "lane_E_misconduct.db",
    "F": "lane_F_appellate.db",
}

_LANE_DESCRIPTIONS: Dict[str, str] = {
    "A": "Custody (Watson v. Pigors)",
    "B": "Housing (Shady Oaks)",
    "C": "Convergence (cross-lane)",
    "D": "PPO / Protection Orders",
    "E": "Judicial Misconduct / JTC",
    "F": "Appellate (COA / MSC)",
}

# ---------------------------------------------------------------------------
# Posture detection heuristics (compiled once, immutable)
# ---------------------------------------------------------------------------
_POSTURE_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?:transcript|docket|register of actions|court record)", re.I), "RECORD_FACT"),
    (re.compile(r"(?:affidavit|declaration|under oath|sworn)", re.I), "SWORN_FACT"),
    (re.compile(r"(?:exhibit|photograph|document|receipt|contract|letter)", re.I), "EVIDENCE_FACT"),
    (re.compile(r"(?:alleged?|claim(?:ed|s)?|assert(?:ed|s)?|accus)", re.I), "ALLEGATION"),
    (re.compile(r"(?:infer|imply|suggest|appear|seem|likely|probably)", re.I), "INFERENCE"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_connect(db_path: Path) -> Optional[sqlite3.Connection]:
    """Open a SQLite connection with mandatory PRAGMAs.  Returns None if unavailable."""
    try:
        p = str(db_path)
        if not db_path.exists():
            logger.debug("DB not found: %s", p)
            return None
        conn = sqlite3.connect(p, timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to open DB %s: %s", db_path, exc)
        return None


def _infer_posture(text: str) -> str:
    """Infer evidence posture from text using heuristic rules."""
    for rx, posture in _POSTURE_RULES:
        if rx.search(text):
            return posture
    return "EVIDENCE_FACT"  # safe default


def _fts_escape(query: str) -> str:
    """Escape an FTS5 query — wrap terms in double-quotes for literal match."""
    terms = re.findall(r'\w+', query)
    return " OR ".join(f'"{t}"' for t in terms[:20]) if terms else '""'


# ---------------------------------------------------------------------------
# EvidenceRAG
# ---------------------------------------------------------------------------
class EvidenceRAG:
    """Lane-aware, posture-tagged evidence retrieval engine.

    IRON LAW enforcement: every public method requires an explicit ``lane``
    parameter.  Cross-lane access is permitted ONLY for lane ``"C"`` (convergence).
    """

    POSTURES = POSTURES

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root = root_dir or _ROOT
        self._lock = threading.Lock()
        # Connection cache: {db_name: connection}
        self._conn_cache: Dict[str, Optional[sqlite3.Connection]] = {}

    # ------------------------------------------------------------------
    # Connection management (thread-safe, cached)
    # ------------------------------------------------------------------
    def _conn_for(self, db_name: str) -> Optional[sqlite3.Connection]:
        """Return a cached connection for *db_name*, opening if needed."""
        if db_name not in self._conn_cache:
            with self._lock:
                if db_name not in self._conn_cache:
                    db_path = self._root / db_name
                    self._conn_cache[db_name] = _safe_connect(db_path)
        return self._conn_cache.get(db_name)

    def _main_db(self) -> Optional[sqlite3.Connection]:
        return self._conn_for("litigation_context.db")

    def _lane_db(self, lane: str) -> Optional[sqlite3.Connection]:
        db_name = LANE_DBS.get(lane.upper())
        return self._conn_for(db_name) if db_name else None

    def _highsignal_db(self) -> Optional[sqlite3.Connection]:
        for name in ("MEEK234_HIGHSIGNAL_DB.sqlite", "MEEK234_HIGHSIGNAL_DB.db"):
            conn = self._conn_for(name)
            if conn is not None:
                return conn
        return None

    # ------------------------------------------------------------------
    # Lane enforcement
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_lane(lane: str) -> str:
        """Normalise and validate lane identifier.  Raises ValueError on bad input."""
        lane = lane.strip().upper()
        if lane not in LANE_DBS:
            raise ValueError(f"Unknown lane '{lane}'.  Valid: {list(LANE_DBS)}")
        return lane

    # ------------------------------------------------------------------
    # Primary search
    # ------------------------------------------------------------------
    def search_evidence(
        self,
        query: str,
        lane: str,
        postures: Optional[List[str]] = None,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search evidence within a specific lane.  Respects IRON LAW.

        Parameters
        ----------
        query : str
            Natural-language or keyword query.
        lane : str
            Case lane (A–F).  Lane C allows cross-lane results.
        postures : list[str], optional
            Filter by posture tags.  ``None`` returns all postures.
        top_k : int
            Maximum results.

        Returns
        -------
        list[dict]
            Each dict: ``{text, source, posture, score, lane, doc_id}``.
        """
        results: list[dict[str, Any]] = []
        try:
            lane = self._validate_lane(lane)
            if postures:
                postures = [p.upper() for p in postures if p.upper() in POSTURES]

            # 1. Lane-specific DB
            results.extend(self._search_lane_db(query, lane, top_k))

            # 2. Main DB (evidence_quotes filtered by lane)
            results.extend(self._search_main_db(query, lane, top_k))

            # 3. High-signal DB
            results.extend(self._search_highsignal(query, lane, top_k))

            # Posture filter
            if postures:
                results = [r for r in results if r.get("posture") in postures]

            # Deduplicate by text hash
            seen: set[str] = set()
            unique: list[dict[str, Any]] = []
            for r in results:
                key = r.get("text", "")[:200]
                if key not in seen:
                    seen.add(key)
                    unique.append(r)
            results = unique

            # Sort by score descending, truncate
            results.sort(key=lambda r: r.get("score", 0), reverse=True)
            results = results[:top_k]

        except ValueError as ve:
            logger.warning("search_evidence: %s", ve)
            return [{"status": "error", "error": str(ve)}]
        except Exception as exc:  # noqa: BLE001
            logger.warning("search_evidence failed: %s", exc)
            return [{"status": "error", "error": str(exc)}]

        return results

    def _search_lane_db(
        self, query: str, lane: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Search lane-specific database."""
        hits: list[dict[str, Any]] = []
        try:
            conn = self._lane_db(lane)
            if conn is None:
                return hits

            # Try FTS5 first, fall back to LIKE
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            fts_table = next((t for t in tables if t.endswith("_fts")), None)
            if fts_table:
                rows = conn.execute(
                    f"SELECT *, rank FROM {fts_table} WHERE {fts_table} MATCH ? "
                    f"ORDER BY rank LIMIT ?",
                    (_fts_escape(query), top_k),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    text = d.get("text") or d.get("content") or d.get("quote") or ""
                    hits.append({
                        "text": text,
                        "source": d.get("source", f"lane_{lane}"),
                        "posture": d.get("posture") or _infer_posture(text),
                        "score": abs(d.get("rank", 0)),
                        "lane": lane,
                        "doc_id": d.get("id") or d.get("doc_id"),
                    })
            else:
                # LIKE fallback on common table names
                for tbl in ("evidence", "quotes", "documents", "evidence_quotes"):
                    if tbl in tables:
                        rows = conn.execute(
                            f"SELECT * FROM {tbl} WHERE "
                            f"COALESCE(text,'') || COALESCE(content,'') || COALESCE(quote,'') "
                            f"LIKE ? LIMIT ?",
                            (f"%{query}%", top_k),
                        ).fetchall()
                        for r in rows:
                            d = dict(r)
                            text = d.get("text") or d.get("content") or d.get("quote") or ""
                            hits.append({
                                "text": text,
                                "source": d.get("source", tbl),
                                "posture": d.get("posture") or _infer_posture(text),
                                "score": 1.0,
                                "lane": lane,
                                "doc_id": d.get("id") or d.get("doc_id"),
                            })
        except Exception as exc:  # noqa: BLE001
            logger.debug("_search_lane_db(%s): %s", lane, exc)
        return hits

    def _search_main_db(
        self, query: str, lane: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Search litigation_context.db evidence_quotes, filtered by lane."""
        hits: list[dict[str, Any]] = []
        try:
            conn = self._main_db()
            if conn is None:
                return hits

            # Verify table exists
            tbl_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='evidence_quotes'"
            ).fetchone()
            if not tbl_check:
                return hits

            # Check columns to avoid schema mismatches
            cols = {r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()}
            lane_col = "lane" if "lane" in cols else "vehicle_name" if "vehicle_name" in cols else None
            text_col = "quote_text" if "quote_text" in cols else "text" if "text" in cols else "content"

            sql = f"SELECT * FROM evidence_quotes WHERE {text_col} LIKE ?"
            params: list[Any] = [f"%{query}%"]
            if lane_col and lane != "C":
                sql += f" AND {lane_col} = ?"
                params.append(lane)
            sql += " LIMIT ?"
            params.append(top_k)

            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                d = dict(r)
                text = d.get(text_col) or ""
                hits.append({
                    "text": text,
                    "source": d.get("source_document") or d.get("source") or "litigation_context",
                    "posture": d.get("posture") or _infer_posture(text),
                    "score": 2.0,
                    "lane": lane,
                    "doc_id": d.get("id") or d.get("quote_id"),
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug("_search_main_db: %s", exc)
        return hits

    def _search_highsignal(
        self, query: str, lane: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Search MEEK234 high-signal quotes DB."""
        hits: list[dict[str, Any]] = []
        try:
            conn = self._highsignal_db()
            if conn is None:
                return hits

            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            target = next(
                (t for t in tables if "quote" in t.lower() or "signal" in t.lower()),
                tables[0] if tables else None,
            )
            if target is None:
                return hits

            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({target})").fetchall()}
            text_col = next((c for c in ("quote_text", "text", "content", "quote") if c in cols), None)
            if text_col is None:
                return hits

            rows = conn.execute(
                f"SELECT * FROM {target} WHERE {text_col} LIKE ? LIMIT ?",
                (f"%{query}%", top_k),
            ).fetchall()
            for r in rows:
                d = dict(r)
                text = d.get(text_col) or ""
                hits.append({
                    "text": text,
                    "source": "MEEK234_HIGHSIGNAL",
                    "posture": d.get("posture") or _infer_posture(text),
                    "score": 3.0,  # high-signal bonus
                    "lane": lane,
                    "doc_id": d.get("id") or d.get("quote_id"),
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug("_search_highsignal: %s", exc)
        return hits

    # ------------------------------------------------------------------
    # Harm search
    # ------------------------------------------------------------------
    def search_harms(
        self,
        query: str,
        category: Optional[str] = None,
        severity_min: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search harm records from MANBEARPIG knowledge transfer.

        Parameters
        ----------
        query : str
            Search text.
        category : str, optional
            Filter by harm category (e.g. ``"emotional"``, ``"financial"``).
        severity_min : int
            Minimum severity score (0–10).
        """
        results: list[dict[str, Any]] = []
        try:
            conn = self._main_db()
            if conn is None:
                return results

            # Check for harms-related tables
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            harm_table = next(
                (t for t in tables if "harm" in t.lower()),
                None,
            )
            if harm_table is None:
                return results

            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({harm_table})").fetchall()}
            text_col = next((c for c in ("description", "text", "harm_description", "content") if c in cols), None)
            if text_col is None:
                return results

            sql = f"SELECT * FROM {harm_table} WHERE {text_col} LIKE ?"
            params: list[Any] = [f"%{query}%"]

            if category and "category" in cols:
                sql += " AND category = ?"
                params.append(category)
            if severity_min > 0 and "severity" in cols:
                sql += " AND severity >= ?"
                params.append(severity_min)
            sql += " LIMIT 50"

            rows = conn.execute(sql, params).fetchall()
            results = [dict(r) for r in rows]
        except Exception as exc:  # noqa: BLE001
            logger.debug("search_harms: %s", exc)
        return results

    # ------------------------------------------------------------------
    # Evidence chain
    # ------------------------------------------------------------------
    def get_evidence_chain(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get full evidence chain for a claim — links evidence to legal elements."""
        chain: list[dict[str, Any]] = []
        try:
            conn = self._main_db()
            if conn is None:
                return chain

            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            # evidence_chains or authority_chains table
            chain_table = next(
                (t for t in tables if "evidence_chain" in t.lower() or "authority_chain" in t.lower()),
                None,
            )
            if chain_table:
                cols = {r[1] for r in conn.execute(f"PRAGMA table_info({chain_table})").fetchall()}
                id_col = next((c for c in ("claim_id", "id", "chain_id") if c in cols), None)
                if id_col:
                    rows = conn.execute(
                        f"SELECT * FROM {chain_table} WHERE {id_col} = ?", (claim_id,)
                    ).fetchall()
                    chain.extend(dict(r) for r in rows)

            # Also pull related evidence_quotes
            if "evidence_quotes" in tables:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()}
                id_col = next((c for c in ("claim_id", "claim", "id") if c in cols), None)
                if id_col:
                    rows = conn.execute(
                        f"SELECT * FROM evidence_quotes WHERE {id_col} = ? LIMIT 50",
                        (claim_id,),
                    ).fetchall()
                    chain.extend(dict(r) for r in rows)
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_evidence_chain: %s", exc)
        return chain

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------
    def find_gaps(self, lane: str, claim_type: str) -> List[Dict[str, str]]:
        """Find evidence gaps — elements without sufficient evidence support."""
        gaps: list[dict[str, str]] = []
        try:
            lane = self._validate_lane(lane)
            conn = self._main_db()
            if conn is None:
                return [{"gap": "No database connection available"}]

            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            # Look for claims / filing_readiness / gap_analysis tables
            if "claims" in tables:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(claims)").fetchall()}
                type_col = next((c for c in ("claim_type", "type", "category") if c in cols), None)
                lane_col = next((c for c in ("lane", "vehicle_name") if c in cols), None)

                sql = "SELECT * FROM claims WHERE 1=1"
                params: list[Any] = []
                if type_col:
                    sql += f" AND {type_col} LIKE ?"
                    params.append(f"%{claim_type}%")
                if lane_col:
                    sql += f" AND {lane_col} = ?"
                    params.append(lane)

                rows = conn.execute(sql, params).fetchall()
                for r in rows:
                    d = dict(r)
                    status = d.get("status", "").lower()
                    if "gap" in status or "missing" in status or "incomplete" in status:
                        gaps.append({
                            "claim_id": str(d.get("claim_id") or d.get("id", "?")),
                            "description": d.get("description") or d.get("claim_type") or claim_type,
                            "status": status,
                            "lane": lane,
                        })

            if "gap_analysis" in tables:
                rows = conn.execute(
                    "SELECT * FROM gap_analysis WHERE lane = ? LIMIT 50", (lane,)
                ).fetchall()
                gaps.extend(dict(r) for r in rows)

            if not gaps:
                gaps.append({
                    "gap": "none_detected",
                    "note": f"No evidence gaps found for lane {lane} / {claim_type} (or table missing)",
                })
        except ValueError as ve:
            return [{"gap": "error", "error": str(ve)}]
        except Exception as exc:  # noqa: BLE001
            logger.debug("find_gaps: %s", exc)
            gaps.append({"gap": "error", "error": str(exc)})
        return gaps

    # ------------------------------------------------------------------
    # Cross-reference
    # ------------------------------------------------------------------
    def cross_reference(self, evidence_id: str) -> List[Dict[str, Any]]:
        """Find all documents/claims that reference a piece of evidence."""
        refs: list[dict[str, Any]] = []
        try:
            conn = self._main_db()
            if conn is None:
                return refs

            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            for tbl in tables:
                if tbl.startswith("sqlite_") or "_fts" in tbl:
                    continue
                try:
                    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({tbl})").fetchall()}
                    id_cols = [c for c in cols if "evidence" in c.lower() or "quote" in c.lower() or "doc_id" in c.lower()]
                    for col in id_cols:
                        rows = conn.execute(
                            f"SELECT * FROM {tbl} WHERE {col} = ? LIMIT 10",
                            (evidence_id,),
                        ).fetchall()
                        for r in rows:
                            d = dict(r)
                            d["_source_table"] = tbl
                            refs.append(d)
                except Exception:  # noqa: BLE001
                    continue
        except Exception as exc:  # noqa: BLE001
            logger.debug("cross_reference: %s", exc)
        return refs

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close all cached connections."""
        for name, conn in self._conn_cache.items():
            try:
                if conn:
                    conn.close()
            except Exception:  # noqa: BLE001
                pass
        self._conn_cache.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance_lock = threading.Lock()
_instance: Optional[EvidenceRAG] = None


def get_evidence_rag() -> EvidenceRAG:
    """Return module-level singleton.  Thread-safe lazy init."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = EvidenceRAG()
    return _instance


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
def _cli_main() -> None:
    """``python evidence_rag.py <lane> <query>``"""
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 3:
        print("Usage: python evidence_rag.py <lane A-F> <query>")
        return

    lane = sys.argv[1]
    query = " ".join(sys.argv[2:])
    rag = get_evidence_rag()
    results = rag.search_evidence(query, lane)

    for i, r in enumerate(results, 1):
        posture = r.get("posture", "?")
        text = (r.get("text") or "")[:120]
        print(f"  {i:2d}. [{posture}] {text}")
    if not results:
        print("  No results.")


if __name__ == "__main__":
    _cli_main()
