#!/usr/bin/env python3
"""
APEX Citation Grounding — Every claim must be grounded in cited authority.
=========================================================================
Validates MCR, MCL, case law citations against litigation_context.db.
Zero hallucinated citations. Extracts, verifies, and tags claims with
their source authorities.

Shadow-programmed: APEX_LLM_ENABLED gates neural features.
NEVER crashes — all methods try/except with fallbacks.
Never sets CWD to repo root (shadow modules).
Uses Path(__file__).parent for paths.
DB: busy_timeout=60000, journal_mode=WAL, cache_size=-32000.
Thread-safe, UTF-8 safe, logging, type hints.
"""

import json
import logging
import os
import re
import sqlite3
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
DEFAULT_DB = os.environ.get(
    "LITIGATION_DB_PATH",
    str(_MODULE_DIR.parent.parent.parent / "litigation_context.db"),
)


class CitationGrounding:
    """Validates and grounds legal citations against the litigation database.

    Supports MCR, MCL, case law (Mich App / Mich), USC, and MRE citations.
    Verifies each citation exists in the DB and tags uncited claims.
    """

    # ── Regex patterns for Michigan citations ──────────────────────
    MCR_PATTERN: str = r'MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)'
    MCL_PATTERN: str = r'MCL\s+(\d+\.\d+[a-z]*(?:\([0-9]+\))*)'
    CASE_PATTERN: str = r'(\d+\s+Mich\.?\s*(?:App\.?)?\s+\d+)'
    USC_PATTERN: str = r'(\d+\s+U\.?S\.?C\.?\s+(?:§\s*)?\d+)'
    MRE_PATTERN: str = r'MRE\s+(\d+(?:\([a-z0-9]+\))*)'

    # Combined citation regex (order matters for priority)
    _CITATION_RE = re.compile(
        r'(?:MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*)'
        r'|(?:MCL\s+\d+\.\d+[a-z]*(?:\([0-9]+\))*)'
        r'|(?:MRE\s+\d+(?:\([a-z0-9]+\))*)'
        r'|(?:\d+\s+U\.?S\.?C\.?\s+(?:§\s*)?\d+)'
        r'|(?:\d+\s+Mich\.?\s*(?:App\.?)?\s+\d+)',
        re.IGNORECASE
    )

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    # ── DB Connection ──────────────────────────────────────────────

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        """Open a read-only WAL connection with APEX PRAGMAs."""
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.warning("[CitationGrounding] DB connect failed: %s", e)
            return None

    # ── Public API ─────────────────────────────────────────────────

    def ground(self, text: str) -> dict:
        """Validate all citations in text.

        Returns:
            {
                valid: [{"citation": str, "type": str, "source": str, "text_snippet": str}],
                invalid: [{"citation": str, "type": str, "reason": str}],
                unverified: [{"citation": str, "type": str, "reason": str}],
                total: int,
                grounding_score: float  # 0.0 - 1.0
            }
        """
        try:
            citations = self.extract_citations(text)
            valid: List[Dict] = []
            invalid: List[Dict] = []
            unverified: List[Dict] = []

            for cite_info in citations:
                cite_str = cite_info["citation"]
                result = self.verify_citation(cite_str)

                if result.get("exists"):
                    valid.append({
                        "citation": cite_str,
                        "type": cite_info["type"],
                        "source": result.get("source", "db"),
                        "text_snippet": result.get("text", "")[:200],
                        "position": cite_info.get("position", 0),
                    })
                elif result.get("error"):
                    unverified.append({
                        "citation": cite_str,
                        "type": cite_info["type"],
                        "reason": result.get("error", "verification failed"),
                    })
                else:
                    invalid.append({
                        "citation": cite_str,
                        "type": cite_info["type"],
                        "reason": "not found in litigation database",
                    })

            total = len(citations)
            score = len(valid) / total if total > 0 else 1.0

            return {
                "valid": valid,
                "invalid": invalid,
                "unverified": unverified,
                "total": total,
                "grounding_score": round(score, 3),
            }
        except Exception as e:
            logger.error("[CitationGrounding] ground() failed: %s", e, exc_info=True)
            return {
                "valid": [], "invalid": [], "unverified": [],
                "total": 0, "grounding_score": 0.0, "error": str(e),
            }

    def extract_citations(self, text: str) -> list:
        """Extract all citations from text with their positions and types.

        Returns:
            List of {"citation": str, "type": str, "position": int}
        """
        try:
            if not text:
                return []

            results: List[Dict] = []
            seen: set = set()

            for match in self._CITATION_RE.finditer(text):
                cite = match.group(0).strip()
                normalized = re.sub(r'\s+', ' ', cite).strip()
                if normalized in seen:
                    continue
                seen.add(normalized)

                cite_type = self._classify_citation(normalized)
                results.append({
                    "citation": normalized,
                    "type": cite_type,
                    "position": match.start(),
                })

            return results
        except Exception as e:
            logger.warning("[CitationGrounding] extract_citations failed: %s", e)
            return []

    def verify_citation(self, citation: str) -> dict:
        """Verify a single citation against the DB.

        Returns:
            {exists: bool, text: str, source: str} or {exists: False, error: str}
        """
        try:
            # Check cache first
            cache_key = citation.upper().strip()
            with self._lock:
                if cache_key in self._cache:
                    return self._cache[cache_key]

            conn = self._get_conn()
            if conn is None:
                return {"exists": False, "error": "database unavailable"}

            try:
                result = self._search_citation_in_db(conn, citation)
                with self._lock:
                    self._cache[cache_key] = result
                return result
            finally:
                conn.close()
        except Exception as e:
            logger.warning("[CitationGrounding] verify_citation failed for '%s': %s", citation, e)
            return {"exists": False, "error": str(e)}

    def add_citations(self, text: str, claims: list = None) -> str:
        """Add [CITE:xxx] tags to uncited claims.

        Uses retrieval to find the best citation for each uncited sentence.
        If claims is None, splits text into sentences as claims.

        Returns:
            Text with [CITE:xxx] tags appended to uncited sentences.
        """
        try:
            if not text:
                return text

            # Split into sentences if no claims provided
            if claims is None:
                claims = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 20]

            existing_cites = set(c["citation"] for c in self.extract_citations(text))
            tagged_parts: List[str] = []

            for claim in claims:
                claim_cites = self.extract_citations(claim)
                if claim_cites:
                    tagged_parts.append(claim)
                    continue

                # Try to find a citation for this claim
                best_cite = self._find_citation_for_claim(claim)
                if best_cite:
                    tagged_parts.append(f"{claim} [CITE:{best_cite}]")
                else:
                    tagged_parts.append(f"{claim} [CITE:NEEDED]")

            return " ".join(tagged_parts)
        except Exception as e:
            logger.warning("[CitationGrounding] add_citations failed: %s", e)
            return text

    # ── Internal helpers ───────────────────────────────────────────

    def _classify_citation(self, citation: str) -> str:
        """Classify a citation string into its type."""
        upper = citation.upper()
        if upper.startswith("MCR"):
            return "MCR"
        elif upper.startswith("MCL"):
            return "MCL"
        elif upper.startswith("MRE"):
            return "MRE"
        elif "U.S.C" in upper or "USC" in upper:
            return "USC"
        elif "MICH" in upper:
            return "case_law"
        else:
            return "unknown"

    def _search_citation_in_db(self, conn: sqlite3.Connection, citation: str) -> dict:
        """Search for a citation across multiple DB tables."""
        # Normalize the citation for searching
        search_term = re.sub(r'\s+', ' ', citation).strip()
        search_like = f"%{search_term}%"

        # Tables and columns to search
        search_targets = [
            ("auth_rules", "full_text", "rule_id"),
            ("rules_text", "context", "rule_id"),
            ("evidence_quotes", "quote_text", "quote_id"),
            ("authority_chains", "authority_text", "chain_id"),
        ]

        for table, text_col, id_col in search_targets:
            try:
                row = conn.execute(
                    f"SELECT {id_col}, {text_col} FROM {table} "
                    f"WHERE {text_col} LIKE ? LIMIT 1",
                    (search_like,)
                ).fetchone()
                if row:
                    return {
                        "exists": True,
                        "text": str(row[1])[:300] if row[1] else "",
                        "source": f"{table}.{id_col}={row[0]}",
                    }
            except Exception:
                continue

        # Try FTS5 tables as fallback
        fts_targets = [
            ("auth_rules_fts", "full_text"),
            ("rules_text_fts", "context"),
            ("evidence_quotes_fts", "quote_text"),
        ]
        safe_q = re.sub(r'[^\w\s.]', ' ', search_term).strip()
        tokens = [t for t in safe_q.split() if len(t) > 1]
        if tokens:
            fts_query = " AND ".join(f'"{t}"' for t in tokens[:4])
            for fts_table, text_col in fts_targets:
                try:
                    row = conn.execute(
                        f"SELECT {text_col} FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT 1",
                        (fts_query,)
                    ).fetchone()
                    if row:
                        return {
                            "exists": True,
                            "text": str(row[0])[:300] if row[0] else "",
                            "source": fts_table,
                        }
                except Exception:
                    continue

        return {"exists": False, "text": "", "source": ""}

    def _find_citation_for_claim(self, claim: str) -> Optional[str]:
        """Find the best citation for an uncited claim using keyword search."""
        try:
            conn = self._get_conn()
            if conn is None:
                return None

            try:
                # Extract key legal terms from claim
                words = re.findall(r'\w{4,}', claim.lower())
                legal_terms = [w for w in words if w not in {
                    "that", "this", "with", "from", "have", "been", "were",
                    "they", "their", "there", "which", "when", "where",
                    "court", "judge", "order", "also", "would", "should",
                }][:5]

                if not legal_terms:
                    return None

                # Search auth_rules_fts for matching authority
                fts_query = " OR ".join(f'"{t}"' for t in legal_terms)
                try:
                    row = conn.execute(
                        "SELECT full_text FROM auth_rules_fts "
                        "WHERE auth_rules_fts MATCH ? ORDER BY rank LIMIT 1",
                        (fts_query,)
                    ).fetchone()
                except Exception:
                    row = None

                if row and row[0]:
                    # Extract the first citation from the matched text
                    match = self._CITATION_RE.search(str(row[0]))
                    if match:
                        return match.group(0)

                return None
            finally:
                conn.close()
        except Exception as e:
            logger.debug("[CitationGrounding] _find_citation_for_claim failed: %s", e)
            return None

    # ── Status & Self-Test ─────────────────────────────────────────

    def status(self) -> Dict:
        """Return engine status."""
        return {
            "engine": "APEX-CitationGrounding",
            "apex_llm_enabled": APEX_LLM_ENABLED,
            "db_path": self.db_path,
            "db_available": os.path.exists(self.db_path),
            "cache_size": len(self._cache),
            "patterns": {
                "MCR": self.MCR_PATTERN,
                "MCL": self.MCL_PATTERN,
                "case_law": self.CASE_PATTERN,
                "USC": self.USC_PATTERN,
                "MRE": self.MRE_PATTERN,
            },
        }

    def self_test(self) -> Dict:
        """Run self-test with sample citations."""
        results = {"tests": [], "status": "pass"}
        try:
            # Test 1: Extract citations
            sample = "Under MCR 2.003(D)(1), a judge must disqualify. See MCL 722.23 and 123 Mich App 456."
            cites = self.extract_citations(sample)
            results["tests"].append({
                "name": "extract_citations",
                "pass": len(cites) >= 2,
                "count": len(cites),
                "citations": [c["citation"] for c in cites],
            })

            # Test 2: Ground citations
            grounding = self.ground(sample)
            results["tests"].append({
                "name": "ground",
                "pass": grounding["total"] >= 2,
                "total": grounding["total"],
                "score": grounding["grounding_score"],
            })

            # Test 3: Classify citation types
            types = {c["type"] for c in cites}
            results["tests"].append({
                "name": "classify_types",
                "pass": "MCR" in types,
                "types_found": list(types),
            })

            results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
        except Exception as e:
            results["status"] = "fail"
            results["error"] = str(e)
        return results


# ── CLI Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    cg = CitationGrounding()
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        print(json.dumps(cg.self_test(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        print(json.dumps(cg.status(), indent=2, default=str))
    elif len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        result = cg.ground(text)
        print(json.dumps(result, indent=2, default=str))
    else:
        print(json.dumps(cg.status(), indent=2, default=str))
