#!/usr/bin/env python3
"""
APEX Query Expansion v2 — Expands queries with synonyms and related terms
==========================================================================
When LLM available: neural synonym generation.
When not: curated legal synonym dictionary + DB co-occurrence mining.

Coexists with query_expander.py (v1). This module adds:
- APEX_LLM_ENABLED gating for neural expansion
- Larger curated synonym dictionary (15+ categories)
- Multi-strategy expansion (synonyms + authority refs + co-occurrence)
- Configurable max_expansions

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
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
DEFAULT_DB = os.environ.get(
    "LITIGATION_DB_PATH",
    str(_MODULE_DIR.parent.parent.parent / "litigation_context.db"),
)

# GGUF model path for neural expansion
GGUF_PATH = str(_MODULE_DIR / "gguf" / "qwen2.5-1.5b-instruct-q4_k_m.gguf")


class QueryExpansionV2:
    """APEX Query Expansion with curated synonyms and optional neural generation.

    Three expansion strategies (applied in order):
    1. Curated legal synonym dictionary (always available)
    2. DB co-occurrence mining (when DB available)
    3. Neural synonym generation (when APEX_LLM_ENABLED + model available)
    """

    # Curated legal synonyms (always available)
    LEGAL_SYNONYMS: Dict[str, List[str]] = {
        "disqualification": ["recusal", "removal", "bias challenge", "MCR 2.003",
                             "judicial disqualification", "motion to disqualify"],
        "custody": ["parenting time", "physical custody", "legal custody", "placement",
                     "custodial environment", "MCL 722.23", "best interest"],
        "eviction": ["constructive eviction", "wrongful eviction", "unlawful detainer",
                      "forcible entry", "summary proceedings"],
        "protection order": ["PPO", "restraining order", "no contact order",
                              "MCL 600.2950", "personal protection order"],
        "misconduct": ["judicial misconduct", "ethical violation", "canon violation",
                        "MCR 9.104", "benchbook violation", "JTC complaint"],
        "damages": ["harm", "injury", "loss", "economic damages", "non-economic damages",
                     "compensatory", "punitive", "treble damages"],
        "appeal": ["appellate review", "application for leave", "claim of appeal",
                    "MCR 7.204", "MCR 7.205", "court of appeals"],
        "service": ["service of process", "personal service", "substitute service",
                     "MCR 2.105", "proof of service", "certificate of service"],
        "discovery": ["interrogatories", "depositions", "requests for production",
                       "MCR 2.302", "subpoena", "motion to compel"],
        "contempt": ["civil contempt", "criminal contempt", "failure to comply",
                      "MCL 600.1701", "MCR 3.606", "purge condition"],
        "alienation": ["parental alienation", "interference", "denial of parenting time",
                        "MCL 722.23(j)", "factor j", "gatekeeping"],
        "conspiracy": ["coordinated action", "concerted effort", "agreement to violate",
                        "42 USC 1983", "Monell", "pattern and practice"],
        "habitability": ["implied warranty", "fitness for use", "building code violation",
                          "truth in renting", "MCL 125", "housing code"],
        "ex parte": ["without notice", "one-sided", "unilateral communication",
                      "ex parte order", "MCR 2.003(C)"],
        "void judgment": ["jurisdictional defect", "due process violation", "collateral attack",
                           "subject matter jurisdiction", "void ab initio"],
    }

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._llm = None
        self._llm_loaded = False
        self._lock = threading.Lock()
        # Build reverse lookup for efficient matching
        self._lookup: Dict[str, List[str]] = {}
        for key, synonyms in self.LEGAL_SYNONYMS.items():
            self._lookup[key.lower()] = synonyms
            for syn in synonyms:
                norm = syn.lower()
                if norm not in self._lookup:
                    self._lookup[norm] = synonyms

    # ── LLM Loading ────────────────────────────────────────────────

    def _load_llm(self):
        """Lazy-load GGUF model for neural synonym generation."""
        if self._llm_loaded:
            return self._llm
        with self._lock:
            if self._llm_loaded:
                return self._llm
            self._llm_loaded = True
            if not APEX_LLM_ENABLED:
                logger.info("[QEv2] APEX_LLM_ENABLED=false — curated synonyms only")
                return None
            if not os.path.exists(GGUF_PATH):
                logger.info("[QEv2] GGUF model not found — curated synonyms only")
                return None
            try:
                from llama_cpp import Llama
                self._llm = Llama(
                    model_path=GGUF_PATH, n_ctx=1024, n_threads=4, verbose=False,
                )
                logger.info("[QEv2] GGUF model loaded for neural expansion")
            except Exception as e:
                logger.warning("[QEv2] Model load failed: %s — curated synonyms only", e)
                self._llm = None
            return self._llm

    # ── DB Connection ──────────────────────────────────────────────

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        """Open a read-only WAL connection."""
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA query_only=ON")
            return conn
        except Exception as e:
            logger.warning("[QEv2] DB connect failed: %s", e)
            return None

    # ── Public API ─────────────────────────────────────────────────

    def expand(self, query: str, max_expansions: int = 5) -> list:
        """Expand query into multiple variants. Returns list of expanded queries.

        Applies three strategies in order:
        1. Curated synonym expansion
        2. DB co-occurrence expansion
        3. Neural expansion (when available)

        Returns list of unique expanded query variants (original always first).
        """
        try:
            if not query or not query.strip():
                return [query] if query else []

            variants: List[str] = [query]

            # Strategy 1: Curated synonyms
            synonym_expanded = self._expand_with_synonyms(query, max_expansions)
            if synonym_expanded and synonym_expanded != query:
                variants.append(synonym_expanded)

            # Strategy 2: DB co-occurrence
            try:
                cooc_expanded = self._expand_with_cooccurrence(query, max_expansions)
                if cooc_expanded and cooc_expanded != query:
                    variants.append(cooc_expanded)
            except Exception as e:
                logger.debug("[QEv2] Co-occurrence expansion failed: %s", e)

            # Strategy 3: Neural expansion (when available)
            llm = self._load_llm()
            if llm is not None:
                try:
                    neural_expanded = self._expand_neural(query, llm, max_expansions)
                    if neural_expanded and neural_expanded != query:
                        variants.append(neural_expanded)
                except Exception as e:
                    logger.debug("[QEv2] Neural expansion failed: %s", e)

            # Deduplicate and limit
            seen: Set[str] = set()
            unique_variants: List[str] = []
            for v in variants:
                normalized = " ".join(v.split()).strip()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    unique_variants.append(normalized)

            return unique_variants[:max_expansions + 1]
        except Exception as e:
            logger.error("[QEv2] expand failed: %s", e, exc_info=True)
            return [query] if query else []

    def get_synonyms(self, term: str) -> list:
        """Get synonyms for a legal term."""
        try:
            if not term:
                return []

            norm = term.lower().strip()

            # Direct lookup
            if norm in self._lookup:
                return list(self._lookup[norm])

            # Substring match
            matches: List[str] = []
            for key, syns in self.LEGAL_SYNONYMS.items():
                if norm in key.lower() or key.lower() in norm:
                    matches.extend(syns)
            return list(set(matches)) if matches else []
        except Exception as e:
            logger.warning("[QEv2] get_synonyms failed: %s", e)
            return []

    # ── Expansion strategies ───────────────────────────────────────

    def _expand_with_synonyms(self, query: str, max_expansions: int) -> str:
        """Expand query using curated legal synonym dictionary."""
        try:
            q_lower = query.lower()
            expansions: Set[str] = set()

            # Multi-word phrase matches (check longer phrases first)
            for key in sorted(self.LEGAL_SYNONYMS.keys(), key=len, reverse=True):
                if key.lower() in q_lower:
                    for syn in self.LEGAL_SYNONYMS[key]:
                        if syn.lower() not in q_lower:
                            expansions.add(syn)
                        if len(expansions) >= max_expansions * 2:
                            break

            # Single word matches
            tokens = re.findall(r"[\w'.]+", q_lower)
            for token in tokens:
                if token in self._lookup:
                    for syn in self._lookup[token]:
                        if syn.lower() not in q_lower:
                            expansions.add(syn)

            if not expansions:
                return query

            # Take top expansions, prefer shorter ones (more likely to be precise)
            sorted_expansions = sorted(expansions, key=len)[:max_expansions]
            return query + " " + " ".join(sorted_expansions)
        except Exception as e:
            logger.debug("[QEv2] synonym expansion failed: %s", e)
            return query

    def _expand_with_cooccurrence(self, query: str, max_terms: int = 5) -> str:
        """Expand query using DB co-occurrence mining."""
        conn = self._get_conn()
        if conn is None:
            return query

        try:
            tokens = re.findall(r'\w+', query.lower())
            safe_tokens = [t for t in tokens if len(t) > 2]
            if not safe_tokens:
                return query

            fts_query = " OR ".join(f'"{t}"' for t in safe_tokens[:5])

            # Try FTS5 search
            try:
                rows = conn.execute(
                    "SELECT quote_text FROM evidence_quotes_fts "
                    "WHERE evidence_quotes_fts MATCH ? LIMIT 100",
                    (fts_query,)
                ).fetchall()
            except Exception:
                # Fallback: LIKE search
                like_clauses = " OR ".join(
                    f"quote_text LIKE '%{t}%'" for t in safe_tokens[:3]
                )
                rows = conn.execute(
                    f"SELECT quote_text FROM evidence_quotes WHERE {like_clauses} LIMIT 100"
                ).fetchall()

            # Count co-occurring terms
            stop_words = {
                "the", "and", "for", "that", "this", "with", "was", "are",
                "not", "but", "have", "has", "had", "been", "from", "they",
                "will", "would", "could", "should", "their", "there", "what",
                "which", "when", "where", "who", "how", "can", "does", "did",
            }
            query_set = set(tokens)
            co_counter: Counter = Counter()

            for (text,) in rows:
                if not text:
                    continue
                words = re.findall(r'\w+', text.lower())
                for w in words:
                    if len(w) > 3 and w not in stop_words and w not in query_set:
                        co_counter[w] += 1

            top_terms = [t for t, _ in co_counter.most_common(max_terms)]
            if top_terms:
                return query + " " + " ".join(top_terms)
            return query
        except Exception as e:
            logger.debug("[QEv2] co-occurrence expansion failed: %s", e)
            return query
        finally:
            conn.close()

    def _expand_neural(self, query: str, llm: Any, max_expansions: int) -> str:
        """Expand query using GGUF model for synonym generation."""
        try:
            prompt = (
                f"List {max_expansions} legal synonyms or related terms for this query. "
                f"Output ONLY the terms, comma-separated.\n\n"
                f"Query: {query[:200]}\n\nRelated terms:"
            )
            resp = llm(prompt, max_tokens=100, temperature=0.3, stop=["\n\n"])
            text = resp["choices"][0]["text"].strip()
            terms = [t.strip() for t in text.split(",") if t.strip() and len(t.strip()) > 2]
            if terms:
                return query + " " + " ".join(terms[:max_expansions])
            return query
        except Exception as e:
            logger.debug("[QEv2] neural expansion failed: %s", e)
            return query

    # ── Status & Self-Test ─────────────────────────────────────────

    def status(self) -> Dict:
        """Return engine status."""
        return {
            "engine": "APEX-QueryExpansionV2",
            "apex_llm_enabled": APEX_LLM_ENABLED,
            "synonym_categories": len(self.LEGAL_SYNONYMS),
            "total_synonyms": sum(len(v) for v in self.LEGAL_SYNONYMS.values()),
            "lookup_keys": len(self._lookup),
            "db_path": self.db_path,
            "db_available": os.path.exists(self.db_path),
            "model_loaded": self._llm is not None,
        }

    def self_test(self) -> Dict:
        """Run self-test with sample queries."""
        results = {"tests": [], "status": "pass"}
        try:
            # Test 1: Synonym expansion
            variants = self.expand("custody disqualification")
            results["tests"].append({
                "name": "expand_basic",
                "pass": len(variants) >= 1,
                "count": len(variants),
                "preview": [v[:80] for v in variants[:3]],
            })

            # Test 2: Get synonyms
            syns = self.get_synonyms("custody")
            results["tests"].append({
                "name": "get_synonyms",
                "pass": len(syns) > 0,
                "count": len(syns),
                "sample": syns[:3],
            })

            # Test 3: Unknown term
            syns2 = self.get_synonyms("xyznonexistent")
            results["tests"].append({
                "name": "unknown_term",
                "pass": isinstance(syns2, list),
                "count": len(syns2),
            })

            # Test 4: Empty query
            variants2 = self.expand("")
            results["tests"].append({
                "name": "empty_query",
                "pass": isinstance(variants2, list),
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

    qe = QueryExpansionV2()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "--self-test":
        print(json.dumps(qe.self_test(), indent=2, default=str))
    elif cmd == "--status":
        print(json.dumps(qe.status(), indent=2, default=str))
    elif cmd == "--synonyms":
        term = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        print(json.dumps(qe.get_synonyms(term), indent=2, default=str))
    elif cmd not in ("status", "--status"):
        query = " ".join(sys.argv[1:])
        variants = qe.expand(query)
        for i, v in enumerate(variants):
            print(f"  [{i}] {v[:120]}")
    else:
        print(json.dumps(qe.status(), indent=2, default=str))
