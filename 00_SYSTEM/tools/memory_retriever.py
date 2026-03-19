"""
memory_retriever.py — Document-Specific Memory Pack Generator
=============================================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Generates tiered memory packs for each court filing document by querying
litigation_context.db. Implements:
- Tiered Memory System (conversation-memory skill)
- Context Quality Gates (context-manager skill)
- Memory Type Architecture (agent-memory-systems skill)

No network calls. Pure SQLite + FTS5.
"""

import sqlite3
import json
import os
import re
import time
from typing import Dict, List, Any, Optional

DB_PATH = r"C:\Users\andre\litigation_context.db"
VEHICLES_ROOT = r"C:\Users\andre\LitigationOS\06_VEHICLES"

DOCUMENT_TOPICS = {
    "MOTION_DISQUALIFY_JUDGE_MCNEILL_V4.md": {
        "lane": "A", "type": "motion",
        "topics": ["judicial disqualification", "bias", "ex parte", "due process", "recusal"],
        "vehicle_match": "JUDICIAL_DISQUALIFICATION",
    },
    "EMERGENCY_MOTION_PARENTING_TIME.md": {
        "lane": "A", "type": "motion",
        "topics": ["parenting time", "emergency relief", "irreparable harm", "best interest", "ex parte"],
        "vehicle_match": "EMERGENCY_MOTION_RESTORE_PT",
    },
    "EMERGENCY_MOTION_RESTORE_PARENTING_TIME_V4.md": {
        "lane": "A", "type": "motion",
        "topics": ["parenting time", "ex parte order", "hearsay", "custody suspension", "separation harm"],
        "vehicle_match": "EMERGENCY_MOTION_RESTORE_PT",
    },
    "MOTION_CHANGE_OF_VENUE.md": {
        "lane": "A", "type": "motion",
        "topics": ["venue change", "judicial bias", "institutional connections", "impropriety", "fair trial"],
        "vehicle_match": None,
    },
    "MOTION_TO_COMPEL_DISCOVERY.md": {
        "lane": "A", "type": "motion",
        "topics": ["discovery enforcement", "employment records", "insider access", "sanctions"],
        "vehicle_match": None,
    },
    "MOTION_FOR_CONTEMPT.md": {
        "lane": "A", "type": "motion",
        "topics": ["contempt", "parenting time violation", "Factor J", "willful failure", "mandatory remedies"],
        "vehicle_match": None,
    },
    "MOTION_CONTEMPT_SHOW_CAUSE_V4.md": {
        "lane": "A", "type": "motion",
        "topics": ["contempt", "parenting time denial", "alienation pattern", "Factor J", "child welfare"],
        "vehicle_match": None,
    },
    "MOTION_MODIFY_CUSTODY_V4.md": {
        "lane": "A", "type": "motion",
        "topics": ["custody modification", "changed circumstances", "Vodvarka", "alienation", "best interest"],
        "vehicle_match": None,
    },
    "CIVIL_COMPLAINT_WATSON.md": {
        "lane": "A", "type": "complaint",
        "topics": ["tortious interference", "emotional distress", "parental alienation", "abuse of process", "conspiracy"],
        "vehicle_match": None,
    },
    "TORT_COMPLAINT_WATSON_FAMILY.md": {
        "lane": "A", "type": "complaint",
        "topics": ["tortious interference", "alienation", "conspiracy", "PPO weaponization", "parental rights"],
        "vehicle_match": None,
    },
    "DISCOVERY_REQUESTS_V4.md": {
        "lane": "A", "type": "discovery",
        "topics": ["discovery", "interrogatories", "document requests", "employment records", "bias investigation"],
        "vehicle_match": None,
    },
    "AFFIDAVIT_ANDREW_PIGORS.md": {
        "lane": "A", "type": "affidavit",
        "topics": ["parenting time denial", "alienation", "judicial bias", "mental health", "ex parte"],
        "vehicle_match": None,
    },
    "PROPOSED_ORDERS_BUNDLE_V4.md": {
        "lane": "A", "type": "proposed_order",
        "topics": ["parenting time restoration", "disqualification", "ex parte vacation", "reassignment"],
        "vehicle_match": None,
    },
    "SHADY_OAKS_FILING_PACKAGE.md": {
        "lane": "B", "type": "complaint",
        "topics": ["housing", "landlord tenant", "habitability", "retaliation", "fair housing"],
        "vehicle_match": None,
    },
    "SHADY_OAKS_EXHIBIT_INDEX.md": {
        "lane": "B", "type": "exhibit_index",
        "topics": ["housing evidence", "exhibits", "inspection reports", "lease violations"],
        "vehicle_match": None,
    },
    "CIVIL_COMPLAINT_WATSONS_V4.md": {
        "lane": "C", "type": "complaint",
        "topics": ["parental alienation", "institutional bias", "appellate connection", "civil rights"],
        "vehicle_match": None,
    },
    "MOTION_CHANGE_OF_VENUE_V4.md": {
        "lane": "C", "type": "motion",
        "topics": ["venue change", "institutional bias", "structural advantage", "prosecutorial connections"],
        "vehicle_match": None,
    },
    "MOTION_TERMINATE_PPO_V4.md": {
        "lane": "D", "type": "motion",
        "topics": ["PPO termination", "manufactured threat", "hearsay", "changed circumstances", "drug allegations"],
        "vehicle_match": "MODIFY_TERMINATE_PPO",
    },
    "JTC_SUPPLEMENTAL_BRIEF_V4.md": {
        "lane": "E", "type": "brief",
        "topics": ["judicial misconduct", "Canon violations", "benchbook violations", "ex parte", "systemic pattern"],
        "vehicle_match": "JTC_COMPLAINT",
    },
    "MSC_SUPERINTENDING_CONTROL_APPLICATION.md": {
        "lane": "E", "type": "application",
        "topics": ["superintending control", "trial court lawlessness", "statutory remedies failure", "due process"],
        "vehicle_match": None,
    },
    "APPELLANT_BRIEF_COA_366810.md": {
        "lane": "F", "type": "brief",
        "topics": ["appellate review", "ex parte defects", "best interest failure", "parental rights", "cumulative error"],
        "vehicle_match": None,
    },
    "COA_366810_APPELLANTS_BRIEF.md": {
        "lane": "F", "type": "brief",
        "topics": ["appellate arguments", "best interest analysis", "benchbook violations", "Factor J", "reassignment"],
        "vehicle_match": None,
    },
    "MSC_APPLICATION_LEAVE_TO_APPEAL.md": {
        "lane": "G", "type": "application",
        "topics": ["leave to appeal", "significant question", "appellate review", "constitutional rights"],
        "vehicle_match": None,
    },
    "MSC_BRIEF_IN_SUPPORT.md": {
        "lane": "G", "type": "brief",
        "topics": ["superintending control", "appellate review", "constitutional rights", "judicial misconduct"],
        "vehicle_match": None,
    },
    "MSC_APPENDIX_INDEX.md": {
        "lane": "G", "type": "index",
        "topics": ["appendix", "record compilation", "exhibit index"],
        "vehicle_match": None,
    },
    "MSC_RESEARCH_AGENT_GUIDE.md": {
        "lane": "G", "type": "guide",
        "topics": ["research methodology", "authority search", "legal analysis"],
        "vehicle_match": None,
    },
}


