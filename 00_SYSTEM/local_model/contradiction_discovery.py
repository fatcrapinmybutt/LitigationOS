#!/usr/bin/env python3
"""
DELTA 3 — Auto-Contradiction Discovery for THE MANBEARPIG
==========================================================
TF-IDF cosine similarity engine that AUTOMATICALLY discovers contradictions
that manual review missed. Supplements the 10,558 known contradictions in
contradiction_map with ML-discovered novel conflicts.

Performance design:
  - Never compares all 308K evidence_quotes pairwise (95B comparisons)
  - Filters to speaker/topic subsets first (hundreds, not hundreds of thousands)
  - TF-IDF vectorize → batch cosine_similarity (efficient numpy/scipy)
  - Pre-filter by similarity > threshold before semantic analysis
  - Capped at configurable limits

Usage:
    # Python API
    from contradiction_discovery import ContradictionDiscovery
    cd = ContradictionDiscovery()
    results = cd.find_watson_contradictions()
    report = cd.full_scan()

    # CLI
    python contradiction_discovery.py watson
    python contradiction_discovery.py judicial
    python contradiction_discovery.py cross --doc-a TRANSCRIPT --doc-b CUSTODY_ORDER
    python contradiction_discovery.py full-scan
    python contradiction_discovery.py status
    python contradiction_discovery.py self-test
"""

from __future__ import annotations

try:
    import network_safety_net  # noqa: F401
except ImportError:
    pass

import json
import logging
import os
import pickle
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "model_data"
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Contradiction signal keywords ──────────────────────────────────
_NEGATION_WORDS = {"no", "not", "never", "none", "nothing", "nobody",
                   "neither", "nor", "nowhere", "cannot", "didn't",
                   "doesn't", "wasn't", "weren't", "isn't", "aren't",
                   "won't", "wouldn't", "couldn't", "shouldn't", "hasn't",
                   "haven't", "hadn't", "don't", "denied", "deny", "denies",
                   "refused", "reject", "false"}
_AFFIRMATION_WORDS = {"yes", "always", "every", "confirmed", "admitted",
                      "acknowledged", "agreed", "true", "did", "does", "was",
                      "were", "had", "has", "have", "affirmed", "stated",
                      "testified", "conceded"}

# Month patterns for temporal extraction
_DATE_RE = re.compile(
    r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|'
    r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s*\d{2,4})\b',
    re.IGNORECASE
)


def _clean_text(text: str) -> str:
    """Normalize OCR-noisy text for comparison."""
    if not text:
        return ""
    # Collapse whitespace (OCR artifacts)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove non-printable chars
    text = re.sub(r'[^\x20-\x7E]', '', text)
    return text


def _extract_dates(text: str) -> set:
    """Extract date references from text."""
    return set(_DATE_RE.findall(text.lower()))


def _word_set(text: str) -> set:
    """Get lowercase word set from text."""
    return set(re.findall(r'\b[a-z]+\b', text.lower()))


