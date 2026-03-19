"""
Deep Pattern Mining Engine — MBP LitigationOS 2026 v1.0
========================================================
Association rule mining and frequent pattern discovery across 308K+ evidence
quotes, 10K+ contradictions, and 15K+ impeachment items.  Finds hidden
correlations, recurring patterns, and non-obvious connections that humans
would miss.

DB: C:\\Users\\andre\\litigation_context.db
"""

from __future__ import annotations

import math
import os
import re
import sqlite3
import statistics
import sys
import textwrap
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Optional heavy imports — graceful fallback
# ---------------------------------------------------------------------------
try:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

try:
    from scipy.spatial.distance import cdist
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
_MAX_SAMPLE = 50_000  # sample cap for expensive ops
_ASSOCIATION_MAX_ITEMSET = 3  # max itemset size for association mining


class PatternMiner:
    """Deep pattern mining engine for the MANBEARPIG litigation AI system."""

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self.db_path = db_path
        if not os.path.isfile(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish (or re-establish) the DB connection with retries."""
        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                self._conn = sqlite3.connect(self.db_path, timeout=30)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode=WAL")
                return
            except Exception as exc:
                last_err = exc
                import time
                time.sleep(2 ** attempt)
        raise ConnectionError(
            f"Failed to connect after 3 attempts: {last_err}"
        )

    def _cur(self) -> sqlite3.Cursor:
        if self._conn is None:
            self._connect()
        return self._conn.cursor()  # type: ignore[union-attr]

    def _query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        try:
            return self._cur().execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            self._connect()
            return self._cur().execute(sql, params).fetchall()

    def _query_dicts(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        rows = self._query(sql, params)
        if not rows:
            return []
        keys = rows[0].keys()
        return [dict(zip(keys, row)) for row in rows]

    # ------------------------------------------------------------------
    # 1. mine_evidence_patterns — association rule mining
    # ------------------------------------------------------------------
    def mine_evidence_patterns(
        self,
        min_support: float = 0.01,
        min_confidence: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Find co-occurring evidence patterns via association rule mining.

        Builds item-sets from evidence_quotes grouped by document_id.
        Items are (evidence_category, speaker, legal_significance) tuples.
        Returns rules with support, confidence, and lift.
        """
        rows = self._query(
            "SELECT document_id, evidence_category, speaker, legal_significance "
            "FROM evidence_quotes WHERE document_id IS NOT NULL"
        )
        if not rows:
            return []

        # Build transactions: one set of items per document
        transactions: Dict[int, set] = defaultdict(set)
        for r in rows:
            doc_id = r["document_id"]
            cat = r["evidence_category"]
            spk = r["speaker"]
            sig = r["legal_significance"]
            if cat:
                transactions[doc_id].add(f"cat:{cat}")
            if spk:
                transactions[doc_id].add(f"spk:{spk}")
            if sig:
                # Normalise long significance text to first 60 chars
                sig_key = sig[:60].strip()
                transactions[doc_id].add(f"sig:{sig_key}")

        tx_list = list(transactions.values())
        n_tx = len(tx_list)
        if n_tx == 0:
            return []

        # Count single-item and pair frequencies
        single_counts: Counter = Counter()
        pair_counts: Counter = Counter()
        for items in tx_list:
            for item in items:
                single_counts[item] += 1
            if len(items) >= 2:
                sorted_items = sorted(items)
                for a, b in combinations(sorted_items, 2):
                    pair_counts[(a, b)] += 1

        # Generate association rules A → B
        rules: List[Dict[str, Any]] = []
        min_count = max(1, int(min_support * n_tx))
        for (a, b), ab_count in pair_counts.items():
            if ab_count < min_count:
                continue
            support = ab_count / n_tx
            # A → B
            conf_ab = ab_count / single_counts[a] if single_counts[a] else 0
            if conf_ab >= min_confidence:
                expected = (single_counts[a] / n_tx) * (single_counts[b] / n_tx)
                lift = support / expected if expected > 0 else 0
                rules.append({
                    "antecedent": a,
                    "consequent": b,
                    "support": round(support, 6),
                    "confidence": round(conf_ab, 4),
                    "lift": round(lift, 4),
                    "co_occurrences": ab_count,
                })
            # B → A
            conf_ba = ab_count / single_counts[b] if single_counts[b] else 0
            if conf_ba >= min_confidence:
                expected = (single_counts[a] / n_tx) * (single_counts[b] / n_tx)
                lift = support / expected if expected > 0 else 0
                rules.append({
                    "antecedent": b,
                    "consequent": a,
                    "support": round(support, 6),
                    "confidence": round(conf_ba, 4),
                    "lift": round(lift, 4),
                    "co_occurrences": ab_count,
                })

        rules.sort(key=lambda r: r["lift"], reverse=True)
        return rules

    # ------------------------------------------------------------------
    # 2. mine_contradiction_patterns
    # ------------------------------------------------------------------
    def mine_contradiction_patterns(self) -> Dict[str, Any]:
        """Find patterns in contradictions: speaker, temporal, and topic."""
        rows = self._query_dicts(
            "SELECT id, source_a_type, source_a_doc_id, source_a_text, "
            "source_b_type, source_b_doc_id, source_b_text, "
            "contradiction_type, severity, legal_impact, created_at "
            "FROM contradiction_map"
        )

        speaker_patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        temporal_patterns: Dict[str, int] = defaultdict(int)
        topic_patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        severity_by_type: Dict[str, Counter] = defaultdict(Counter)
        type_co_occurrence: Counter = Counter()

        # Extract speaker mentions from contradiction text
        speaker_re = re.compile(
            r"\b(Watson|Pigors|Court|McNeill|FOC|GAL)\b", re.IGNORECASE
        )

        for r in rows:
            ctype = r.get("contradiction_type", "UNKNOWN") or "UNKNOWN"
            sev = r.get("severity", "UNKNOWN") or "UNKNOWN"
            impact = r.get("legal_impact", "") or ""
            a_text = r.get("source_a_text", "") or ""
            b_text = r.get("source_b_text", "") or ""
            combined = f"{a_text} {b_text}"

            # Speaker patterns
            speakers_found = set(
                m.upper() for m in speaker_re.findall(combined)
            )
            for spk in speakers_found:
                speaker_patterns[spk][ctype] += 1

            # Temporal patterns — bucket by month
            created = r.get("created_at", "")
            if created and len(str(created)) >= 7:
                month_key = str(created)[:7]
                temporal_patterns[month_key] += 1

            # Topic extraction from legal_impact
            if impact:
                topic_tokens = re.findall(r"[A-Za-z_]{4,}", impact)
                for tok in topic_tokens[:5]:
                    topic_patterns[tok.lower()][ctype] += 1

            severity_by_type[ctype][sev] += 1

        # Co-occurrence of contradiction types within same document pair
        doc_pair_types: Dict[Tuple, set] = defaultdict(set)
        for r in rows:
            key = (r.get("source_a_doc_id"), r.get("source_b_doc_id"))
            if key[0] is not None and key[1] is not None:
                doc_pair_types[key].add(r.get("contradiction_type", ""))
        for types_set in doc_pair_types.values():
            if len(types_set) >= 2:
                for a, b in combinations(sorted(types_set), 2):
                    type_co_occurrence[(a, b)] += 1

        return {
            "speaker_patterns": {
                spk: dict(types) for spk, types in speaker_patterns.items()
            },
            "temporal_patterns": dict(sorted(temporal_patterns.items())),
            "topic_patterns": {
                topic: dict(types)
                for topic, types in sorted(
                    topic_patterns.items(),
                    key=lambda x: sum(x[1].values()),
                    reverse=True,
                )[:30]
            },
            "severity_by_type": {
                ct: dict(sev) for ct, sev in severity_by_type.items()
            },
            "type_co_occurrences": [
                {"types": list(pair), "count": cnt}
                for pair, cnt in type_co_occurrence.most_common(20)
            ],
            "total_contradictions": len(rows),
        }

    # ------------------------------------------------------------------
    # 3. mine_judicial_patterns
    # ------------------------------------------------------------------
    def mine_judicial_patterns(self) -> Dict[str, Any]:
        """Detect patterns in judicial behaviour from docket events,
        judicial violations, and related evidence."""

        # --- Ruling patterns from docket_events ---
        events = self._query_dicts(
            "SELECT event_id, case_id, event_date_iso, title, event_type, "
            "summary, truth_tag FROM docket_events ORDER BY event_date_iso"
        )

        ruling_patterns: Dict[str, int] = defaultdict(int)
        ex_parte_events: List[Dict[str, Any]] = []
        timeline: List[Dict[str, Any]] = []
        pro_pigors = 0
        pro_watson = 0
        neutral = 0

        pigors_re = re.compile(
            r"\b(Pigors|Plaintiff|Andrew|father)\b", re.IGNORECASE
        )
        watson_re = re.compile(
            r"\b(Watson|Defendant|Tiffany|mother)\b", re.IGNORECASE
        )
        grant_re = re.compile(
            r"\b(grant|approv|sustain|favor)\b", re.IGNORECASE
        )
        deny_re = re.compile(
            r"\b(deni|reject|overrul|dismiss)\b", re.IGNORECASE
        )

        for ev in events:
            etype = ev.get("event_type", "") or ""
            title = ev.get("title", "") or ""
            summary = ev.get("summary", "") or ""
            combined = f"{title} {summary}"
            date_str = ev.get("event_date_iso", "")

            ruling_patterns[etype] += 1
            timeline.append({"date": date_str, "type": etype, "title": title})

            if "ex_parte" in etype or "ex parte" in combined.lower():
                ex_parte_events.append(ev)

            # Attempt to classify ruling direction
            is_order = etype in ("order", "ex_parte_order", "order_denial")
            if is_order:
                pigors_mention = bool(pigors_re.search(combined))
                watson_mention = bool(watson_re.search(combined))
                granted = bool(grant_re.search(combined))
                denied = bool(deny_re.search(combined))

                if pigors_mention and denied:
                    pro_watson += 1
                elif watson_mention and denied:
                    pro_pigors += 1
                elif watson_mention and granted:
                    pro_watson += 1
                elif pigors_mention and granted:
                    pro_pigors += 1
                else:
                    neutral += 1

        # --- Judicial violations analysis ---
        violations = self._query_dicts(
            "SELECT violation_id, judge_name, canon_number, "
            "violation_description, severity, created_at "
            "FROM judicial_violations"
        )

        violation_by_canon: Counter = Counter()
        violation_by_severity: Counter = Counter()
        violation_timeline: Dict[str, int] = defaultdict(int)
        for v in violations:
            canon = v.get("canon_number", "unknown") or "unknown"
            violation_by_canon[canon] += 1
            sev = v.get("severity", "unknown") or "unknown"
            violation_by_severity[sev] += 1
            created = v.get("created_at", "")
            if created and len(str(created)) >= 7:
                violation_timeline[str(created)[:7]] += 1

        # --- Temporal shifts: divide events into halves ---
        sorted_events = sorted(
            events, key=lambda e: e.get("event_date_iso", "") or ""
        )
        mid = len(sorted_events) // 2
        first_half = sorted_events[:mid]
        second_half = sorted_events[mid:]

        def _event_type_dist(evts: list) -> Dict[str, float]:
            c: Counter = Counter()
            for e in evts:
                c[e.get("event_type", "")] += 1
            total = sum(c.values()) or 1
            return {k: round(v / total, 4) for k, v in c.most_common()}

        temporal_shifts = {
            "first_half_distribution": _event_type_dist(first_half),
            "second_half_distribution": _event_type_dist(second_half),
            "first_half_period": (
                first_half[0].get("event_date_iso", "") if first_half else "",
                first_half[-1].get("event_date_iso", "") if first_half else "",
            ),
            "second_half_period": (
                second_half[0].get("event_date_iso", "") if second_half else "",
                second_half[-1].get("event_date_iso", "") if second_half else "",
            ),
        }

        return {
            "ruling_patterns": {
                "event_type_counts": dict(ruling_patterns),
                "pro_pigors_rulings": pro_pigors,
                "pro_watson_rulings": pro_watson,
                "neutral_rulings": neutral,
                "total_orders": pro_pigors + pro_watson + neutral,
            },
            "ex_parte_events": [
                {
                    "date": e.get("event_date_iso"),
                    "title": e.get("title"),
                    "summary": e.get("summary"),
                }
                for e in ex_parte_events
            ],
            "temporal_shifts": temporal_shifts,
            "bias_indicators": {
                "ruling_ratio_pigors_watson": (
                    round(pro_pigors / pro_watson, 4)
                    if pro_watson > 0
                    else ("inf" if pro_pigors > 0 else "no_data")
                ),
                "ex_parte_count": len(ex_parte_events),
                "total_violations": len(violations),
                "violations_by_canon": dict(violation_by_canon.most_common(10)),
                "violations_by_severity": dict(violation_by_severity),
                "violation_timeline": dict(sorted(violation_timeline.items())),
            },
        }

    # ------------------------------------------------------------------
    # 4. mine_procedural_patterns
    # ------------------------------------------------------------------
    def mine_procedural_patterns(self) -> Dict[str, Any]:
        """Analyse procedural patterns: timing, outcomes, anomalies."""
        events = self._query_dicts(
            "SELECT event_id, case_id, event_date_iso, title, event_type, "
            "summary FROM docket_events ORDER BY event_date_iso"
        )

        # --- Timing patterns ---
        filings: List[Dict] = []
        orders: List[Dict] = []
        for ev in events:
            etype = ev.get("event_type", "") or ""
            if etype in ("filing", "motion", "motion_filed"):
                filings.append(ev)
            elif etype in ("order", "ex_parte_order", "order_denial"):
                orders.append(ev)

        # Filing → next order timing
        timing_gaps: List[float] = []
        for f in filings:
            f_date = self._parse_date(f.get("event_date_iso", ""))
            if f_date is None:
                continue
            for o in orders:
                o_date = self._parse_date(o.get("event_date_iso", ""))
                if o_date is None:
                    continue
                delta = (o_date - f_date).days
                if 0 <= delta <= 365:
                    timing_gaps.append(delta)
                    break

        timing_stats = {}
        if timing_gaps:
            timing_stats = {
                "mean_days_filing_to_order": round(statistics.mean(timing_gaps), 1),
                "median_days_filing_to_order": round(statistics.median(timing_gaps), 1),
                "min_days": min(timing_gaps),
                "max_days": max(timing_gaps),
                "stdev_days": (
                    round(statistics.stdev(timing_gaps), 1)
                    if len(timing_gaps) > 1
                    else 0
                ),
                "sample_size": len(timing_gaps),
            }

        # --- Outcome patterns (from docket event types) ---
        outcome_counts: Counter = Counter()
        for ev in events:
            etype = ev.get("event_type", "") or ""
            outcome_counts[etype] += 1

        # --- Motion grant/deny analysis from vehicles ---
        vehicles = self._query_dicts(
            "SELECT vehicle_id, case_lane, title, vehicle_type, status "
            "FROM vehicles"
        )
        vehicle_outcomes: Counter = Counter()
        for v in vehicles:
            status = (v.get("status") or "unknown").lower()
            vehicle_outcomes[status] += 1

        # --- Anomaly detection: events with unusual timing ---
        anomalies: List[Dict[str, Any]] = []
        if len(timing_gaps) > 2:
            mean_gap = statistics.mean(timing_gaps)
            std_gap = statistics.stdev(timing_gaps) if len(timing_gaps) > 1 else 1
            for i, f in enumerate(filings):
                if i < len(timing_gaps):
                    gap = timing_gaps[i]
                    z = (gap - mean_gap) / std_gap if std_gap > 0 else 0
                    if abs(z) > 1.5:
                        anomalies.append({
                            "filing": f.get("title", ""),
                            "date": f.get("event_date_iso", ""),
                            "days_to_order": gap,
                            "z_score": round(z, 2),
                            "anomaly": "unusually_fast" if z < 0 else "unusually_slow",
                        })

        # --- Service/notice failure patterns ---
        service_events = [
            ev for ev in events if ev.get("event_type") == "service"
        ]

        return {
            "timing_patterns": timing_stats,
            "outcome_patterns": {
                "docket_event_types": dict(outcome_counts.most_common()),
                "vehicle_statuses": dict(vehicle_outcomes),
            },
            "anomalies": anomalies,
            "service_events": [
                {"date": s.get("event_date_iso"), "title": s.get("title")}
                for s in service_events
            ],
            "total_events": len(events),
            "total_filings": len(filings),
            "total_orders": len(orders),
        }

    # ------------------------------------------------------------------
    # 5. find_hidden_connections
    # ------------------------------------------------------------------
    def find_hidden_connections(
        self, entity_a: str, entity_b: str
    ) -> Dict[str, Any]:
        """Find non-obvious connections between two entities via shared
        documents, overlapping timelines, and transitive paths."""
        a_lower = entity_a.lower()
        b_lower = entity_b.lower()
        a_like = f"%{a_lower}%"
        b_like = f"%{b_lower}%"

        # --- Direct connections: documents mentioning both ---
        direct_docs = self._query_dicts(
            "SELECT DISTINCT eq1.document_id, d.file_name "
            "FROM evidence_quotes eq1 "
            "JOIN evidence_quotes eq2 ON eq1.document_id = eq2.document_id "
            "LEFT JOIN documents d ON eq1.document_id = d.id "
            "WHERE LOWER(eq1.quote_text) LIKE ? "
            "AND LOWER(eq2.quote_text) LIKE ? "
            "AND eq1.id != eq2.id "
            "LIMIT 50",
            (a_like, b_like),
        )

        # --- Direct co-mentions in contradictions ---
        direct_contradictions = self._query_dicts(
            "SELECT id, contradiction_type, severity, "
            "source_a_text, source_b_text "
            "FROM contradiction_map "
            "WHERE (LOWER(source_a_text) LIKE ? OR LOWER(source_b_text) LIKE ?) "
            "AND (LOWER(source_a_text) LIKE ? OR LOWER(source_b_text) LIKE ?) "
            "LIMIT 50",
            (a_like, a_like, b_like, b_like),
        )

        # --- Direct co-mentions in impeachment items ---
        direct_impeachment = self._query_dicts(
            "SELECT id, speaker, legal_hook, statement "
            "FROM impeachment_items "
            "WHERE (LOWER(statement) LIKE ? OR LOWER(contradicting_text) LIKE ?) "
            "AND (LOWER(statement) LIKE ? OR LOWER(contradicting_text) LIKE ?) "
            "LIMIT 50",
            (a_like, a_like, b_like, b_like),
        )

        direct_connections = []
        for d in direct_docs:
            direct_connections.append({
                "type": "shared_document",
                "document_id": d.get("document_id"),
                "file_name": d.get("file_name"),
            })
        for c in direct_contradictions:
            direct_connections.append({
                "type": "contradiction",
                "id": c.get("id"),
                "contradiction_type": c.get("contradiction_type"),
                "severity": c.get("severity"),
            })
        for imp in direct_impeachment:
            direct_connections.append({
                "type": "impeachment",
                "id": imp.get("id"),
                "speaker": imp.get("speaker"),
                "legal_hook": imp.get("legal_hook"),
            })

        # --- Indirect / transitive connections (A → C → B) ---
        # Find documents mentioning A, then check if those docs also
        # reference something that connects to B
        a_doc_ids = self._query(
            "SELECT DISTINCT document_id FROM evidence_quotes "
            "WHERE LOWER(quote_text) LIKE ? AND document_id IS NOT NULL "
            "LIMIT 500",
            (a_like,),
        )
        a_docs = {r["document_id"] for r in a_doc_ids}

        b_doc_ids = self._query(
            "SELECT DISTINCT document_id FROM evidence_quotes "
            "WHERE LOWER(quote_text) LIKE ? AND document_id IS NOT NULL "
            "LIMIT 500",
            (b_like,),
        )
        b_docs = {r["document_id"] for r in b_doc_ids}

        shared_docs = a_docs & b_docs  # already captured as direct

        # Find bridge entities: other entities in A-docs that also appear
        # in B-docs (transitive)
        indirect_connections: List[Dict[str, Any]] = []
        if a_docs and b_docs:
            # Sample speakers from A-docs
            a_doc_sample = list(a_docs)[:100]
            placeholders = ",".join("?" * len(a_doc_sample))
            a_speakers = self._query(
                f"SELECT DISTINCT speaker FROM evidence_quotes "
                f"WHERE document_id IN ({placeholders}) "
                f"AND speaker IS NOT NULL",
                tuple(a_doc_sample),
            )
            b_doc_sample = list(b_docs)[:100]
            placeholders_b = ",".join("?" * len(b_doc_sample))
            b_speakers = self._query(
                f"SELECT DISTINCT speaker FROM evidence_quotes "
                f"WHERE document_id IN ({placeholders_b}) "
                f"AND speaker IS NOT NULL",
                tuple(b_doc_sample),
            )
            a_spk_set = {r["speaker"] for r in a_speakers}
            b_spk_set = {r["speaker"] for r in b_speakers}
            bridge_speakers = a_spk_set & b_spk_set
            for spk in bridge_speakers:
                indirect_connections.append({
                    "type": "bridge_speaker",
                    "entity": spk,
                    "path": f"{entity_a} ← doc ← {spk} → doc → {entity_b}",
                })

        # Strength score: weighted sum of connection counts
        strength = (
            len(direct_docs) * 1.0
            + len(direct_contradictions) * 2.0
            + len(direct_impeachment) * 1.5
            + len(indirect_connections) * 0.5
        )
        max_strength = 100.0
        normalised = min(strength / max_strength, 1.0)

        return {
            "entity_a": entity_a,
            "entity_b": entity_b,
            "direct_connections": direct_connections,
            "indirect_connections": indirect_connections,
            "shared_document_count": len(direct_docs),
            "contradiction_count": len(direct_contradictions),
            "impeachment_count": len(direct_impeachment),
            "strength": round(normalised, 4),
        }

    # ------------------------------------------------------------------
    # 6. cluster_evidence
    # ------------------------------------------------------------------
    def cluster_evidence(self, n_clusters: int = 10) -> List[Dict[str, Any]]:
        """Cluster evidence quotes into thematic groups using TF-IDF +
        KMeans (sklearn) with fallback to manual centroid clustering."""
        rows = self._query(
            "SELECT id, quote_text, evidence_category, speaker "
            "FROM evidence_quotes WHERE quote_text IS NOT NULL "
            "ORDER BY RANDOM() LIMIT ?",
            (_MAX_SAMPLE,),
        )
        if not rows:
            return []

        texts = [r["quote_text"] for r in rows]
        ids = [r["id"] for r in rows]
        categories = [r["evidence_category"] for r in rows]

        if _HAS_SKLEARN:
            return self._cluster_sklearn(texts, ids, categories, n_clusters)
        else:
            return self._cluster_manual(texts, ids, categories, n_clusters)

    def _cluster_sklearn(
        self,
        texts: List[str],
        ids: List[int],
        categories: List[str],
        n_clusters: int,
    ) -> List[Dict[str, Any]]:
        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            min_df=5,
            max_df=0.8,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        actual_k = min(n_clusters, tfidf_matrix.shape[0])
        km = KMeans(n_clusters=actual_k, n_init=5, max_iter=100, random_state=42)
        labels = km.fit_predict(tfidf_matrix)

        clusters: List[Dict[str, Any]] = []
        for cid in range(actual_k):
            mask = labels == cid
            indices = np.where(mask)[0]
            if len(indices) == 0:
                continue

            # Top terms by centroid weight
            centroid = km.cluster_centers_[cid]
            top_term_idx = centroid.argsort()[-10:][::-1]
            top_terms = [feature_names[i] for i in top_term_idx]

            sample_idx = indices[:5]
            sample_quotes = [texts[i][:200] for i in sample_idx]
            cluster_cats = Counter(categories[i] for i in indices if categories[i])

            clusters.append({
                "cluster_id": cid,
                "label": " | ".join(top_terms[:3]),
                "size": int(len(indices)),
                "top_terms": top_terms,
                "sample_quotes": sample_quotes,
                "dominant_category": (
                    cluster_cats.most_common(1)[0][0] if cluster_cats else None
                ),
            })

        clusters.sort(key=lambda c: c["size"], reverse=True)
        return clusters

    def _cluster_manual(
        self,
        texts: List[str],
        ids: List[int],
        categories: List[str],
        n_clusters: int,
    ) -> List[Dict[str, Any]]:
        """Fallback clustering without sklearn: group by category +
        keyword frequency."""
        cat_groups: Dict[str, List[int]] = defaultdict(list)
        for i, cat in enumerate(categories):
            cat_groups[cat or "unknown"].append(i)

        clusters: List[Dict[str, Any]] = []
        for cid, (cat, indices) in enumerate(
            sorted(cat_groups.items(), key=lambda x: -len(x[1]))[:n_clusters]
        ):
            # Extract top terms via simple word frequency
            word_freq: Counter = Counter()
            stop = {
                "the", "and", "for", "that", "this", "with", "was", "are",
                "has", "have", "not", "from", "but", "been", "will", "can",
                "had", "her", "his", "they", "its", "you", "all", "she",
                "were", "when", "there", "their", "would", "each", "which",
            }
            for idx in indices[:2000]:
                words = re.findall(r"[a-z]{3,}", texts[idx].lower())
                word_freq.update(w for w in words if w not in stop)

            top_terms = [w for w, _ in word_freq.most_common(10)]
            sample_quotes = [texts[i][:200] for i in indices[:5]]

            clusters.append({
                "cluster_id": cid,
                "label": f"{cat} — {' | '.join(top_terms[:3])}",
                "size": len(indices),
                "top_terms": top_terms,
                "sample_quotes": sample_quotes,
                "dominant_category": cat,
            })

        return clusters

    # ------------------------------------------------------------------
    # 7. find_anomalous_evidence
    # ------------------------------------------------------------------
    def find_anomalous_evidence(
        self, top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """Statistical outlier detection via TF-IDF distance from cluster
        centres.  Falls back to length/rarity heuristics if sklearn is
        unavailable."""
        rows = self._query(
            "SELECT id, quote_text, evidence_category, speaker, "
            "legal_significance FROM evidence_quotes "
            "WHERE quote_text IS NOT NULL "
            "ORDER BY RANDOM() LIMIT ?",
            (_MAX_SAMPLE,),
        )
        if not rows:
            return []

        texts = [r["quote_text"] for r in rows]
        ids = [r["id"] for r in rows]
        categories = [r["evidence_category"] for r in rows]
        speakers = [r["speaker"] for r in rows]
        significance = [r["legal_significance"] for r in rows]

        if _HAS_SKLEARN:
            return self._anomalies_tfidf(
                texts, ids, categories, speakers, significance, top_n
            )
        else:
            return self._anomalies_heuristic(
                texts, ids, categories, speakers, significance, top_n
            )

    def _anomalies_tfidf(
        self,
        texts: List[str],
        ids: List[int],
        categories: List[str],
        speakers: List[Optional[str]],
        significance: List[Optional[str]],
        top_n: int,
    ) -> List[Dict[str, Any]]:
        vectorizer = TfidfVectorizer(
            max_features=3000,
            stop_words="english",
            min_df=3,
            max_df=0.8,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)

        n_clusters = min(10, tfidf_matrix.shape[0])
        km = KMeans(n_clusters=n_clusters, n_init=3, max_iter=50, random_state=42)
        labels = km.fit_predict(tfidf_matrix)

        # Distance from assigned cluster centre
        if _HAS_SCIPY:
            centres = km.cluster_centers_
            distances = np.array([
                float(cdist(
                    tfidf_matrix[i].toarray(),
                    centres[labels[i]:labels[i] + 1],
                )[0, 0])
                for i in range(len(texts))
            ])
        else:
            distances = np.array([
                float(np.linalg.norm(
                    tfidf_matrix[i].toarray() - km.cluster_centers_[labels[i]]
                ))
                for i in range(len(texts))
            ])

        # Use percentile-based detection: items in the top percentile
        # of distance are anomalous (z-score on high-dim TF-IDF is often
        # compressed, so percentile rank is more robust).
        p95 = float(np.percentile(distances, 95))
        mean_d = float(np.mean(distances))
        std_d = float(np.std(distances)) or 1.0

        # Anomaly score: normalised distance (higher = more anomalous)
        top_idx = np.argsort(distances)[-top_n:][::-1]
        anomalies: List[Dict[str, Any]] = []
        for idx in top_idx:
            dist = float(distances[idx])
            z = (dist - mean_d) / std_d
            pct_rank = float(np.searchsorted(np.sort(distances), dist)) / len(distances)
            anomalies.append({
                "evidence_id": ids[idx],
                "anomaly_score": round(pct_rank, 4),
                "distance_from_cluster": round(dist, 4),
                "z_score": round(z, 4),
                "above_p95": dist > p95,
                "cluster_label": int(labels[idx]),
                "reason": self._anomaly_reason_pct(pct_rank),
                "quote_text": texts[idx][:300],
                "evidence_category": categories[idx],
                "speaker": speakers[idx],
            })

        return anomalies

    def _anomalies_heuristic(
        self,
        texts: List[str],
        ids: List[int],
        categories: List[str],
        speakers: List[Optional[str]],
        significance: List[Optional[str]],
        top_n: int,
    ) -> List[Dict[str, Any]]:
        """Heuristic outlier detection: unusual length, rare category,
        rare speaker."""
        lengths = np.array([len(t) for t in texts], dtype=float)
        mean_len = float(np.mean(lengths))
        std_len = float(np.std(lengths)) or 1.0

        cat_counts = Counter(categories)
        total = len(categories)

        scores = []
        for i in range(len(texts)):
            z_len = abs((lengths[i] - mean_len) / std_len)
            cat_rarity = 1.0 - (cat_counts[categories[i]] / total)
            score = z_len * 0.6 + cat_rarity * 10.0
            scores.append(score)

        scores_arr = np.array(scores)
        top_idx = np.argsort(scores_arr)[-top_n:][::-1]

        anomalies: List[Dict[str, Any]] = []
        for idx in top_idx:
            anomalies.append({
                "evidence_id": ids[idx],
                "anomaly_score": round(float(scores_arr[idx]), 4),
                "reason": "unusual_length_or_rare_category",
                "quote_text": texts[idx][:300],
                "evidence_category": categories[idx],
                "speaker": speakers[idx],
            })
        return anomalies

    @staticmethod
    def _anomaly_reason_pct(pct_rank: float) -> str:
        if pct_rank > 0.99:
            return "extreme_outlier (top 1%)"
        elif pct_rank > 0.95:
            return "strong_outlier (top 5%)"
        elif pct_rank > 0.90:
            return "moderate_outlier (top 10%)"
        else:
            return "mild_outlier"

    @staticmethod
    def _anomaly_reason(z: float) -> str:
        if z > 3.0:
            return "extreme_outlier"
        elif z > 2.0:
            return "strong_outlier"
        else:
            return "moderate_outlier"

    # ------------------------------------------------------------------
    # 8. generate_pattern_report
    # ------------------------------------------------------------------
    def generate_pattern_report(self) -> Dict[str, Any]:
        """Complete pattern mining report across all analysis dimensions."""
        print("[PatternMiner] Mining evidence association rules ...")
        evidence_rules = self.mine_evidence_patterns()

        print("[PatternMiner] Mining contradiction patterns ...")
        contradiction_pats = self.mine_contradiction_patterns()

        print("[PatternMiner] Mining judicial patterns ...")
        judicial_pats = self.mine_judicial_patterns()

        print("[PatternMiner] Mining procedural patterns ...")
        procedural_pats = self.mine_procedural_patterns()

        print("[PatternMiner] Finding anomalous evidence ...")
        anomalies = self.find_anomalous_evidence(top_n=20)

        print("[PatternMiner] Mining temporal sequences ...")
        temporal_seqs = self.mine_temporal_sequences()

        print("[PatternMiner] Finding hidden connections (Watson ↔ Court) ...")
        hidden_watson_court = self.find_hidden_connections("Watson", "Court")

        # --- Actionable insights ---
        insights: List[str] = []

        # Bias insight
        rp = judicial_pats.get("ruling_patterns", {})
        pro_p = rp.get("pro_pigors_rulings", 0)
        pro_w = rp.get("pro_watson_rulings", 0)
        if pro_w > pro_p and pro_p + pro_w > 0:
            ratio = pro_w / (pro_p + pro_w)
            insights.append(
                f"BIAS SIGNAL: {ratio:.0%} of classifiable rulings favor "
                f"Watson ({pro_w} vs {pro_p} for Pigors). "
                f"Review for MCR 2.003 disqualification."
            )

        # Ex parte insight
        ex_count = len(judicial_pats.get("ex_parte_events", []))
        if ex_count > 0:
            insights.append(
                f"EX PARTE PATTERN: {ex_count} ex parte events detected. "
                f"Each must be scrutinised for due process compliance."
            )

        # Violation insight
        bi = judicial_pats.get("bias_indicators", {})
        total_v = bi.get("total_violations", 0)
        if total_v > 0:
            insights.append(
                f"JUDICIAL VIOLATIONS: {total_v} violations catalogued. "
                f"Top canons: {bi.get('violations_by_canon', {})}. "
                f"Supports JTC complaint and appellate argument."
            )

        # Contradiction insight
        total_c = contradiction_pats.get("total_contradictions", 0)
        if total_c > 0:
            spk_pats = contradiction_pats.get("speaker_patterns", {})
            watson_count = sum(spk_pats.get("WATSON", {}).values())
            insights.append(
                f"CONTRADICTIONS: {total_c} total, Watson mentioned in "
                f"{watson_count} contradiction records. Mine for MRE 613(b) "
                f"impeachment material."
            )

        # Anomaly insight
        if anomalies:
            extreme = [a for a in anomalies if a.get("anomaly_score", 0) > 3.0]
            insights.append(
                f"ANOMALIES: {len(anomalies)} outlier evidence items "
                f"({len(extreme)} extreme). Review for undiscovered arguments."
            )

        # Top association rules insight
        if evidence_rules:
            top3 = evidence_rules[:3]
            rule_strs = [
                f"{r['antecedent']}→{r['consequent']} "
                f"(lift={r['lift']})"
                for r in top3
            ]
            insights.append(
                f"TOP ASSOCIATIONS: {'; '.join(rule_strs)}"
            )

        return {
            "generated_at": datetime.now().isoformat(),
            "evidence_association_rules": {
                "total_rules": len(evidence_rules),
                "top_rules": evidence_rules[:20],
            },
            "contradiction_patterns": contradiction_pats,
            "judicial_patterns": judicial_pats,
            "procedural_patterns": procedural_pats,
            "anomalous_evidence": {
                "total_anomalies": len(anomalies),
                "items": anomalies,
            },
            "temporal_sequences": temporal_seqs,
            "hidden_connections_watson_court": hidden_watson_court,
            "actionable_insights": insights,
        }

    # ------------------------------------------------------------------
    # 9. mine_temporal_sequences
    # ------------------------------------------------------------------
    def mine_temporal_sequences(
        self, window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Sequential pattern mining: event_A → delay → event_B within
        a sliding window."""
        events = self._query_dicts(
            "SELECT event_id, event_date_iso, title, event_type "
            "FROM docket_events WHERE event_date_iso IS NOT NULL "
            "ORDER BY event_date_iso"
        )
        if len(events) < 2:
            return []

        # Parse dates
        parsed: List[Tuple[datetime, Dict]] = []
        for ev in events:
            d = self._parse_date(ev.get("event_date_iso", ""))
            if d:
                parsed.append((d, ev))
        parsed.sort(key=lambda x: x[0])

        # Count sequences A → B within window
        seq_counter: Counter = Counter()
        seq_delays: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        for i in range(len(parsed)):
            date_a, ev_a = parsed[i]
            type_a = ev_a.get("event_type", "")
            for j in range(i + 1, len(parsed)):
                date_b, ev_b = parsed[j]
                delta = (date_b - date_a).days
                if delta > window_days:
                    break
                if delta < 0:
                    continue
                type_b = ev_b.get("event_type", "")
                if type_a and type_b:
                    key = (type_a, type_b)
                    seq_counter[key] += 1
                    seq_delays[key].append(float(delta))

        # Build result
        sequences: List[Dict[str, Any]] = []
        total_pairs = sum(seq_counter.values()) or 1
        for (a, b), count in seq_counter.most_common(30):
            delays = seq_delays[(a, b)]
            avg_delay = statistics.mean(delays) if delays else 0
            confidence = count / total_pairs
            sequences.append({
                "sequence": f"{a} → {b}",
                "frequency": count,
                "avg_delay_days": round(avg_delay, 1),
                "min_delay_days": min(delays) if delays else 0,
                "max_delay_days": max(delays) if delays else 0,
                "confidence": round(confidence, 4),
            })

        return sequences

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(date_str)[:19], fmt)
            except (ValueError, TypeError):
                continue
        return None

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


# ======================================================================
# __main__ — run all mining operations and print summary
# ======================================================================
if __name__ == "__main__":
    import json
    import time

    SEP = "=" * 72

    print(SEP)
    print("  MANBEARPIG LitigationOS — Deep Pattern Mining Engine")
    print("  Pigors v. Watson — Pattern Discovery Report")
    print(SEP)

    t0 = time.time()
    miner = PatternMiner()

    # --- 1. Evidence association rules ---
    print(f"\n{'─'*60}")
    print("1. EVIDENCE ASSOCIATION RULES")
    print(f"{'─'*60}")
    rules = miner.mine_evidence_patterns()
    print(f"   Total rules discovered: {len(rules)}")
    for r in rules[:10]:
        print(
            f"   {r['antecedent']:50s} → {r['consequent']:50s}  "
            f"sup={r['support']:.4f}  conf={r['confidence']:.4f}  "
            f"lift={r['lift']:.2f}"
        )

    # --- 2. Contradiction patterns ---
    print(f"\n{'─'*60}")
    print("2. CONTRADICTION PATTERNS")
    print(f"{'─'*60}")
    cpats = miner.mine_contradiction_patterns()
    print(f"   Total contradictions: {cpats['total_contradictions']}")
    print(f"   Speaker patterns:")
    for spk, types in cpats["speaker_patterns"].items():
        total = sum(types.values())
        print(f"     {spk}: {total} mentions — {dict(types)}")
    print(f"   Severity by type:")
    for ct, sevs in cpats["severity_by_type"].items():
        print(f"     {ct}: {dict(sevs)}")
    if cpats["type_co_occurrences"]:
        print(f"   Top type co-occurrences:")
        for co in cpats["type_co_occurrences"][:5]:
            print(f"     {co['types']}: {co['count']}")

    # --- 3. Judicial patterns ---
    print(f"\n{'─'*60}")
    print("3. JUDICIAL BEHAVIOUR PATTERNS")
    print(f"{'─'*60}")
    jpats = miner.mine_judicial_patterns()
    rp = jpats["ruling_patterns"]
    print(f"   Pro-Pigors rulings:  {rp['pro_pigors_rulings']}")
    print(f"   Pro-Watson rulings:  {rp['pro_watson_rulings']}")
    print(f"   Neutral rulings:     {rp['neutral_rulings']}")
    print(f"   Ex parte events:     {len(jpats['ex_parte_events'])}")
    for ep in jpats["ex_parte_events"]:
        print(f"     [{ep['date']}] {ep['title']}")
    bi = jpats["bias_indicators"]
    print(f"   Judicial violations:  {bi['total_violations']}")
    print(f"   Violations by canon:  {bi['violations_by_canon']}")
    print(f"   Violations by severity: {bi['violations_by_severity']}")

    # --- 4. Procedural patterns ---
    print(f"\n{'─'*60}")
    print("4. PROCEDURAL PATTERNS")
    print(f"{'─'*60}")
    ppats = miner.mine_procedural_patterns()
    if ppats["timing_patterns"]:
        tp = ppats["timing_patterns"]
        print(
            f"   Filing → Order: mean={tp.get('mean_days_filing_to_order')} days, "
            f"median={tp.get('median_days_filing_to_order')} days"
        )
    print(f"   Anomalies found: {len(ppats['anomalies'])}")
    for a in ppats["anomalies"]:
        print(
            f"     [{a['date']}] {a['filing'][:60]} — "
            f"{a['days_to_order']} days (z={a['z_score']}) {a['anomaly']}"
        )

    # --- 5. Hidden connections ---
    print(f"\n{'─'*60}")
    print("5. HIDDEN CONNECTIONS: Watson ↔ Court")
    print(f"{'─'*60}")
    hc = miner.find_hidden_connections("Watson", "Court")
    print(f"   Direct connections: {len(hc['direct_connections'])}")
    print(f"   Indirect connections: {len(hc['indirect_connections'])}")
    print(f"   Connection strength: {hc['strength']}")
    for ic in hc["indirect_connections"][:5]:
        print(f"     Bridge: {ic.get('entity')} — {ic.get('path')}")

    # --- 6. Evidence clusters ---
    print(f"\n{'─'*60}")
    print("6. EVIDENCE CLUSTERS")
    print(f"{'─'*60}")
    clusters = miner.cluster_evidence(n_clusters=10)
    for cl in clusters:
        print(
            f"   Cluster {cl['cluster_id']}: [{cl['size']} items] "
            f"{cl['label']}"
        )

    # --- 7. Anomalous evidence ---
    print(f"\n{'─'*60}")
    print("7. ANOMALOUS EVIDENCE")
    print(f"{'─'*60}")
    anoms = miner.find_anomalous_evidence(top_n=15)
    print(f"   Total anomalies: {len(anoms)}")
    for a in anoms[:10]:
        print(
            f"   [{a['anomaly_score']:.2f}] id={a['evidence_id']} "
            f"({a.get('reason','')}) — {a['quote_text'][:80]}..."
        )

    # --- 8. Temporal sequences ---
    print(f"\n{'─'*60}")
    print("8. TEMPORAL SEQUENCES")
    print(f"{'─'*60}")
    tseqs = miner.mine_temporal_sequences()
    for s in tseqs[:15]:
        print(
            f"   {s['sequence']:40s}  freq={s['frequency']:3d}  "
            f"avg_delay={s['avg_delay_days']:.1f}d  "
            f"conf={s['confidence']:.4f}"
        )

    # --- 9. Full report ---
    print(f"\n{'─'*60}")
    print("9. GENERATING FULL PATTERN REPORT ...")
    print(f"{'─'*60}")
    report = miner.generate_pattern_report()
    print(f"   Actionable insights:")
    for ins in report.get("actionable_insights", []):
        print(f"   ▸ {ins}")

    elapsed = time.time() - t0
    print(f"\n{SEP}")
    print(f"  Completed in {elapsed:.1f}s")
    print(f"  {len(rules)} association rules | {cpats['total_contradictions']} contradictions")
    print(f"  {len(clusters)} clusters | {len(anoms)} anomalies | {len(tseqs)} sequences")
    print(SEP)

    miner.close()