class MemoryRetriever:
    """Generates tiered memory packs for court filing documents."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._error_log: List[str] = []
        self.conn: Optional[sqlite3.Connection] = None
        self._connect_with_retry()

    def _connect_with_retry(self, max_retries: int = 3):
        """Connect to DB with exponential backoff (1s, 2s, 4s)."""
        for attempt in range(max_retries):
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                self.conn.execute("SELECT 1")
                return
            except sqlite3.Error as e:
                wait = 2 ** attempt
                self._error_log.append(
                    "DB connect attempt %d failed: %s (retry in %ds)" % (attempt + 1, e, wait)
                )
                if attempt < max_retries - 1:
                    time.sleep(wait)
        raise RuntimeError("Failed to connect to %s after %d attempts" % (self.db_path, max_retries))

    def _safe_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query with error handling. Returns list of dicts."""
        try:
            cur = self.conn.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as e:
            self._error_log.append("Query error: %s | SQL: %s" % (e, sql[:200]))
            return []

    @staticmethod
    def _fts_match_expr(topics: List[str]) -> str:
        """Build an FTS5 MATCH expression from topics using OR."""
        # Sanitize: remove special FTS5 chars, keep alphanumeric and spaces
        sanitized = []
        for t in topics:
            clean = re.sub(r'[^\w\s]', '', t).strip()
            if clean:
                # Quote multi-word phrases
                if ' ' in clean:
                    sanitized.append('"%s"' % clean)
                else:
                    sanitized.append(clean)
        return " OR ".join(sanitized) if sanitized else '""'

    @staticmethod
    def _like_clauses(columns: List[str], topics: List[str]) -> str:
        """Build LIKE-based WHERE clause for non-FTS tables."""
        clauses = []
        for topic in topics:
            for col in columns:
                clauses.append("%s LIKE '%%%s%%'" % (col, topic.replace("'", "''")))
        return " OR ".join(clauses) if clauses else "1=0"

    def _retrieve_authority(self, topics: List[str], limit: int = 10) -> List[Dict]:
        """Query auth_rules_fts and rules_text_fts for governing authority."""
        results = []
        match_expr = self._fts_match_expr(topics)

        # Tier 1: auth_rules via FTS5
        try:
            sql = """
                SELECT ar.rule_number, ar.title,
                       SUBSTR(ar.full_text, 1, 500) AS text_excerpt,
                       'auth_rules' AS source_table,
                       fts.rank AS fts_rank
                FROM auth_rules_fts fts
                JOIN auth_rules ar ON ar.rowid = fts.rowid
                WHERE auth_rules_fts MATCH ?
                ORDER BY fts.rank
                LIMIT ?
            """
            rows = self._safe_query(sql, (match_expr, limit))
            results.extend(rows)
        except Exception as e:
            self._error_log.append("auth_rules_fts failed: %s, falling back to LIKE" % e)

        # Fallback / supplement: LIKE on auth_rules if FTS returned nothing
        if not results:
            like_where = self._like_clauses(["full_text", "title"], topics)
            sql = """
                SELECT rule_number, title,
                       SUBSTR(full_text, 1, 500) AS text_excerpt,
                       'auth_rules' AS source_table,
                       0.0 AS fts_rank
                FROM auth_rules
                WHERE %s
                LIMIT ?
            """ % like_where
            results.extend(self._safe_query(sql, (limit,)))

        # Tier 2: rules_text via FTS5
        try:
            sql = """
                SELECT rt.rule AS rule_number, rt.chapter AS title,
                       SUBSTR(rt.context, 1, 500) AS text_excerpt,
                       'rules_text' AS source_table,
                       fts.rank AS fts_rank
                FROM rules_text_fts fts
                JOIN rules_text rt ON rt.id = fts.rowid
                WHERE rules_text_fts MATCH ?
                ORDER BY fts.rank
                LIMIT ?
            """
            rows = self._safe_query(sql, (match_expr, limit))
            results.extend(rows)
        except Exception as e:
            self._error_log.append("rules_text_fts failed: %s" % e)

        # Deduplicate by rule_number, keep best rank
        seen = {}
        for r in results:
            key = r.get("rule_number", "")
            if key not in seen or (r.get("fts_rank") or 0) < (seen[key].get("fts_rank") or 0):
                seen[key] = r
        deduped = sorted(seen.values(), key=lambda x: x.get("fts_rank") or 0)
        return deduped[:limit]

    def _retrieve_evidence(self, topics: List[str], limit: int = 10) -> List[Dict]:
        """Query evidence_quotes_fts for supporting evidence."""
        match_expr = self._fts_match_expr(topics)

        # FTS5 primary path
        sql = """
            SELECT SUBSTR(eq.quote_text, 1, 300) AS quote_text,
                   eq.evidence_category, eq.page_number,
                   eq.speaker, eq.legal_significance,
                   eq.document_id
            FROM evidence_quotes_fts fts
            JOIN evidence_quotes eq ON eq.id = fts.rowid
            WHERE evidence_quotes_fts MATCH ?
            ORDER BY fts.rank
            LIMIT ?
        """
        results = self._safe_query(sql, (match_expr, limit))

        # LIKE fallback
        if not results:
            like_where = self._like_clauses(["quote_text", "legal_significance"], topics)
            sql = """
                SELECT SUBSTR(quote_text, 1, 300) AS quote_text,
                       evidence_category, page_number,
                       speaker, legal_significance, document_id
                FROM evidence_quotes
                WHERE %s
                LIMIT ?
            """ % like_where
            results = self._safe_query(sql, (limit,))

        return results

    def _retrieve_impeachment(self, topics: List[str], limit: int = 5) -> List[Dict]:
        """Query impeachment_items using LIKE (no FTS5 available)."""
        like_where = self._like_clauses(["statement", "contradicting_text", "legal_hook"], topics)
        sql = """
            SELECT item_type, speaker,
                   SUBSTR(statement, 1, 200) AS statement,
                   SUBSTR(contradicting_text, 1, 200) AS contradicting_text,
                   legal_hook, severity
            FROM impeachment_items
            WHERE %s
            ORDER BY
                CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    ELSE 4
                END
            LIMIT ?
        """ % like_where
        return self._safe_query(sql, (limit,))

    def _retrieve_adversary_models(self, vehicle_match: Optional[str]) -> List[Dict]:
        """Query adversary_models for anticipated attacks and rebuttals."""
        if not vehicle_match:
            return []
        sql = """
            SELECT attack_type, attack_description,
                   rebuttal_strategy, rebuttal_authority,
                   risk_level
            FROM adversary_models
            WHERE filing_vehicle = ?
        """
        return self._safe_query(sql, (vehicle_match,))

    def _retrieve_contradictions(self, topics: List[str], limit: int = 5) -> List[Dict]:
        """Query contradiction_map using LIKE."""
        like_where = self._like_clauses(["source_a_text", "source_b_text"], topics)
        sql = """
            SELECT SUBSTR(source_a_text, 1, 200) AS source_a_text,
                   SUBSTR(source_b_text, 1, 200) AS source_b_text,
                   contradiction_type, severity
            FROM contradiction_map
            WHERE %s
            ORDER BY
                CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    ELSE 4
                END
            LIMIT ?
        """ % like_where
        return self._safe_query(sql, (limit,))

    def _retrieve_judicial_violations(self, limit: int = 10) -> List[Dict]:
        """Query judicial_violations for top violations by severity."""
        sql = """
            SELECT SUBSTR(violation_description, 1, 200) AS violation_description,
                   canon_number, severity, judge_name
            FROM judicial_violations
            ORDER BY
                CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    ELSE 4
                END
            LIMIT ?
        """
        return self._safe_query(sql, (limit,))

    def _build_entity_context(self) -> Dict:
        """Return static entity context with case constants."""
        # Pull live counts from DB where possible
        violation_count = 0
        benchbook_count = 0
        try:
            rows = self._safe_query("SELECT COUNT(*) AS cnt FROM judicial_violations")
            violation_count = rows[0]["cnt"] if rows else 0
        except Exception:
            pass
        try:
            rows = self._safe_query("SELECT COUNT(*) AS cnt FROM auth_benchbook_violations")
            benchbook_count = rows[0]["cnt"] if rows else 0
        except Exception:
            pass

        return {
            "case_name": "Pigors v. Watson",
            "case_number": "2024-001507-DC",
            "court": "14th Circuit Court, Muskegon County",
            "judge": "Hon. Jenny L. McNeill",
            "plaintiff": "Andrew Pigors (pro se)",
            "defendant": "Tiffany Watson (fka Pigors)",
            "days_separated": "329+",
            "coa_docket": "366810",
            "violation_count": violation_count,
            "benchbook_violation_count": benchbook_count,
        }

    def _score_relevance(self, item: Dict, topics: List[str]) -> float:
        """Score 0.0-1.0 based on topic keyword matches, specificity, severity."""
        score = 0.0
        # Combine all text fields for matching
        text_blob = " ".join(
            str(v).lower() for v in item.values() if isinstance(v, str)
        )

        # Topic keyword match scoring
        topic_hits = 0
        for topic in topics:
            words = topic.lower().split()
            if all(w in text_blob for w in words):
                topic_hits += 1
            elif any(w in text_blob for w in words):
                topic_hits += 0.5
        if topics:
            score += 0.5 * min(topic_hits / len(topics), 1.0)

        # Specificity bonus: page numbers or dates present
        if item.get("page_number") or item.get("date_ref"):
            score += 0.15

        # Severity bonus
        severity = str(item.get("severity", "")).upper()
        if severity == "CRITICAL":
            score += 0.35
        elif severity == "HIGH":
            score += 0.25
        elif severity == "MEDIUM":
            score += 0.15

        # FTS rank bonus (lower rank = better match in SQLite FTS5)
        fts_rank = item.get("fts_rank")
        if fts_rank is not None and fts_rank < 0:
            # FTS5 rank is negative; more negative = better match
            # Flat bonus for being an FTS match + scaled rank bonus
            score += 0.15 + min(abs(fts_rank) / 30.0, 0.2)

        return min(score, 1.0)

    def build_memory_pack(self, doc_filename: str) -> Dict[str, Any]:
        """Build a complete memory pack for a single document."""
        doc_meta = DOCUMENT_TOPICS.get(doc_filename)
        if not doc_meta:
            self._error_log.append("Document not in DOCUMENT_TOPICS: %s" % doc_filename)
            return {
                "document": doc_filename,
                "error": "Not found in DOCUMENT_TOPICS",
                "tiers": {},
            }

        topics = doc_meta["topics"]
        vehicle_match = doc_meta.get("vehicle_match")

        # Retrieve all tiers
        authority = self._retrieve_authority(topics)
        evidence = self._retrieve_evidence(topics)
        impeachment = self._retrieve_impeachment(topics)
        adversary = self._retrieve_adversary_models(vehicle_match)
        contradictions = self._retrieve_contradictions(topics)
        judicial = self._retrieve_judicial_violations()
        entity_ctx = self._build_entity_context()

        # Score and filter (threshold 0.3)
        def score_filter(items: List[Dict]) -> List[Dict]:
            scored = []
            for item in items:
                s = self._score_relevance(item, topics)
                if s >= 0.3:
                    item["_relevance_score"] = round(s, 3)
                    scored.append(item)
            return sorted(scored, key=lambda x: x["_relevance_score"], reverse=True)

        return {
            "document": doc_filename,
            "lane": doc_meta["lane"],
            "doc_type": doc_meta["type"],
            "vehicle_match": vehicle_match,
            "topics": topics,
            "tiers": {
                "authority": score_filter(authority),
                "evidence": score_filter(evidence),
                "impeachment": score_filter(impeachment),
                "adversary_models": adversary,  # small set, no filtering needed
                "contradictions": score_filter(contradictions),
                "judicial_violations": score_filter(judicial),
            },
            "entity_context": entity_ctx,
            "tier_counts": {
                "authority": len(score_filter(authority)),
                "evidence": len(score_filter(evidence)),
                "impeachment": len(score_filter(impeachment)),
                "adversary_models": len(adversary),
                "contradictions": len(score_filter(contradictions)),
                "judicial_violations": len(score_filter(judicial)),
            },
        }

    def build_all_packs(self) -> Dict[str, Dict]:
        """Build memory packs for all documents in DOCUMENT_TOPICS."""
        packs = {}
        for filename in DOCUMENT_TOPICS:
            packs[filename] = self.build_memory_pack(filename)
        return packs

    def export_packs_json(self, output_path: str):
        """Write all packs to a JSON file."""
        packs = self.build_all_packs()
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(packs, f, indent=2, default=str)
        print("[memory_retriever] Exported %d packs to %s" % (len(packs), output_path))

    def close(self):
        """Close DB connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# ── Self-Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  memory_retriever.py — Self-Test")
    print("=" * 70)

    retriever = MemoryRetriever()
    print("[OK] Connected to %s" % DB_PATH)

    # Test documents: Lane A, Lane F, Lane G
    test_docs = [
        "MOTION_DISQUALIFY_JUDGE_MCNEILL_V4.md",   # Lane A
        "APPELLANT_BRIEF_COA_366810.md",             # Lane F
        "MSC_BRIEF_IN_SUPPORT.md",                   # Lane G
    ]

    total_items = 0
    all_have_authority = True

    for doc in test_docs:
        print("\n--- %s ---" % doc)
        pack = retriever.build_memory_pack(doc)
        counts = pack["tier_counts"]
        doc_total = sum(counts.values())
        total_items += doc_total

        print("  Lane: %s | Type: %s" % (pack["lane"], pack["doc_type"]))
        for tier, count in counts.items():
            print("  %-22s: %d items" % (tier, count))
        print("  Total items: %d" % doc_total)

        if counts["authority"] == 0:
            all_have_authority = False
            print("  [WARN] No authority items found!")

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print("  Documents tested:     %d" % len(test_docs))
    print("  Total items retrieved: %d" % total_items)
    print("  All have authority:   %s" % ("PASS" if all_have_authority else "FAIL"))
    print("  Error log entries:    %d" % len(retriever._error_log))

    if retriever._error_log:
        print("\n  Errors:")
        for e in retriever._error_log[:10]:
            print("    - %s" % e)

    retriever.close()
    print("\n[DONE] Self-test complete.")