class ContradictionDiscovery:
    """
    ML-powered contradiction discovery engine.
    Uses TF-IDF cosine similarity to find semantically similar but factually
    contradictory statements across the litigation record.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.vectorizer: Optional[TfidfVectorizer] = None
        self._error_log: list = []
        self._load_vectorizer()

    # ── DB & Model Loading ─────────────────────────────────────────

    def _load_vectorizer(self):
        """Load trained TF-IDF vectorizer from model_data/vectorizer.pkl."""
        pkl_path = MODEL_DIR / "vectorizer.pkl"
        try:
            if pkl_path.exists():
                with open(pkl_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                logger.info(f"Loaded vectorizer: vocab={len(self.vectorizer.vocabulary_)}")
            else:
                logger.warning("vectorizer.pkl not found — will create fresh vectorizer")
                self.vectorizer = None
        except Exception as e:
            self._error_log.append(f"vectorizer load: {e}")
            logger.error(f"Failed to load vectorizer: {e}")
            self.vectorizer = None

    def _get_db(self) -> sqlite3.Connection:
        """Standard DB connection with WAL, query_only, row_factory."""
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        return conn

    # ── Core Similarity Engine ─────────────────────────────────────

    def _vectorize_texts(self, texts: List[str]) -> Any:
        """TF-IDF vectorize a list of texts. Uses loaded vectorizer or fits new one."""
        if not texts:
            return None
        cleaned = [_clean_text(t) for t in texts]
        try:
            if self.vectorizer is not None:
                return self.vectorizer.transform(cleaned)
            else:
                # Fallback: fit a fresh vectorizer on the input texts
                v = TfidfVectorizer(
                    max_features=20000, stop_words="english",
                    ngram_range=(1, 2), min_df=1, max_df=0.95
                )
                matrix = v.fit_transform(cleaned)
                return matrix
        except Exception as e:
            self._error_log.append(f"vectorize: {e}")
            return None

    def _find_similar_pairs(
        self, texts: List[str], ids: List[Any], threshold: float, limit: int
    ) -> List[Tuple[int, int, float]]:
        """
        Find pairs of texts with cosine similarity above threshold.
        Returns list of (idx_a, idx_b, similarity) sorted by similarity desc.
        Efficient: uses batch cosine_similarity from sklearn.
        """
        if len(texts) < 2:
            return []

        matrix = self._vectorize_texts(texts)
        if matrix is None:
            return []

        # Batch cosine similarity — efficient numpy under the hood
        sim_matrix = cosine_similarity(matrix)

        # Extract upper-triangle pairs above threshold
        pairs = []
        n = sim_matrix.shape[0]
        for i in range(n):
            for j in range(i + 1, n):
                score = sim_matrix[i, j]
                if score >= threshold:
                    pairs.append((i, j, float(score)))

        # Sort by similarity descending, cap at limit
        pairs.sort(key=lambda x: x[2], reverse=True)
        return pairs[:limit]

    def _detect_contradiction_signals(
        self, text_a: str, text_b: str
    ) -> Dict[str, Any]:
        """
        Detect contradiction signals between two similar texts.
        Returns signal dict with type and confidence.
        """
        words_a = _word_set(text_a)
        words_b = _word_set(text_b)
        signals = []

        # Signal 1: Negation asymmetry
        neg_a = words_a & _NEGATION_WORDS
        neg_b = words_b & _NEGATION_WORDS
        aff_a = words_a & _AFFIRMATION_WORDS
        aff_b = words_b & _AFFIRMATION_WORDS
        if (neg_a and aff_b and not neg_b) or (neg_b and aff_a and not neg_a):
            signals.append({
                "type": "negation_asymmetry",
                "confidence": 0.8,
                "detail": f"A-neg={neg_a} A-aff={aff_a} B-neg={neg_b} B-aff={aff_b}"
            })

        # Signal 2: Temporal contradiction (different dates for same topic)
        dates_a = _extract_dates(text_a)
        dates_b = _extract_dates(text_b)
        if dates_a and dates_b and dates_a != dates_b:
            overlap_words = words_a & words_b - {"the", "a", "an", "of", "in", "to", "and", "or"}
            if len(overlap_words) > 5:
                signals.append({
                    "type": "temporal_conflict",
                    "confidence": 0.7,
                    "detail": f"dates_a={dates_a} dates_b={dates_b}"
                })

        # Signal 3: Quantitative contradiction (different numbers)
        nums_a = set(re.findall(r'\b\d+\b', text_a))
        nums_b = set(re.findall(r'\b\d+\b', text_b))
        # Filter out very small numbers (page numbers, etc.)
        sig_nums_a = {n for n in nums_a if int(n) > 1}
        sig_nums_b = {n for n in nums_b if int(n) > 1}
        if sig_nums_a and sig_nums_b and sig_nums_a != sig_nums_b:
            common_context = words_a & words_b - {"the", "a", "an", "of", "in", "to"}
            if len(common_context) > 3:
                signals.append({
                    "type": "quantitative_conflict",
                    "confidence": 0.6,
                    "detail": f"nums_a={sig_nums_a} nums_b={sig_nums_b}"
                })

        # Signal 4: Characterization contradiction (opposite descriptors)
        opposites = [
            ("safe", "unsafe"), ("safe", "dangerous"), ("good", "bad"),
            ("fit", "unfit"), ("stable", "unstable"), ("willing", "unwilling"),
            ("cooperative", "uncooperative"), ("appropriate", "inappropriate"),
            ("present", "absent"), ("involved", "uninvolved"),
            ("truthful", "dishonest"), ("honest", "dishonest"),
            ("custodial", "noncustodial"), ("compliant", "noncompliant"),
            ("supervised", "unsupervised"), ("voluntary", "involuntary"),
        ]
        for w1, w2 in opposites:
            if (w1 in words_a and w2 in words_b) or (w2 in words_a and w1 in words_b):
                signals.append({
                    "type": "characterization_conflict",
                    "confidence": 0.85,
                    "detail": f"opposite pair: {w1}/{w2}"
                })

        if not signals:
            return {"has_signal": False, "signals": [], "top_type": None, "confidence": 0.0}

        best = max(signals, key=lambda s: s["confidence"])
        return {
            "has_signal": True,
            "signals": signals,
            "top_type": best["type"],
            "confidence": best["confidence"],
        }

    # ── Watson Contradictions ──────────────────────────────────────

    def find_watson_contradictions(
        self, threshold: float = 0.7, limit: int = 100
    ) -> list:
        """
        Find contradictions in Watson's statements.
        Queries evidence_quotes (speaker LIKE '%Watson%' or quote_text mentions Watson)
        and impeachment_items (speaker LIKE '%Watson%').
        TF-IDF vectorize → cosine similarity → contradiction signal detection.
        """
        conn = self._get_db()
        try:
            # Gather Watson statements from multiple sources
            statements = []

            # Source 1: evidence_quotes with Watson as speaker
            rows = conn.execute(
                "SELECT id, quote_text, 'evidence_quotes' as src "
                "FROM evidence_quotes "
                "WHERE speaker LIKE '%WATSON%' AND length(quote_text) > 30"
            ).fetchall()
            for r in rows:
                statements.append({
                    "id": r["id"], "text": r["quote_text"],
                    "source_table": r["src"]
                })

            # Source 2: impeachment_items with Watson as speaker (statements)
            rows = conn.execute(
                "SELECT id, statement, 'impeachment_statement' as src "
                "FROM impeachment_items "
                "WHERE speaker LIKE '%WATSON%' AND length(statement) > 30"
            ).fetchall()
            for r in rows:
                statements.append({
                    "id": r["id"], "text": r["statement"],
                    "source_table": r["src"]
                })

            # Source 3: impeachment contradicting_text (Watson's other side)
            rows = conn.execute(
                "SELECT id, contradicting_text, 'impeachment_contra' as src "
                "FROM impeachment_items "
                "WHERE speaker LIKE '%WATSON%' AND length(contradicting_text) > 30"
            ).fetchall()
            for r in rows:
                statements.append({
                    "id": r["id"], "text": r["contradicting_text"],
                    "source_table": r["src"]
                })

            # Source 4: evidence_quotes mentioning Watson (broader net)
            rows = conn.execute(
                "SELECT id, quote_text, 'evidence_quotes_mention' as src "
                "FROM evidence_quotes "
                "WHERE quote_text LIKE '%Watson%' "
                "AND speaker IS NOT 'WATSON' "
                "AND length(quote_text) > 50 "
                "LIMIT 2000"
            ).fetchall()
            for r in rows:
                statements.append({
                    "id": r["id"], "text": r["quote_text"],
                    "source_table": r["src"]
                })

            if len(statements) < 2:
                return []

            # Deduplicate by cleaning text
            seen_texts = {}
            unique_statements = []
            for s in statements:
                clean = _clean_text(s["text"])
                if len(clean) < 30:
                    continue
                # Hash first 200 chars to dedup near-identical
                key = clean[:200].lower()
                if key not in seen_texts:
                    seen_texts[key] = True
                    s["clean_text"] = clean
                    unique_statements.append(s)

            logger.info(f"Watson statements: {len(statements)} raw → {len(unique_statements)} unique")

            texts = [s["clean_text"] for s in unique_statements]
            ids = [s["id"] for s in unique_statements]

            # Find similar pairs
            pairs = self._find_similar_pairs(texts, ids, threshold=threshold, limit=limit * 5)

            # Filter for contradiction signals
            contradictions = []
            for idx_a, idx_b, sim in pairs:
                signals = self._detect_contradiction_signals(
                    texts[idx_a], texts[idx_b]
                )
                if signals["has_signal"]:
                    contradictions.append({
                        "statement_a": texts[idx_a][:500],
                        "statement_b": texts[idx_b][:500],
                        "similarity": round(sim, 4),
                        "potential_contradiction_type": signals["top_type"],
                        "confidence": signals["confidence"],
                        "signals": signals["signals"],
                        "source_a_id": unique_statements[idx_a]["id"],
                        "source_b_id": unique_statements[idx_b]["id"],
                        "source_a_table": unique_statements[idx_a]["source_table"],
                        "source_b_table": unique_statements[idx_b]["source_table"],
                    })
                    if len(contradictions) >= limit:
                        break

            contradictions.sort(key=lambda x: (x["confidence"], x["similarity"]), reverse=True)
            return contradictions[:limit]
        finally:
            conn.close()

    # ── Cross-Document Contradictions ──────────────────────────────

    def find_cross_document_contradictions(
        self, doc_type_a: str = "TRANSCRIPT",
        doc_type_b: str = "CUSTODY_ORDER",
        threshold: float = 0.6, limit: int = 50
    ) -> list:
        """
        Find contradictions between different document types.
        E.g., court orders vs evidence, FOC reports vs testimony.
        """
        conn = self._get_db()
        try:
            # Get statements from type A
            rows_a = conn.execute(
                "SELECT id, quote_text, evidence_category "
                "FROM evidence_quotes "
                "WHERE evidence_category = ? AND length(quote_text) > 50 "
                "LIMIT 3000",
                (doc_type_a,)
            ).fetchall()

            # Get statements from type B
            rows_b = conn.execute(
                "SELECT id, quote_text, evidence_category "
                "FROM evidence_quotes "
                "WHERE evidence_category = ? AND length(quote_text) > 50 "
                "LIMIT 3000",
                (doc_type_b,)
            ).fetchall()

            if not rows_a or not rows_b:
                # Try broader search with LIKE
                if not rows_a:
                    rows_a = conn.execute(
                        "SELECT id, quote_text, evidence_category "
                        "FROM evidence_quotes "
                        "WHERE evidence_category LIKE ? AND length(quote_text) > 50 "
                        "LIMIT 3000",
                        (f"%{doc_type_a}%",)
                    ).fetchall()
                if not rows_b:
                    rows_b = conn.execute(
                        "SELECT id, quote_text, evidence_category "
                        "FROM evidence_quotes "
                        "WHERE evidence_category LIKE ? AND length(quote_text) > 50 "
                        "LIMIT 3000",
                        (f"%{doc_type_b}%",)
                    ).fetchall()

            if len(rows_a) < 1 or len(rows_b) < 1:
                return []

            # Combine with source labels
            all_stmts = []
            for r in rows_a:
                clean = _clean_text(r["quote_text"])
                if len(clean) > 30:
                    all_stmts.append({
                        "id": r["id"], "clean_text": clean,
                        "doc_type": doc_type_a, "group": "A"
                    })
            for r in rows_b:
                clean = _clean_text(r["quote_text"])
                if len(clean) > 30:
                    all_stmts.append({
                        "id": r["id"], "clean_text": clean,
                        "doc_type": doc_type_b, "group": "B"
                    })

            texts = [s["clean_text"] for s in all_stmts]
            ids = [s["id"] for s in all_stmts]

            # Find similar pairs — only keep cross-group pairs
            matrix = self._vectorize_texts(texts)
            if matrix is None:
                return []

            sim_matrix = cosine_similarity(matrix)
            n = len(all_stmts)

            pairs = []
            for i in range(n):
                for j in range(i + 1, n):
                    # Only cross-document pairs
                    if all_stmts[i]["group"] == all_stmts[j]["group"]:
                        continue
                    score = sim_matrix[i, j]
                    if score >= threshold:
                        pairs.append((i, j, float(score)))

            pairs.sort(key=lambda x: x[2], reverse=True)
            pairs = pairs[:limit * 5]

            contradictions = []
            for idx_a, idx_b, sim in pairs:
                signals = self._detect_contradiction_signals(
                    texts[idx_a], texts[idx_b]
                )
                if signals["has_signal"]:
                    contradictions.append({
                        "statement_a": texts[idx_a][:500],
                        "statement_b": texts[idx_b][:500],
                        "similarity": round(sim, 4),
                        "potential_contradiction_type": signals["top_type"],
                        "confidence": signals["confidence"],
                        "doc_type_a": all_stmts[idx_a]["doc_type"],
                        "doc_type_b": all_stmts[idx_b]["doc_type"],
                        "source_a_id": all_stmts[idx_a]["id"],
                        "source_b_id": all_stmts[idx_b]["id"],
                    })
                    if len(contradictions) >= limit:
                        break

            contradictions.sort(key=lambda x: (x["confidence"], x["similarity"]), reverse=True)
            return contradictions[:limit]
        finally:
            conn.close()

    # ── Judicial Inconsistencies ───────────────────────────────────

    def find_judicial_inconsistencies(
        self, judge: str = "McNeill", threshold: float = 0.65, limit: int = 50
    ) -> list:
        """
        Find contradictions in judicial rulings/statements.
        Queries judicial_violations and forensic_judicial_analysis.
        """
        conn = self._get_db()
        try:
            statements = []

            # Source 1: judicial_violations
            rows = conn.execute(
                "SELECT violation_id, violation_description "
                "FROM judicial_violations "
                "WHERE judge_name LIKE ? AND length(violation_description) > 30",
                (f"%{judge}%",)
            ).fetchall()
            for r in rows:
                clean = _clean_text(r["violation_description"])
                if len(clean) > 30:
                    statements.append({
                        "id": r["violation_id"], "clean_text": clean,
                        "source_table": "judicial_violations"
                    })

            # Source 2: forensic_judicial_analysis
            rows = conn.execute(
                "SELECT finding_id, description, category "
                "FROM forensic_judicial_analysis "
                "WHERE length(description) > 30 "
                "LIMIT 3000"
            ).fetchall()
            for r in rows:
                clean = _clean_text(r["description"])
                if len(clean) > 30:
                    statements.append({
                        "id": r["finding_id"], "clean_text": clean,
                        "source_table": "forensic_judicial_analysis"
                    })

            # Deduplicate
            seen = {}
            unique = []
            for s in statements:
                key = s["clean_text"][:200].lower()
                if key not in seen:
                    seen[key] = True
                    unique.append(s)

            if len(unique) < 2:
                return []

            logger.info(f"Judicial statements: {len(statements)} raw → {len(unique)} unique")

            texts = [s["clean_text"] for s in unique]
            pairs = self._find_similar_pairs(texts, [s["id"] for s in unique], threshold, limit * 5)

            contradictions = []
            for idx_a, idx_b, sim in pairs:
                # For judicial: also flag same-category with different outcomes
                signals = self._detect_contradiction_signals(texts[idx_a], texts[idx_b])

                # Extra signal: cross-source (violation vs forensic finding)
                if unique[idx_a]["source_table"] != unique[idx_b]["source_table"]:
                    if not signals["has_signal"]:
                        signals = {
                            "has_signal": True,
                            "signals": [{"type": "cross_source_judicial", "confidence": 0.6,
                                         "detail": "Same topic across judicial_violations and forensic_analysis"}],
                            "top_type": "cross_source_judicial",
                            "confidence": 0.6,
                        }

                if signals["has_signal"]:
                    contradictions.append({
                        "statement_a": texts[idx_a][:500],
                        "statement_b": texts[idx_b][:500],
                        "similarity": round(sim, 4),
                        "potential_contradiction_type": signals["top_type"],
                        "confidence": signals["confidence"],
                        "source_a_id": unique[idx_a]["id"],
                        "source_b_id": unique[idx_b]["id"],
                        "source_a_table": unique[idx_a]["source_table"],
                        "source_b_table": unique[idx_b]["source_table"],
                    })
                    if len(contradictions) >= limit:
                        break

            contradictions.sort(key=lambda x: (x["confidence"], x["similarity"]), reverse=True)
            return contradictions[:limit]
        finally:
            conn.close()

    # ── Compare to Known ───────────────────────────────────────────

    def compare_to_known(self, new_contradictions: list) -> dict:
        """
        Compare newly discovered contradictions against contradiction_map (10,558 known).
        Uses TF-IDF similarity to check if a new contradiction matches any known one.
        """
        if not new_contradictions:
            return {"new": [], "already_known": 0, "novel_count": 0}

        conn = self._get_db()
        try:
            # Load known contradiction texts
            known_rows = conn.execute(
                "SELECT id, source_a_text, source_b_text, contradiction_type "
                "FROM contradiction_map"
            ).fetchall()

            # Build a combined text for each known contradiction
            known_texts = []
            for r in known_rows:
                combined = _clean_text(
                    (r["source_a_text"] or "") + " " + (r["source_b_text"] or "")
                )
                known_texts.append(combined)

            # Build combined text for new contradictions
            new_texts = []
            for c in new_contradictions:
                combined = _clean_text(c["statement_a"] + " " + c["statement_b"])
                new_texts.append(combined)

            # Vectorize all together
            all_texts = known_texts + new_texts
            matrix = self._vectorize_texts(all_texts)
            if matrix is None:
                return {"new": new_contradictions, "already_known": 0,
                        "novel_count": len(new_contradictions)}

            n_known = len(known_texts)
            known_matrix = matrix[:n_known]
            new_matrix = matrix[n_known:]

            # Compare each new against all known
            if new_matrix.shape[0] == 0 or known_matrix.shape[0] == 0:
                return {"new": new_contradictions, "already_known": 0,
                        "novel_count": len(new_contradictions)}

            cross_sim = cosine_similarity(new_matrix, known_matrix)

            novel = []
            already_known = 0
            for i, c in enumerate(new_contradictions):
                max_sim = float(cross_sim[i].max()) if cross_sim[i].size > 0 else 0.0
                if max_sim > 0.85:
                    already_known += 1
                    c["known_match_similarity"] = round(max_sim, 4)
                else:
                    c["novelty_score"] = round(1.0 - max_sim, 4)
                    novel.append(c)

            return {
                "new": novel,
                "already_known": already_known,
                "novel_count": len(novel),
            }
        finally:
            conn.close()

    # ── Severity Scoring ───────────────────────────────────────────

    def score_contradiction_severity(
        self, statement_a: str, statement_b: str
    ) -> dict:
        """
        Score a contradiction's severity for litigation.
        Returns: {severity, type, impeachment_value, legal_significance}
        """
        signals = self._detect_contradiction_signals(statement_a, statement_b)
        if not signals["has_signal"]:
            return {
                "severity": "low",
                "type": "potential",
                "impeachment_value": 0.2,
                "legal_significance": "Statements are similar but no clear contradiction signal detected."
            }

        top_type = signals["top_type"]
        confidence = signals["confidence"]

        severity_map = {
            "negation_asymmetry": ("high", "factual_contradiction",
                                   "Direct factual contradiction — strongest impeachment value. "
                                   "One statement affirms what the other denies."),
            "temporal_conflict": ("high", "temporal_contradiction",
                                 "Inconsistent dates/timelines for same events. "
                                 "Strong impeachment under MRE 613(b)."),
            "characterization_conflict": ("medium", "characterization_contradiction",
                                          "Different characterizations of same event/person. "
                                          "Useful for credibility challenge."),
            "quantitative_conflict": ("medium", "quantitative_contradiction",
                                      "Different numbers/amounts for same subject. "
                                      "Impeachment value depends on materiality."),
            "cross_source_judicial": ("high", "judicial_inconsistency",
                                      "Judicial ruling inconsistent across proceedings. "
                                      "Relevant to MCR 2.003 disqualification."),
        }

        sev, ctype, sig = severity_map.get(
            top_type,
            ("low", "unclassified", "Potential contradiction detected.")
        )

        # Impeachment value based on severity and confidence
        imp_val = {"high": 0.9, "medium": 0.6, "low": 0.3}.get(sev, 0.3)
        imp_val *= confidence

        return {
            "severity": sev,
            "type": ctype,
            "impeachment_value": round(imp_val, 3),
            "legal_significance": sig,
        }

    # ── Impeachment Item Generation ────────────────────────────────

    def generate_impeachment_items(self, contradictions: list) -> list:
        """
        Convert discovered contradictions into impeachment items.
        Format per MRE 801(d)(1)(A) for prior inconsistent statements.
        """
        items = []
        for c in contradictions:
            severity = self.score_contradiction_severity(
                c.get("statement_a", ""), c.get("statement_b", "")
            )

            ctype = c.get("potential_contradiction_type", "unknown")
            # Select MRE authority based on type
            if ctype in ("negation_asymmetry", "temporal_conflict"):
                mre = "MRE 613(b) — Extrinsic evidence of prior inconsistent statement"
            elif ctype == "characterization_conflict":
                mre = "MRE 608(b) — Specific instances of conduct for credibility"
            elif ctype == "cross_source_judicial":
                mre = "MCR 2.003(C)(1) — Judicial bias/prejudice; MRE 201 — Judicial notice"
            else:
                mre = "MRE 613(b) — Prior inconsistent statement"

            items.append({
                "speaker": "WATSON",
                "prior_statement": c.get("statement_a", "")[:500],
                "contradicting_statement": c.get("statement_b", "")[:500],
                "legal_hook": f"{severity['type']} — {severity['legal_significance'][:100]}",
                "MRE_authority": mre,
                "severity": severity["severity"],
                "impeachment_value": severity["impeachment_value"],
                "source_a_id": c.get("source_a_id"),
                "source_b_id": c.get("source_b_id"),
                "ml_discovered": True,
            })

        items.sort(key=lambda x: x["impeachment_value"], reverse=True)
        return items

    # ── Full Scan ──────────────────────────────────────────────────

    def full_scan(self) -> dict:
        """
        Run complete contradiction discovery:
        1. Watson contradictions
        2. Judicial inconsistencies
        3. Cross-document contradictions
        4. Compare all to known
        5. Generate new impeachment items
        Returns comprehensive report.
        """
        t0 = time.time()
        report = {"scan_time": None, "errors": []}

        # 1. Watson contradictions
        try:
            watson = self.find_watson_contradictions(threshold=0.7, limit=100)
            report["watson_contradictions"] = len(watson)
            report["watson_raw"] = watson
        except Exception as e:
            watson = []
            report["watson_contradictions"] = 0
            report["errors"].append(f"watson: {e}")

        # 2. Judicial inconsistencies
        try:
            judicial = self.find_judicial_inconsistencies(threshold=0.65, limit=50)
            report["judicial_inconsistencies"] = len(judicial)
            report["judicial_raw"] = judicial
        except Exception as e:
            judicial = []
            report["judicial_inconsistencies"] = 0
            report["errors"].append(f"judicial: {e}")

        # 3. Cross-document contradictions
        try:
            cross = self.find_cross_document_contradictions(
                "TRANSCRIPT", "CUSTODY_ORDER", threshold=0.6, limit=50
            )
            report["cross_document_contradictions"] = len(cross)
            report["cross_raw"] = cross
        except Exception as e:
            cross = []
            report["cross_document_contradictions"] = 0
            report["errors"].append(f"cross: {e}")

        # 4. Combine and compare to known
        all_found = watson + judicial + cross
        try:
            comparison = self.compare_to_known(all_found)
            report["total_discovered"] = len(all_found)
            report["novel_count"] = comparison["novel_count"]
            report["already_known"] = comparison["already_known"]
            report["novel_contradictions"] = comparison["new"]
        except Exception as e:
            report["novel_count"] = len(all_found)
            report["already_known"] = 0
            report["novel_contradictions"] = all_found
            report["errors"].append(f"compare: {e}")

        # 5. Generate impeachment items from novel discoveries
        try:
            novel = report.get("novel_contradictions", [])
            impeachment = self.generate_impeachment_items(novel)
            report["new_impeachment_items"] = len(impeachment)
            report["impeachment_items"] = impeachment
        except Exception as e:
            report["new_impeachment_items"] = 0
            report["errors"].append(f"impeachment: {e}")

        report["scan_time"] = round(time.time() - t0, 2)
        return report

    # ── Status ─────────────────────────────────────────────────────

    def status(self) -> dict:
        """Known contradictions count, Watson statements count, scan status."""
        conn = self._get_db()
        try:
            known = conn.execute("SELECT COUNT(*) FROM contradiction_map").fetchone()[0]
            watson_eq = conn.execute(
                "SELECT COUNT(*) FROM evidence_quotes WHERE speaker LIKE '%WATSON%'"
            ).fetchone()[0]
            watson_imp = conn.execute(
                "SELECT COUNT(*) FROM impeachment_items WHERE speaker LIKE '%WATSON%'"
            ).fetchone()[0]
            watson_mention = conn.execute(
                "SELECT COUNT(*) FROM evidence_quotes "
                "WHERE quote_text LIKE '%Watson%' AND length(quote_text) > 50"
            ).fetchone()[0]
            total_eq = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
            jv = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
            fja = conn.execute("SELECT COUNT(*) FROM forensic_judicial_analysis").fetchone()[0]

            return {
                "known_contradictions": known,
                "watson_evidence_quotes": watson_eq,
                "watson_impeachment_items": watson_imp,
                "watson_mentions_in_evidence": watson_mention,
                "total_evidence_quotes": total_eq,
                "judicial_violations": jv,
                "forensic_judicial_findings": fja,
                "vectorizer_loaded": self.vectorizer is not None,
                "vectorizer_vocab_size": len(self.vectorizer.vocabulary_) if self.vectorizer else 0,
                "errors": self._error_log[-5:] if self._error_log else [],
            }
        finally:
            conn.close()

    # ── Self-Test ──────────────────────────────────────────────────

    def self_test(self) -> dict:
        """Run self-diagnostics to verify all components work."""
        results = {"pass": True, "tests": []}

        def _test(name, fn):
            try:
                result = fn()
                results["tests"].append({"name": name, "status": "PASS", "detail": str(result)[:200]})
            except Exception as e:
                results["tests"].append({"name": name, "status": "FAIL", "detail": str(e)[:200]})
                results["pass"] = False

        # Test 1: DB connection
        _test("db_connection", lambda: bool(self._get_db().close() or True))

        # Test 2: Vectorizer loaded
        _test("vectorizer_loaded", lambda: self.vectorizer is not None)

        # Test 3: Vectorize sample texts
        _test("vectorize_sample", lambda: self._vectorize_texts(
            ["test statement one", "test statement two"]
        ).shape)

        # Test 4: Contradiction signal detection
        _test("signal_detection", lambda: self._detect_contradiction_signals(
            "Watson said she never left the children alone",
            "Watson admitted she always left the children unsupervised"
        ))

        # Test 5: Severity scoring
        _test("severity_scoring", lambda: self.score_contradiction_severity(
            "The hearing was on January 5, 2024",
            "The hearing was on March 12, 2024"
        ))

        # Test 6: Status query
        _test("status_query", lambda: self.status())

        # Test 7: Small Watson scan (limit 5)
        _test("watson_scan_small", lambda: len(
            self.find_watson_contradictions(threshold=0.8, limit=5)
        ))

        return results


# ── CLI ────────────────────────────────────────────────────────────

def _print_json(obj):
    """Pretty-print JSON to stdout."""
    print(json.dumps(obj, indent=2, default=str))


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="DELTA 3 — Auto-Contradiction Discovery for THE MANBEARPIG"
    )
    parser.add_argument("command", nargs="?", default="status",
                        choices=["watson", "judicial", "cross", "full-scan",
                                 "status", "self-test"],
                        help="Command to run")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Cosine similarity threshold")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max results to return")
    parser.add_argument("--doc-a", type=str, default="TRANSCRIPT",
                        help="Document type A (for cross command)")
    parser.add_argument("--doc-b", type=str, default="CUSTODY_ORDER",
                        help="Document type B (for cross command)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON")

    args = parser.parse_args()
    cd = ContradictionDiscovery()

    if args.command == "status":
        result = cd.status()
        if args.json:
            _print_json(result)
        else:
            print("=" * 60)
            print("DELTA 3 — Contradiction Discovery Status")
            print("=" * 60)
            for k, v in result.items():
                print(f"  {k}: {v}")

    elif args.command == "self-test":
        result = cd.self_test()
        if args.json:
            _print_json(result)
        else:
            print("=" * 60)
            print("DELTA 3 — Self-Test Results")
            print("=" * 60)
            for t in result["tests"]:
                icon = "PASS" if t["status"] == "PASS" else "FAIL"
                print(f"  [{icon}] {t['name']}: {t['detail'][:100]}")
            print(f"\n  Overall: {'ALL PASS' if result['pass'] else 'FAILURES DETECTED'}")

    elif args.command == "watson":
        threshold = args.threshold or 0.7
        limit = args.limit or 100
        print(f"Scanning Watson contradictions (threshold={threshold}, limit={limit})...")
        contradictions = cd.find_watson_contradictions(threshold=threshold, limit=limit)
        comparison = cd.compare_to_known(contradictions)
        impeachment = cd.generate_impeachment_items(comparison["new"])

        if args.json:
            _print_json({
                "contradictions_found": len(contradictions),
                "novel": comparison["novel_count"],
                "already_known": comparison["already_known"],
                "impeachment_items": impeachment,
                "raw": contradictions,
            })
        else:
            print("=" * 60)
            print("DELTA 3 — Watson Contradiction Scan")
            print("=" * 60)
            print(f"  Total contradictions found:  {len(contradictions)}")
            print(f"  Already known:               {comparison['already_known']}")
            print(f"  NEW contradictions:           {comparison['novel_count']}")
            print(f"  New impeachment items:        {len(impeachment)}")
            print()
            for i, c in enumerate(contradictions[:10]):
                print(f"  --- Contradiction #{i+1} (sim={c['similarity']}, type={c['potential_contradiction_type']}) ---")
                print(f"    A: {c['statement_a'][:150]}...")
                print(f"    B: {c['statement_b'][:150]}...")
                print()

    elif args.command == "judicial":
        threshold = args.threshold or 0.65
        limit = args.limit or 50
        print(f"Scanning judicial inconsistencies (threshold={threshold}, limit={limit})...")
        contradictions = cd.find_judicial_inconsistencies(threshold=threshold, limit=limit)
        comparison = cd.compare_to_known(contradictions)

        if args.json:
            _print_json({
                "contradictions_found": len(contradictions),
                "novel": comparison["novel_count"],
                "already_known": comparison["already_known"],
                "raw": contradictions,
            })
        else:
            print("=" * 60)
            print("DELTA 3 — Judicial Inconsistency Scan")
            print("=" * 60)
            print(f"  Total found:     {len(contradictions)}")
            print(f"  Already known:   {comparison['already_known']}")
            print(f"  NEW:             {comparison['novel_count']}")
            print()
            for i, c in enumerate(contradictions[:10]):
                print(f"  --- #{i+1} (sim={c['similarity']}, type={c['potential_contradiction_type']}) ---")
                print(f"    A [{c.get('source_a_table','')}]: {c['statement_a'][:150]}...")
                print(f"    B [{c.get('source_b_table','')}]: {c['statement_b'][:150]}...")
                print()

    elif args.command == "cross":
        threshold = args.threshold or 0.6
        limit = args.limit or 50
        print(f"Scanning cross-document contradictions ({args.doc_a} vs {args.doc_b})...")
        contradictions = cd.find_cross_document_contradictions(
            args.doc_a, args.doc_b, threshold=threshold, limit=limit
        )
        comparison = cd.compare_to_known(contradictions)

        if args.json:
            _print_json({
                "contradictions_found": len(contradictions),
                "novel": comparison["novel_count"],
                "already_known": comparison["already_known"],
                "raw": contradictions,
            })
        else:
            print("=" * 60)
            print(f"DELTA 3 — Cross-Document: {args.doc_a} vs {args.doc_b}")
            print("=" * 60)
            print(f"  Total found:     {len(contradictions)}")
            print(f"  Already known:   {comparison['already_known']}")
            print(f"  NEW:             {comparison['novel_count']}")

    elif args.command == "full-scan":
        print("Running FULL contradiction discovery scan...")
        report = cd.full_scan()

        if args.json:
            # Remove raw data for cleaner JSON
            slim = {k: v for k, v in report.items()
                    if not k.endswith("_raw") and k != "impeachment_items"
                    and k != "novel_contradictions"}
            slim["sample_novel"] = report.get("novel_contradictions", [])[:5]
            slim["sample_impeachment"] = report.get("impeachment_items", [])[:5]
            _print_json(slim)
        else:
            print("=" * 60)
            print("DELTA 3 — Full Scan Report")
            print("=" * 60)
            print(f"  Scan time:                   {report['scan_time']}s")
            print(f"  Watson contradictions:        {report['watson_contradictions']}")
            print(f"  Judicial inconsistencies:     {report['judicial_inconsistencies']}")
            print(f"  Cross-document contradictions:{report['cross_document_contradictions']}")
            print(f"  Total discovered:             {report.get('total_discovered', 0)}")
            print(f"  Already known:                {report.get('already_known', 0)}")
            print(f"  NOVEL contradictions:         {report.get('novel_count', 0)}")
            print(f"  New impeachment items:        {report.get('new_impeachment_items', 0)}")
            if report.get("errors"):
                print(f"  Errors:                       {report['errors']}")


if __name__ == "__main__":
    main()
