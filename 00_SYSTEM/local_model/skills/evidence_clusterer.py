#!/usr/bin/env python3
"""
MBP LitigationOS -- Evidence Clusterer Skill
==============================================
Cluster, group, search, and chain evidence from 308K+ evidence quotes,
30K+ drive evidence items, and Watson's evidence docs for
Pigors v. Watson.

Case: Andrew Pigors v. Tiffany Watson
Court: 14th Circuit Court, Muskegon County
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# Legal theme keyword mappings for clustering
THEME_KEYWORDS = {
    "ex_parte": ["ex parte", "one-sided", "without notice", "unilateral communication"],
    "custody": ["custody", "custodial", "parenting time", "visitation", "placement"],
    "ppo": ["ppo", "protection order", "personal protection", "restraining", "2950"],
    "alienation": ["alienat", "interfere", "gatekeep", "withhold", "undermine", "disparage"],
    "contempt": ["contempt", "sanction", "violat order", "willful", "disobey"],
    "due_process": ["due process", "notice", "hearing", "opportunity to be heard", "fundamental right"],
    "bias": ["bias", "prejudice", "partial", "favoritism", "impartial"],
    "evidence_tampering": ["tamper", "destroy", "spoliat", "fabricat", "falsif"],
    "financial": ["support", "garnish", "arrearage", "income", "financial"],
    "best_interest": ["best interest", "722.23", "factor", "welfare", "child's needs"],
    "domestic_violence": ["domestic violence", "abuse", "assault", "threat", "fear"],
    "housing": ["housing", "shady oaks", "residence", "living", "home"],
}

# Legal grounds for MSC action
MSC_GROUNDS = [
    "judicial_bias", "ex_parte_violations", "due_process_denial",
    "parental_alienation", "ppo_weaponization", "contempt_abuse",
    "benchbook_violations", "procedural_irregularities",
    "custody_modification_error", "evidence_exclusion",
    "hearing_denial", "fundamental_rights_violation",
]


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection with WAL mode."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class EvidenceClusterer:
    """Evidence clustering, searching, and chain-building engine."""

    def __init__(self):
        self._cache: Dict = {}

    # ── Theme Clustering ──────────────────────────────────────────────

    def cluster_by_theme(
        self, themes: Optional[List[str]] = None, limit_per: int = 50
    ) -> Dict:
        """Group evidence_quotes by legal themes using keyword matching."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        target_themes = themes or list(THEME_KEYWORDS.keys())
        clusters: Dict[str, List[Dict]] = {}

        try:
            for theme in target_themes:
                keywords = THEME_KEYWORDS.get(theme, [theme])
                like_clauses = " OR ".join(["quote_text LIKE ?"] * len(keywords))
                params = [f"%{kw}%" for kw in keywords]
                params.append(limit_per)

                rows = conn.execute(
                    f"SELECT id, substr(quote_text, 1, 400) as quote_text, "
                    f"speaker, date_ref, evidence_category, legal_significance "
                    f"FROM evidence_quotes "
                    f"WHERE {like_clauses} "
                    f"LIMIT ?",
                    params,
                ).fetchall()
                clusters[theme] = [dict(r) for r in rows]

            conn.close()
        except Exception as e:
            conn.close()
            return {"error": str(e)}

        summary = {t: len(v) for t, v in clusters.items()}
        return {
            "total_themes": len(clusters),
            "theme_counts": summary,
            "clusters": clusters,
        }

    def cluster_by_ground(
        self, grounds: Optional[List[str]] = None
    ) -> Dict:
        """Group evidence by 12 legal grounds from the MSC action."""
        target_grounds = grounds or MSC_GROUNDS
        # Map grounds to keywords
        ground_keywords = {
            "judicial_bias": ["bias", "prejudice", "partial", "impartial"],
            "ex_parte_violations": ["ex parte", "one-sided", "without notice"],
            "due_process_denial": ["due process", "notice", "hearing denied"],
            "parental_alienation": ["alienat", "gatekeep", "interfere", "withhold"],
            "ppo_weaponization": ["ppo", "protection order", "weapon"],
            "contempt_abuse": ["contempt", "sanction", "punish"],
            "benchbook_violations": ["benchbook", "canon", "judicial conduct"],
            "procedural_irregularities": ["procedur", "irregular", "MCR", "rule violation"],
            "custody_modification_error": ["custody", "modification", "change", "722.27"],
            "evidence_exclusion": ["evidence", "exclud", "suppress", "deny admission"],
            "hearing_denial": ["hearing", "denied", "refused", "opportunity"],
            "fundamental_rights_violation": ["fundamental", "constitutional", "parental right", "14th"],
        }

        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        clusters: Dict[str, List[Dict]] = {}
        try:
            for ground in target_grounds:
                keywords = ground_keywords.get(ground, [ground.replace("_", " ")])
                like_clauses = " OR ".join(["quote_text LIKE ?"] * len(keywords))
                params = [f"%{kw}%" for kw in keywords]

                rows = conn.execute(
                    f"SELECT id, substr(quote_text, 1, 400) as quote_text, "
                    f"speaker, date_ref, evidence_category "
                    f"FROM evidence_quotes "
                    f"WHERE {like_clauses} "
                    f"LIMIT 50",
                    params,
                ).fetchall()
                clusters[ground] = [dict(r) for r in rows]

            conn.close()
        except Exception as e:
            conn.close()
            return {"error": str(e)}

        return {
            "total_grounds": len(clusters),
            "ground_counts": {g: len(v) for g, v in clusters.items()},
            "clusters": clusters,
        }

    def cluster_by_witness(
        self, speaker: Optional[str] = None
    ) -> Dict:
        """Group evidence by speaker/witness."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        try:
            if speaker:
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 400) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance "
                    "FROM evidence_quotes "
                    "WHERE speaker LIKE ? LIMIT 100",
                    (f"%{speaker}%",),
                ).fetchall()
                result = {speaker: [dict(r) for r in rows]}
                conn.close()
                return {"speakers": result, "speaker_counts": {speaker: len(result[speaker])}}

            # Get top speakers
            rows = conn.execute(
                "SELECT speaker, COUNT(*) as cnt "
                "FROM evidence_quotes "
                "WHERE speaker IS NOT NULL AND speaker != '' "
                "GROUP BY speaker ORDER BY cnt DESC LIMIT 20"
            ).fetchall()
            speaker_counts = {r["speaker"]: r["cnt"] for r in rows}

            # Get sample quotes per top speaker
            speakers: Dict[str, List[Dict]] = {}
            for spk in list(speaker_counts.keys())[:10]:
                sample = conn.execute(
                    "SELECT id, substr(quote_text, 1, 300) as quote_text, "
                    "date_ref, evidence_category "
                    "FROM evidence_quotes WHERE speaker = ? LIMIT 20",
                    (spk,),
                ).fetchall()
                speakers[spk] = [dict(r) for r in sample]

            conn.close()
            return {"speakers": speakers, "speaker_counts": speaker_counts}
        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def cluster_by_category(self) -> Dict:
        """Group evidence by evidence_category column."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        try:
            rows = conn.execute(
                "SELECT evidence_category, COUNT(*) as cnt "
                "FROM evidence_quotes "
                "WHERE evidence_category IS NOT NULL AND evidence_category != '' "
                "GROUP BY evidence_category ORDER BY cnt DESC"
            ).fetchall()
            categories = {r["evidence_category"]: r["cnt"] for r in rows}

            # Sample from top categories
            samples: Dict[str, List[Dict]] = {}
            for cat in list(categories.keys())[:10]:
                sample = conn.execute(
                    "SELECT id, substr(quote_text, 1, 300) as quote_text, "
                    "speaker, date_ref "
                    "FROM evidence_quotes WHERE evidence_category = ? LIMIT 20",
                    (cat,),
                ).fetchall()
                samples[cat] = [dict(r) for r in sample]

            conn.close()
            return {
                "total_categories": len(categories),
                "category_counts": categories,
                "samples": samples,
            }
        except Exception as e:
            conn.close()
            return {"error": str(e)}

    # ── Chain Building & Search ───────────────────────────────────────

    def build_evidence_chain(self, topic: str) -> List[Dict]:
        """Build sequential evidence chain for a topic, ordered by date."""
        conn = _get_db()
        if not conn:
            return []

        try:
            # FTS first
            chain = []
            try:
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 400) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance "
                    "FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ?) "
                    "AND date_ref IS NOT NULL AND date_ref != '' "
                    "ORDER BY date_ref ASC LIMIT 100",
                    (topic,),
                ).fetchall()
                chain = [dict(r) for r in rows]
            except Exception:
                # LIKE fallback
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 400) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance "
                    "FROM evidence_quotes "
                    "WHERE quote_text LIKE ? "
                    "AND date_ref IS NOT NULL AND date_ref != '' "
                    "ORDER BY date_ref ASC LIMIT 100",
                    (f"%{topic}%",),
                ).fetchall()
                chain = [dict(r) for r in rows]

            conn.close()
            return chain
        except Exception:
            conn.close()
            return []

    def get_strongest_evidence(self, topic: str, limit: int = 20) -> List[Dict]:
        """Highest-relevance evidence for topic using FTS ranking."""
        conn = _get_db()
        if not conn:
            return []

        try:
            # Use FTS5 rank for relevance scoring
            rows = []
            try:
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 500) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance, "
                    "rank "
                    "FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ? "
                    " ORDER BY rank LIMIT ?)",
                    (topic, limit),
                ).fetchall()
            except Exception:
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 500) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance "
                    "FROM evidence_quotes WHERE quote_text LIKE ? LIMIT ?",
                    (f"%{topic}%", limit),
                ).fetchall()

            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def search_evidence(self, query: str, limit: int = 50) -> List[Dict]:
        """FTS5 search across evidence_quotes_fts."""
        conn = _get_db()
        if not conn:
            return []

        try:
            try:
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 500) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance "
                    "FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ?) LIMIT ?",
                    (query, limit),
                ).fetchall()
            except Exception:
                rows = conn.execute(
                    "SELECT id, substr(quote_text, 1, 500) as quote_text, "
                    "speaker, date_ref, evidence_category, legal_significance "
                    "FROM evidence_quotes WHERE quote_text LIKE ? LIMIT ?",
                    (f"%{query}%", limit),
                ).fetchall()

            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    # ── Supplemental Sources ──────────────────────────────────────────

    def get_drive_evidence(self, limit: int = 50) -> List[Dict]:
        """Query drive_evidence (30,373 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT id, file_path, file_type, relevance_score, "
                "substr(keyword_hits, 1, 200) as keyword_hits, "
                "substr(extracted_facts, 1, 300) as extracted_facts, "
                "case_lane, file_modified "
                "FROM drive_evidence "
                "ORDER BY relevance_score DESC LIMIT ?",
                (limit,),
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    def get_watson_evidence(self, limit: int = 50) -> List[Dict]:
        """Query watsons_evidence_docs (299 rows)."""
        conn = _get_db()
        if not conn:
            return []

        try:
            rows = conn.execute(
                "SELECT id, filename, substr(content, 1, 400) as content, "
                "file_size, ingested_at "
                "FROM watsons_evidence_docs "
                "ORDER BY ingested_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            result = [dict(r) for r in rows]
            conn.close()
            return result
        except Exception:
            conn.close()
            return []

    # ── Statistics ────────────────────────────────────────────────────

    def get_statistics(self) -> Dict:
        """Counts by theme, category, speaker."""
        conn = _get_db()
        if not conn:
            return {"error": "DB connection failed"}

        stats: Dict = {}
        try:
            stats["evidence_quotes_total"] = conn.execute(
                "SELECT COUNT(*) FROM evidence_quotes"
            ).fetchone()[0]
            stats["drive_evidence_total"] = conn.execute(
                "SELECT COUNT(*) FROM drive_evidence"
            ).fetchone()[0]
            stats["watson_evidence_total"] = conn.execute(
                "SELECT COUNT(*) FROM watsons_evidence_docs"
            ).fetchone()[0]

            # Top categories
            rows = conn.execute(
                "SELECT evidence_category, COUNT(*) as cnt "
                "FROM evidence_quotes "
                "WHERE evidence_category IS NOT NULL AND evidence_category != '' "
                "GROUP BY evidence_category ORDER BY cnt DESC LIMIT 15"
            ).fetchall()
            stats["top_categories"] = {r["evidence_category"]: r["cnt"] for r in rows}

            # Top speakers
            rows = conn.execute(
                "SELECT speaker, COUNT(*) as cnt "
                "FROM evidence_quotes "
                "WHERE speaker IS NOT NULL AND speaker != '' "
                "GROUP BY speaker ORDER BY cnt DESC LIMIT 15"
            ).fetchall()
            stats["top_speakers"] = {r["speaker"]: r["cnt"] for r in rows}

            # Drive evidence by case lane
            rows = conn.execute(
                "SELECT case_lane, COUNT(*) as cnt "
                "FROM drive_evidence "
                "WHERE case_lane IS NOT NULL AND case_lane != '' "
                "GROUP BY case_lane ORDER BY cnt DESC"
            ).fetchall()
            stats["drive_by_lane"] = {r["case_lane"]: r["cnt"] for r in rows}

            conn.close()
        except Exception as e:
            stats["error"] = str(e)

        return stats


def self_test() -> Dict:
    """Verify skill connectivity and data availability."""
    results = {"skill": "evidence_clusterer", "timestamp": datetime.now().isoformat()}
    conn = _get_db()
    if not conn:
        results["status"] = "FAIL"
        results["error"] = "DB connection failed"
        return results

    checks = {}
    for table in ["evidence_quotes", "drive_evidence", "watsons_evidence_docs"]:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            checks[table] = {"status": "OK", "rows": count}
        except Exception as e:
            checks[table] = {"status": "FAIL", "error": str(e)}

    # FTS check
    try:
        conn.execute(
            "SELECT rowid FROM evidence_quotes_fts "
            "WHERE evidence_quotes_fts MATCH 'custody' LIMIT 1"
        ).fetchone()
        checks["evidence_quotes_fts"] = {"status": "OK"}
    except Exception as e:
        checks["evidence_quotes_fts"] = {"status": "FAIL", "error": str(e)}

    conn.close()
    results["checks"] = checks
    results["status"] = (
        "OK" if all(c["status"] == "OK" for c in checks.values()) else "DEGRADED"
    )
    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    clusterer = EvidenceClusterer()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "theme":
            themes = sys.argv[2].split(",") if len(sys.argv) > 2 else None
            cycle_json(clusterer.cluster_by_theme(themes=themes))
        elif cmd == "ground":
            grounds = sys.argv[2].split(",") if len(sys.argv) > 2 else None
            cycle_json(clusterer.cluster_by_ground(grounds=grounds))
        elif cmd == "witness":
            speaker = sys.argv[2] if len(sys.argv) > 2 else None
            cycle_json(clusterer.cluster_by_witness(speaker=speaker))
        elif cmd == "category":
            cycle_json(clusterer.cluster_by_category())
        elif cmd == "chain":
            topic = sys.argv[2] if len(sys.argv) > 2 else "custody"
            cycle_json(clusterer.build_evidence_chain(topic))
        elif cmd == "strongest":
            topic = sys.argv[2] if len(sys.argv) > 2 else "custody"
            cycle_json(clusterer.get_strongest_evidence(topic))
        elif cmd == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "alienation"
            cycle_json(clusterer.search_evidence(query))
        elif cmd == "drive":
            cycle_json(clusterer.get_drive_evidence())
        elif cmd == "watson":
            cycle_json(clusterer.get_watson_evidence())
        elif cmd == "stats":
            cycle_json(clusterer.get_statistics())
        elif cmd == "self_test":
            cycle_json(self_test())
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Evidence Clusterer Skill")
        print("Usage: python evidence_clusterer.py <command> [args]")
        print("Commands: theme, ground, witness, category, chain, strongest, search, drive, watson, stats, self_test")
