#!/usr/bin/env python3
"""
+======================================================================+
|                     N E X U S   E N G I N E                          |
|              Litigation Fusion Reactor  v1.0                         |
|                                                                      |
|  The first multi-case autonomous litigation reasoning engine.        |
|  Fuses ALL 186 tables across 5+ case types into unified intelligence.|
+======================================================================+

Actions (via stdin JSON):
  fuse        Cross-table evidence search (5+ tables simultaneously)
  case_map    Multi-standard analysis (custody/housing/judicial/criminal/federal)
  credibility Per-person credibility destruction matrix
  readiness   Filing readiness with gap analysis (10+ lanes)
  priorities  Daily action plan (deadlines x readiness)
  argue       Argument chain synthesis (evidence -> authority -> impeachment)
  impeach     Complete impeachment package per person/entity
  damages     Aggregate damages across all claims

Usage:
  echo {"action":"priorities"} | python nexus_engine.py
  echo {"action":"fuse","topic":"alienation","limit":20} | python nexus_engine.py
  echo {"action":"case_map","case_type":"custody"} | python nexus_engine.py
  echo {"action":"credibility","person":"Emily Watson"} | python nexus_engine.py
"""

import logging
import sqlite3
import json
import sys
import os
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)

# Prefer shared module for DB connections; fall back to hardcoded path
try:
    _system_dir = str(Path(__file__).resolve().parent.parent.parent)
    if _system_dir not in sys.path:
        sys.path.insert(0, _system_dir)
    from shared import get_db as _shared_get_db, sanitize_fts5, safe_fts5_search, expand_query
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

DB_PATH = os.environ.get(
    "NEXUS_DB_PATH",
    str(Path(__file__).resolve().parents[3] / "litigation_context.db")
)

if not _HAS_SHARED:
    import re

if not _HAS_SHARED:
    # Fallback: local sanitize_fts5 if shared module not available
    def sanitize_fts5(query):
        """Sanitize a query string for safe FTS5 MATCH usage.
        Strips characters that break FTS5 (periods, colons, hyphens in citations)
        and wraps multi-word terms properly.
        """
        if not query:
            return ""
        import re as _re
        phrases = _re.findall(r'"[^"]*"', query)
        remainder = _re.sub(r'"[^"]*"', '', query)
        ops = {"AND", "OR", "NOT"}
        remainder = _re.sub(r'[\.:\(\)§\[\]\{\}]', ' ', remainder)
        remainder = _re.sub(r'\s+', ' ', remainder).strip()
        tokens = []
        for t in remainder.split():
            if t.upper() in ops:
                tokens.append(t.upper())
            elif len(t) >= 2:
                tokens.append(t)
        parts = phrases + tokens
        return " ".join(parts) if parts else query
# If _HAS_SHARED, sanitize_fts5 is already imported from shared

# ====================================================================
# CASE PROFILES - Legal frameworks for each case type
# ====================================================================

CUSTODY_FACTORS = {
    "a": {"name": "Love, Affection & Emotional Ties",
           "statute": "MCL 722.23(a)",
           "fts": "love OR affection OR bond OR emotional ties"},
    "b": {"name": "Capacity for Guidance & Education",
           "statute": "MCL 722.23(b)",
           "fts": "guidance OR education OR school OR upbringing"},
    "c": {"name": "Material Needs Capacity",
           "statute": "MCL 722.23(c)",
           "fts": "food OR clothing OR medical OR material needs"},
    "d": {"name": "Stable Environment",
           "statute": "MCL 722.23(d)",
           "fts": "stable OR environment OR continuity OR residence"},
    "e": {"name": "Permanence of Family Unit",
           "statute": "MCL 722.23(e)",
           "fts": "permanence OR family unit OR custodial home"},
    "f": {"name": "Moral Fitness",
           "statute": "MCL 722.23(f)",
           "fts": "moral fitness OR criminal OR fraud OR perjury"},
    "g": {"name": "Mental & Physical Health",
           "statute": "MCL 722.23(g)",
           "fts": "mental health OR physical health OR therapy"},
    "h": {"name": "Home, School & Community Record",
           "statute": "MCL 722.23(h)",
           "fts": "school OR community OR attendance OR activities"},
    "i": {"name": "Child Preference",
           "statute": "MCL 722.23(i)",
           "fts": "preference OR child wishes OR child wants"},
    "j": {"name": "Willingness to Facilitate Relationship",
           "statute": "MCL 722.23(j)",
           "fts": "alienation OR facilitate OR cooperation OR deny OR withhold"},
    "k": {"name": "Domestic Violence",
           "statute": "MCL 722.23(k)",
           "fts": "domestic violence OR abuse OR assault OR PPO"},
    "l": {"name": "Other Relevant Factors",
           "statute": "MCL 722.23(l)",
           "fts": "judicial bias OR misconduct OR due process OR conspiracy"},
}

HOUSING_STANDARDS = {
    "lease": {"name": "Lease Agreement Violations",
              "statutes": ["MCL 125.2322", "MCL 554.631"],
              "fts": "lease OR agreement OR rent terms OR violation"},
    "eviction": {"name": "Wrongful Eviction / Retaliation",
                 "statutes": ["MCL 125.2328", "MCL 600.5720", "MCL 600.5714"],
                 "fts": "eviction OR retaliation OR wrongful OR retaliatory"},
    "rent": {"name": "Rent Increase / Overcharge",
             "statutes": ["MCL 125.2332", "MCL 125.2322(1)"],
             "fts": "rent increase OR overcharge OR ledger OR manipulation"},
    "habitability": {"name": "Habitability / Property Conditions",
                     "statutes": ["MCL 125.2307", "MCL 125.471", "MCL 125.535"],
                     "fts": "sewer OR utility OR shutoff OR repair OR habitability"},
    "deposit": {"name": "Security Deposit Violations",
                "statutes": ["MCL 554.601", "MCL 554.602", "MCL 554.603"],
                "fts": "security deposit OR itemized OR return deposit"},
    "corporate": {"name": "Corporate Structure Fraud",
                  "statutes": ["MCL 450.4101", "MCL 600.2919"],
                  "fts": "dissolved OR corporate OR veil OR alter ego OR successor"},
    "mhca": {"name": "Mobile Home Commission Act",
             "statutes": ["MCL 125.2301", "MCL 125.2344", "MCL 125.2307(1)"],
             "fts": "mobile home OR manufactured OR commission OR MHCA"},
    "utility": {"name": "Utility Shutoff / Essential Services",
                "statutes": ["MCL 125.534", "MCL 125.535", "MCL 125.474"],
                "fts": "utility OR shutoff OR water OR sewer OR electric"},
}

JUDICIAL_STANDARDS = {
    "impartiality": {"name": "Impartiality Requirement",
                     "canons": ["Canon 1", "Canon 2", "Canon 3"],
                     "rules": ["MCR 2.003(C)(1)"],
                     "fts": "impartial OR bias OR prejudice OR appearance"},
    "conflict": {"name": "Conflict of Interest / Recusal",
                 "canons": ["Canon 2", "Canon 3"],
                 "rules": ["MCR 2.003(C)(1)(g)"],
                 "fts": "conflict OR recusal OR disqualification OR Berry"},
    "due_process": {"name": "Due Process Violations",
                    "canons": ["Canon 3"],
                    "rules": ["MCR 2.003", "MCR 3.210"],
                    "fts": "due process OR ex parte OR notice OR hearing"},
    "abuse": {"name": "Abuse of Discretion",
              "canons": ["Canon 3"],
              "rules": ["MCR 2.003"],
              "fts": "abuse discretion OR arbitrary OR capricious OR unreasonable"},
    "conduct": {"name": "Professional Conduct",
                "canons": ["Canon 1", "Canon 4", "Canon 5"],
                "rules": ["MCR 9.104"],
                "fts": "misconduct OR professional OR integrity OR discipline"},
}

CRIMINAL_ELEMENTS = {
    "self_defense": {"name": "Self-Defense (SYG)",
                     "statutes": ["MCL 780.972", "MCL 780.974"],
                     "fts": "self defense OR reasonable force OR imminent threat"},
    "discovery": {"name": "Discovery Rights",
                  "rules": ["MCR 6.201", "MCR 6.202"],
                  "fts": "discovery OR disclosure OR witness list OR evidence"},
    "brady": {"name": "Brady Material",
              "authorities": ["Brady v. Maryland, 373 U.S. 83"],
              "fts": "Brady OR exculpatory OR suppress OR withhold evidence"},
}

FEDERAL_ELEMENTS = {
    "section_1983": {"name": "Deprivation Under Color of Law",
                     "statutes": ["42 U.S.C. 1983"],
                     "fts": "deprivation OR rights OR color of law OR state action"},
    "proc_due_process": {"name": "Procedural Due Process",
                         "amendments": ["14th Amendment"],
                         "fts": "procedural due process OR notice OR hearing OR liberty"},
    "subst_due_process": {"name": "Substantive Due Process - Parental Rights",
                          "cases": ["Troxel v. Granville, 530 U.S. 57"],
                          "fts": "fundamental right OR parental OR Troxel OR substantive"},
}

APPELLATE_ELEMENTS = {
    "abuse_discretion": {"name": "Abuse of Discretion Review",
                         "fts": "abuse discretion OR custody decision OR standard review"},
    "de_novo": {"name": "De Novo Review",
                "fts": "de novo OR constitutional OR legal question"},
    "clear_error": {"name": "Clear Error Review",
                    "fts": "clear error OR factual findings OR weight evidence"},
    "preserved": {"name": "Preserved Errors",
                  "fts": "objection OR preserved OR motion reconsider"},
}

PPO_ELEMENTS = {
    "dissolution": {"name": "PPO Dissolution",
                    "statutes": ["MCL 600.2950", "MCL 600.2950a"],
                    "fts": "PPO OR protection order OR terminate OR dissolve"},
    "weaponization": {"name": "PPO Weaponization",
                      "fts": "weaponize OR false PPO OR retaliation OR custody leverage"},
    "violations": {"name": "Respondent PPO Violations by Petitioner",
                   "fts": "third party OR harassment OR contact OR violat"},
}

CORPORATE_CHAINS = {
    "shady_oaks": {
        "name": "Shady Oaks Corporate Chain",
        "entities": [
            {"name": "Shady Oaks MHP LLC", "status": "dissolved", "role": "property manager"},
            {"name": "Shady Oaks Park MHP LLC", "status": "dissolved", "role": "property owner"},
            {"name": "Homes of America LLC", "status": "active", "role": "parent company"},
            {"name": "Partridge Equities LLC", "status": "active", "role": "investment vehicle"},
            {"name": "Partridge Securities LLC", "status": "active", "role": "securities entity"},
            {"name": "Alden Global Capital", "status": "active", "role": "ultimate owner"},
        ],
    }
}

CASE_PROFILES = {
    "custody": {
        "name": "Pigors v Watson - Custody Modification",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court, Muskegon County",
        "lanes": ["A", "D", "E"],
        "filings": ["F1", "F7", "F3"],
        "standards": CUSTODY_FACTORS,
    },
    "housing": {
        "name": "Pigors v Shady Oaks - Housing/Corporate Fraud",
        "case_number": "2025-002760-CZ",
        "court": "14th Circuit Court, Muskegon County",
        "lanes": ["B"],
        "filings": ["F2"],
        "standards": HOUSING_STANDARDS,
    },
    "judicial": {
        "name": "Judicial Misconduct - McNeill Disqualification/JTC",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit / JTC / MSC",
        "lanes": ["A", "E"],
        "filings": ["F3", "F5", "F6"],
        "standards": JUDICIAL_STANDARDS,
    },
    "criminal": {
        "name": "People v Pigors - Criminal Defense",
        "case_number": "2025-25245676SM",
        "court": "60th District Court",
        "lanes": ["CRIMINAL"],
        "filings": ["CRIMINAL"],
        "standards": CRIMINAL_ELEMENTS,
    },
    "federal": {
        "name": "Pigors v McNeill et al - Federal Civil Rights",
        "case_number": "TBD",
        "court": "W.D. Michigan",
        "lanes": ["A"],
        "filings": ["F4"],
        "standards": FEDERAL_ELEMENTS,
    },
    "ppo": {
        "name": "PPO Termination - Watson PPO",
        "case_number": "2023-5907-PP",
        "court": "14th Circuit Court",
        "lanes": ["A"],
        "filings": ["F8"],
        "standards": PPO_ELEMENTS,
    },
    "appellate": {
        "name": "COA Appeal 366810",
        "case_number": "366810",
        "court": "Michigan Court of Appeals",
        "lanes": ["F"],
        "filings": ["F9", "F10"],
        "standards": APPELLATE_ELEMENTS,
    },
}

LANE_MAP = {
    "F1": "Emergency TRO / Custody",
    "F2": "Shady Oaks Housing Complaint",
    "F3": "McNeill Disqualification (MCR 2.003)",
    "F4": "Federal 1983 Complaint",
    "F5": "MSC Original Action",
    "F6": "JTC Complaint",
    "F7": "Custody Modification",
    "F8": "PPO Termination",
    "F9": "COA Brief on Appeal",
    "F10": "COA Emergency Motion",
    "CRIMINAL": "Criminal Defense",
}


# ====================================================================
# NEXUS ENGINE
# ====================================================================

class NexusEngine:
    """Multi-case autonomous litigation reasoning engine."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._conn = None
        self._cache = {}          # Session-scoped query cache
        self._cache_ts = {}       # Cache timestamps for TTL

    @property
    def conn(self):
        if self._conn is None:
            if _HAS_SHARED and self.db_path == DB_PATH:
                # Use shared module — gets standard PRAGMAs automatically
                self._conn = _shared_get_db("litigation", readonly=True)
            else:
                # Fallback: direct connection (custom db_path or shared unavailable)
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA busy_timeout=60000")
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA cache_size=-32000")
                self._conn.execute("PRAGMA query_only=ON")
        return self._conn

    def _q(self, sql, params=()):
        """Execute query, return list of dicts. Auto-falls back to LIKE on FTS5 failure."""
        try:
            rows = self.conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            err_str = str(e).lower()
            # Detect FTS5 failures and attempt LIKE fallback
            if "fts5" in err_str or "match" in err_str or "syntax error" in err_str:
                try:
                    return self._fts5_like_fallback(sql, params)
                except Exception:
                    pass
            return [{"error": str(e), "sql": sql[:200]}]

    def _q_cached(self, sql, params=(), ttl=300):
        """Execute query with session-scoped TTL cache for read-only reference data."""
        import time
        cache_key = f"{sql}|{str(params)}"
        now = time.time()
        if cache_key in self._cache and (now - self._cache_ts.get(cache_key, 0)) < ttl:
            return self._cache[cache_key]
        result = self._q(sql, params)
        self._cache[cache_key] = result
        self._cache_ts[cache_key] = now
        return result

    def _fts5_like_fallback(self, fts_sql, params):
        """Convert a failed FTS5 MATCH query to a LIKE query.

        Extracts the search term from params and rewrites the WHERE clause.
        """
        import re as _re
        # The first param is typically the FTS5 search term
        search_term = str(params[0]) if params else ""
        if not search_term:
            return []

        # Extract base table from JOIN clause if present
        join_match = _re.search(r'JOIN\s+(\w+)\s+\w+\s+ON', fts_sql, _re.IGNORECASE)
        if join_match:
            base_table = join_match.group(1)
            # Get the text columns from the base table
            cols = [r[1] for r in self.conn.execute(f"PRAGMA table_info([{base_table}])").fetchall()
                    if r[2].upper() in ("TEXT", "")]
            if cols:
                # Build LIKE query against first text column
                terms = _re.sub(r'[^\w\s]', ' ', search_term).split()
                terms = [t for t in terms if len(t) >= 2 and t.upper() not in {"AND", "OR", "NOT"}]
                if not terms:
                    return []
                like_clauses = " AND ".join([f"[{cols[0]}] LIKE ?" for _ in terms])
                like_params = [f"%{t}%" for t in terms]
                remaining_params = list(params[1:])
                fallback_sql = f"SELECT * FROM [{base_table}] WHERE {like_clauses} LIMIT ?"
                # Last param is usually LIMIT
                limit_val = remaining_params[-1] if remaining_params and isinstance(remaining_params[-1], int) else 25
                rows = self.conn.execute(fallback_sql, like_params + [limit_val]).fetchall()
                return [dict(r) for r in rows]
        return []

    def _scalar(self, sql, params=()):
        """Return single value."""
        try:
            row = self.conn.execute(sql, params).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    # ----------------------------------------------------------------
    # FUSE - Cross-table evidence fusion
    # ----------------------------------------------------------------
    def fuse(self, topic, lanes=None, limit=50):
        """Search ALL evidence tables simultaneously for a topic.

        Returns fused results from: evidence_fts, timeline_fts,
        police_reports, impeachment_matrix, authority_chains_v2.
        """
        results = {"topic": topic, "lanes": lanes, "sources": {}}
        safe_topic = sanitize_fts5(topic)

        # 1. Evidence quotes (FTS5)
        lane_clause = ""
        params = []
        if lanes:
            placeholders = ",".join("?" * len(lanes))
            lane_clause = " AND eq.lane IN ({})".format(placeholders)
            params = list(lanes)

        evidence_sql = """
            WITH matched AS (
                SELECT rowid, rank
                FROM evidence_fts
                WHERE evidence_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            )
            SELECT eq.id, eq.source_file, eq.category, eq.lane,
                   eq.relevance_score,
                   snippet(evidence_fts, 0, '>>>', '<<<', '...', 40) AS excerpt
            FROM evidence_fts
            JOIN matched ON evidence_fts.rowid = matched.rowid
            JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
            {}
            ORDER BY matched.rank
        """.format(lane_clause)
        evidence = self._q(evidence_sql, [safe_topic, limit] + params)
        results["sources"]["evidence_quotes"] = {
            "count": len(evidence),
            "items": evidence,
        }

        # 2. Timeline events (FTS5) — CTE to avoid snippet() on all rows before LIMIT
        timeline_sql = """
            WITH matched AS (
                SELECT rowid, rank
                FROM timeline_fts
                WHERE timeline_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            )
            SELECT te.id, te.event_date, te.lane, te.category, te.severity,
                   snippet(timeline_fts, 0, '>>>', '<<<', '...', 40) AS excerpt
            FROM timeline_fts
            JOIN matched ON timeline_fts.rowid = matched.rowid
            JOIN timeline_events te ON timeline_fts.rowid = te.id
            ORDER BY matched.rank
        """
        timeline = self._q(timeline_sql, [safe_topic, limit])
        results["sources"]["timeline_events"] = {
            "count": len(timeline),
            "items": timeline,
        }

        # 3. Police reports (LIKE search)
        police_sql = """
            SELECT id, filename, officers, allegations,
                   exculpatory, key_quotes
            FROM police_reports
            WHERE full_text LIKE ?
            LIMIT ?
        """
        police = self._q(police_sql, ["%" + topic + "%", limit])
        results["sources"]["police_reports"] = {
            "count": len(police),
            "items": police,
        }

        # 4. Impeachment matrix
        imp_sql = """
            SELECT id, category, evidence_summary,
                   impeachment_value, cross_exam_question, filing_relevance
            FROM impeachment_matrix
            WHERE evidence_summary LIKE ? OR cross_exam_question LIKE ?
            ORDER BY impeachment_value DESC
            LIMIT ?
        """
        imp = self._q(imp_sql, ["%" + topic + "%", "%" + topic + "%", limit])
        results["sources"]["impeachment"] = {
            "count": len(imp),
            "items": imp,
        }

        # 5. Authority chains
        auth_sql = """
            SELECT id, primary_citation, supporting_citation,
                   relationship, lane
            FROM authority_chains_v2
            WHERE primary_citation LIKE ? OR paragraph_context LIKE ?
            LIMIT ?
        """
        auth = self._q(auth_sql, ["%" + topic + "%", "%" + topic + "%", limit])
        results["sources"]["authorities"] = {
            "count": len(auth),
            "items": auth,
        }

        # Total fusion count
        results["total_fused"] = sum(
            s["count"] for s in results["sources"].values()
        )
        return results

    # ----------------------------------------------------------------
    # CASE_MAP - Multi-standard analysis per case type
    # ----------------------------------------------------------------
    def case_map(self, case_type):
        """Analyze a case against its legal standards."""
        if case_type not in CASE_PROFILES:
            return {"error": "Unknown case type: " + case_type,
                    "valid": list(CASE_PROFILES.keys())}

        profile = CASE_PROFILES[case_type]
        result = {
            "case_type": case_type,
            "name": profile["name"],
            "case_number": profile["case_number"],
            "court": profile["court"],
            "lanes": profile["lanes"],
            "filings": profile["filings"],
            "standards": {},
        }

        if case_type == "custody":
            return self._case_map_custody(result, profile)
        elif case_type == "judicial":
            return self._case_map_judicial(result, profile)
        elif case_type == "housing":
            return self._case_map_housing(result, profile)
        else:
            return self._case_map_generic(result, profile)

    def _case_map_custody(self, result, profile):
        """Custody analysis using pre-computed best_interest tables."""
        summary = self._q("""
            SELECT factor_letter, factor_name, mcl_section,
                   andrew_score, emily_score, net_score,
                   evidence_count, strongest_evidence_text,
                   key_citations, assessment
            FROM best_interest_summary
            ORDER BY factor_letter
        """)

        for row in summary:
            fl = row.get("factor_letter", "?")
            result["standards"][fl] = {
                "name": row.get("factor_name", ""),
                "statute": row.get("mcl_section", ""),
                "andrew_score": row.get("andrew_score", 0),
                "emily_score": row.get("emily_score", 0),
                "net_score": row.get("net_score", 0),
                "evidence_count": row.get("evidence_count", 0),
                "strongest_evidence": row.get("strongest_evidence_text", ""),
                "citations": row.get("key_citations", ""),
                "assessment": row.get("assessment", ""),
            }

        andrew_total = sum(r.get("andrew_score", 0) for r in summary)
        emily_total = sum(r.get("emily_score", 0) for r in summary)
        result["aggregate"] = {
            "andrew_total": andrew_total,
            "emily_total": emily_total,
            "advantage": "Andrew" if andrew_total > emily_total else "Emily",
            "margin": abs(andrew_total - emily_total),
            "total_evidence": self._scalar(
                "SELECT COUNT(*) FROM best_interest_factor_map"
            ),
        }

        result["alienation_events"] = self._scalar(
            "SELECT COUNT(*) FROM alienation_timeline"
        )
        result["separation_days"] = (date.today() - date(2025, 8, 8)).days

        return result

    def _case_map_judicial(self, result, profile):
        """Judicial misconduct analysis."""
        result["total_violations"] = self._scalar(
            "SELECT COUNT(*) FROM judicial_violations"
        )
        result["bias_events"] = self._scalar(
            "SELECT COUNT(*) FROM judicial_bias_chronology"
        )
        result["audit_entries"] = self._scalar(
            "SELECT COUNT(*) FROM judicial_audit"
        )

        berry = self._q_cached("SELECT * FROM berry_mcneill_intelligence LIMIT 20", ttl=600)
        result["berry_mcneill"] = {"count": len(berry), "items": berry}

        canons = self._q_cached("SELECT * FROM michigan_judicial_canons", ttl=600)
        result["canons"] = canons

        for key, std in profile["standards"].items():
            evidence_count = self._scalar("""
                SELECT COUNT(*) FROM evidence_quotes
                WHERE (category LIKE '%judicial%' OR category LIKE '%misconduct%'
                       OR category LIKE '%bias%')
                AND lane IN ('A','E')
            """)
            auth_count = self._scalar("""
                SELECT COUNT(*) FROM authority_chains_v2
                WHERE primary_citation LIKE '%MCR 2.003%'
            """)
            result["standards"][key] = {
                "name": std["name"],
                "canons": std.get("canons", []),
                "rules": std.get("rules", []),
                "evidence_count": evidence_count,
                "authority_count": auth_count,
            }

        return result

    def _case_map_housing(self, result, profile):
        """Housing case analysis with corporate chain tracking."""
        result["total_evidence"] = self._scalar(
            "SELECT COUNT(*) FROM evidence_quotes WHERE lane = 'B'"
        )
        result["corporate_chain"] = CORPORATE_CHAINS.get("shady_oaks", {})

        for key, std in profile["standards"].items():
            fts_term = std["fts"]
            ev_count = 0
            try:
                ev_count = self._scalar("""
                    SELECT COUNT(*) FROM evidence_fts
                    JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                    WHERE evidence_fts MATCH ? AND eq.lane = 'B'
                """, [fts_term])
            except Exception:
                ev_count = 0

            statutes = std.get("statutes", [])
            if statutes:
                placeholders = " OR ".join(["primary_citation LIKE ?"] * len(statutes))
                auth_count = self._scalar(
                    f"SELECT COUNT(*) FROM authority_chains_v2 WHERE {placeholders}",
                    ["%" + s + "%" for s in statutes]
                )
            else:
                auth_count = 0

            samples = []
            try:
                samples = self._q("""
                    SELECT eq.id, eq.source_file, eq.relevance_score,
                           snippet(evidence_fts, 0, '>>>', '<<<', '...', 30) AS excerpt
                    FROM evidence_fts
                    JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                    WHERE evidence_fts MATCH ? AND eq.lane = 'B'
                    ORDER BY rank LIMIT 3
                """, [fts_term])
            except Exception as e:
                logger.warning("FTS5 housing samples query failed for %r: %s", fts_term, e)
                samples = [{"error": f"FTS5 query failed: {e}", "fts_term": fts_term}]

            result["standards"][key] = {
                "name": std["name"],
                "statutes": std.get("statutes", []),
                "evidence_count": ev_count,
                "authority_count": auth_count,
                "top_evidence": samples,
            }

        damages = self._q("""
            SELECT category, description,
                   conservative_amount, aggressive_amount, basis
            FROM damages_calculation
            WHERE lane = 'B' OR lane LIKE '%housing%'
        """)
        result["damages"] = damages

        return result

    def _case_map_generic(self, result, profile):
        """Generic analysis for criminal/federal/ppo/appellate."""
        for key, std in profile["standards"].items():
            fts_term = std.get("fts", key)
            ev_count = 0
            try:
                ev_count = self._scalar("""
                    SELECT COUNT(*) FROM evidence_fts
                    JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                    WHERE evidence_fts MATCH ?
                """, [fts_term])
            except Exception as e:
                logger.warning("FTS5 count query failed for %r: %s", fts_term, e)

            samples = []
            try:
                samples = self._q("""
                    SELECT eq.id, eq.source_file, eq.category, eq.lane,
                           snippet(evidence_fts, 0, '>>>', '<<<', '...', 30) AS excerpt
                    FROM evidence_fts
                    JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                    WHERE evidence_fts MATCH ?
                    ORDER BY rank LIMIT 3
                """, [fts_term])
            except Exception as e:
                logger.warning("FTS5 generic samples query failed for %r: %s", fts_term, e)
                samples = [{"error": f"FTS5 query failed: {e}", "fts_term": fts_term}]

            result["standards"][key] = {
                "name": std["name"],
                "statutes": std.get("statutes", []),
                "rules": std.get("rules", []),
                "evidence_count": ev_count,
                "top_evidence": samples,
            }

        return result

    # ----------------------------------------------------------------
    # CREDIBILITY - Per-person credibility destruction matrix
    # ----------------------------------------------------------------
    def credibility(self, person, limit=25):
        """Aggregate credibility problems for a person/entity."""
        result = {
            "person": person,
            "sources": {},
            "total_items": 0,
            "credibility_score": 100,
        }
        like = "%" + person + "%"

        # 1. Impeachment matrix
        imp = self._q("""
            SELECT id, category, evidence_summary, impeachment_value,
                   cross_exam_question, filing_relevance, event_date
            FROM impeachment_matrix
            WHERE evidence_summary LIKE ? OR cross_exam_question LIKE ?
            ORDER BY impeachment_value DESC
            LIMIT ?
        """, [like, like, limit])
        result["sources"]["impeachment"] = {"count": len(imp), "items": imp}

        # 2. False allegations
        false_allege = self._q("""
            SELECT * FROM false_allegations
            WHERE allegation LIKE ? OR alleged_by LIKE ?
            LIMIT ?
        """, [like, like, limit])
        result["sources"]["false_allegations"] = {
            "count": len(false_allege), "items": false_allege
        }

        # 3. Police reports
        police = self._q("""
            SELECT id, filename, officers, allegations,
                   exculpatory, false_reports, key_quotes
            FROM police_reports WHERE full_text LIKE ? LIMIT ?
        """, [like, limit])
        result["sources"]["police_reports"] = {
            "count": len(police), "items": police
        }

        # 4. Contradictions
        contras = self._q("""
            SELECT claim_id, source_a, source_b,
                   contradiction_text, severity
            FROM contradiction_map
            WHERE source_a LIKE ? OR source_b LIKE ?
                  OR contradiction_text LIKE ?
            ORDER BY severity DESC LIMIT ?
        """, [like, like, like, limit])
        result["sources"]["contradictions"] = {
            "count": len(contras), "items": contras
        }

        # 5. Credibility-tagged evidence
        cred_ev = self._q("""
            SELECT id, source_file, quote_text, category, relevance_score
            FROM evidence_quotes
            WHERE (category LIKE '%credib%' OR category LIKE '%false%'
                   OR category LIKE '%impeach%')
            AND quote_text LIKE ?
            ORDER BY relevance_score DESC LIMIT ?
        """, [like, limit])
        result["sources"]["evidence"] = {
            "count": len(cred_ev), "items": cred_ev
        }

        # Calculate credibility score
        total = sum(s["count"] for s in result["sources"].values())
        result["total_items"] = total

        for item in imp:
            val = item.get("impeachment_value", 0) or 0
            result["credibility_score"] -= val * 2
        result["credibility_score"] -= len(false_allege) * 10
        result["credibility_score"] -= len(contras) * 5
        result["credibility_score"] = max(0, result["credibility_score"])

        score = result["credibility_score"]
        if score >= 80:
            result["rating"] = "HIGH CREDIBILITY"
        elif score >= 50:
            result["rating"] = "DAMAGED CREDIBILITY"
        elif score >= 20:
            result["rating"] = "SEVERELY DAMAGED"
        else:
            result["rating"] = "DESTROYED - ZERO CREDIBILITY"

        return result

    # ----------------------------------------------------------------
    # READINESS - Filing readiness with gap analysis
    # ----------------------------------------------------------------
    def readiness(self, lane=None):
        """Filing readiness dashboard across all 10+ lanes."""
        result = {"lanes": {}, "summary": {}}

        pkg_sql = "SELECT * FROM filing_packages"
        params = []
        if lane:
            pkg_sql += " WHERE lane = ?"
            params = [lane]
        packages = self._q(pkg_sql, params)

        deadlines = self._q_cached("SELECT * FROM deadlines ORDER BY due_date", ttl=120)
        readiness_rows = self._q_cached("SELECT * FROM filing_readiness", ttl=120)
        readiness_map = {}
        for r in readiness_rows:
            key = r.get("filing_id", r.get("vehicle_name", ""))
            readiness_map[key] = r.get("readiness_score", 50)

        # Batch count queries — one query per table instead of N per package
        _ev_counts = {}
        for row in self._q("SELECT lane, COUNT(*) as cnt FROM evidence_quotes GROUP BY lane"):
            _ev_counts[row.get("lane", "")] = row.get("cnt", 0)

        _auth_counts = {}
        for row in self._q("SELECT lane, COUNT(*) as cnt FROM authority_chains_v2 GROUP BY lane"):
            _auth_counts[row.get("lane", "")] = row.get("cnt", 0)

        _imp_counts = {}
        for row in self._q("SELECT filing_relevance, COUNT(*) as cnt FROM impeachment_matrix GROUP BY filing_relevance"):
            # filing_relevance can contain multiple IDs; approximate by checking
            for fid_key in (row.get("filing_relevance") or "").split(","):
                fid_key = fid_key.strip()
                if fid_key:
                    _imp_counts[fid_key] = _imp_counts.get(fid_key, 0) + row.get("cnt", 0)

        # Index deadlines by filing_id for O(1) lookup
        _deadline_map = {}
        for d in deadlines:
            fid = d.get("filing_id", "")
            if fid and fid not in _deadline_map:
                _deadline_map[fid] = d

        for pkg in packages:
            lid = pkg.get("filing_id") or pkg.get("lane", "?")
            ln = pkg.get("lane", "?")

            ev_count = _ev_counts.get(ln, 0)
            auth_count = _auth_counts.get(ln, 0)
            imp_count = _imp_counts.get(lid, 0)

            filing_deadline = _deadline_map.get(lid)

            rdns = readiness_map.get(lid, 0)

            gaps = []
            if ev_count < 10:
                gaps.append("LOW evidence ({} items)".format(ev_count))
            if auth_count < 5:
                gaps.append("LOW authority chains ({})".format(auth_count))
            if rdns and rdns < 80:
                gaps.append("Readiness only {}%".format(rdns))

            result["lanes"][lid] = {
                "title": pkg.get("title", LANE_MAP.get(ln, ln)),
                "lane": ln,
                "status": pkg.get("status", "unknown"),
                "evidence_count": ev_count,
                "authority_count": auth_count,
                "impeachment_count": imp_count,
                "readiness_score": rdns,
                "deadline": filing_deadline,
                "gaps": gaps,
                "doc_count": pkg.get("doc_count", 0),
            }

        total_filings = len(result["lanes"])
        ready = sum(1 for v in result["lanes"].values()
                    if (v.get("readiness_score") or 0) >= 90)
        result["summary"] = {
            "total_filings": total_filings,
            "ready_count": ready,
            "not_ready": total_filings - ready,
            "total_deadlines": len(deadlines),
        }

        return result

    # ----------------------------------------------------------------
    # PRIORITIES - Daily action plan
    # ----------------------------------------------------------------
    def priorities(self):
        """Prioritized action items. Priority = urgency x (1 - readiness)."""
        today = date.today()
        result = {"date": today.isoformat(), "items": [], "overdue": []}

        deadlines = self._q_cached("SELECT * FROM deadlines ORDER BY due_date", ttl=120)
        readiness_rows = self._q_cached("SELECT * FROM filing_readiness", ttl=120)
        readiness_map = {}
        for r in readiness_rows:
            key = r.get("filing_id", r.get("vehicle_name", ""))
            readiness_map[key] = r.get("readiness_score", 50)

        for d in deadlines:
            due = d.get("due_date", "2099-12-31")
            try:
                due_date = datetime.strptime(due[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                due_date = date(2099, 12, 31)

            days_left = (due_date - today).days
            filing_id = d.get("filing_id", "")
            rdns = readiness_map.get(filing_id, 50)

            if days_left <= 0:
                urgency = 100
            elif days_left <= 3:
                urgency = 90
            elif days_left <= 7:
                urgency = 70
            elif days_left <= 14:
                urgency = 50
            elif days_left <= 30:
                urgency = 30
            else:
                urgency = 10

            gap = max(0, 100 - (rdns or 50))
            priority_score = urgency + (gap * 0.5)

            if days_left <= 0:
                flag, emoji = "OVERDUE", "\U0001f534"
            elif days_left <= 3:
                flag, emoji = "CRITICAL", "\U0001f7e0"
            elif days_left <= 7:
                flag, emoji = "URGENT", "\U0001f7e1"
            else:
                flag, emoji = "OK", "\U0001f7e2"

            item = {
                "title": d.get("title", "Unknown"),
                "filing_id": filing_id,
                "due_date": due,
                "days_left": days_left,
                "urgency": flag,
                "emoji": emoji,
                "readiness": rdns,
                "priority_score": round(priority_score, 1),
                "court": d.get("court", ""),
                "case_number": d.get("case_number", ""),
            }

            if days_left <= 0:
                result["overdue"].append(item)
            result["items"].append(item)

        result["items"].sort(key=lambda x: x["priority_score"], reverse=True)
        result["separation_days"] = (today - date(2025, 8, 8)).days

        return result

    # ----------------------------------------------------------------
    # ARGUE - Argument chain synthesis
    # ----------------------------------------------------------------
    def argue(self, claim, lane=None, limit=10):
        """Build argument chain: evidence -> authority -> impeachment."""
        result = {
            "claim": claim, "lane": lane,
            "evidence": [], "authorities": [],
            "impeachment": [], "chain_strength": 0,
        }
        like = "%" + claim + "%"
        safe_claim = sanitize_fts5(claim)

        try:
            evidence = self._q("""
                SELECT eq.id, eq.source_file, eq.category, eq.lane,
                       eq.relevance_score,
                       snippet(evidence_fts, 0, '>>>', '<<<', '...', 40) AS excerpt
                FROM evidence_fts
                JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                WHERE evidence_fts MATCH ?
                ORDER BY rank LIMIT ?
            """, [safe_claim, limit])
        except Exception:
            evidence = self._q("""
                SELECT id, source_file, category, lane, relevance_score,
                       substr(quote_text, 1, 200) AS excerpt
                FROM evidence_quotes WHERE quote_text LIKE ?
                ORDER BY relevance_score DESC LIMIT ?
            """, [like, limit])
        result["evidence"] = evidence

        authorities = self._q("""
            SELECT primary_citation, supporting_citation,
                   relationship, source_type, lane
            FROM authority_chains_v2
            WHERE paragraph_context LIKE ?
            ORDER BY lane LIMIT ?
        """, [like, limit])
        result["authorities"] = authorities

        impeachment = self._q("""
            SELECT category, evidence_summary, impeachment_value,
                   cross_exam_question, filing_relevance
            FROM impeachment_matrix
            WHERE evidence_summary LIKE ? OR cross_exam_question LIKE ?
            ORDER BY impeachment_value DESC LIMIT ?
        """, [like, like, limit])
        result["impeachment"] = impeachment

        result["chain_strength"] = (
            len(evidence) * 3 + len(authorities) * 2 + len(impeachment) * 5
        )

        cs = result["chain_strength"]
        if cs >= 100:
            result["rating"] = "DEVASTATING"
        elif cs >= 50:
            result["rating"] = "STRONG"
        elif cs >= 20:
            result["rating"] = "ADEQUATE"
        else:
            result["rating"] = "NEEDS STRENGTHENING"

        return result

    # ----------------------------------------------------------------
    # IMPEACH - Complete impeachment package
    # ----------------------------------------------------------------
    def impeach(self, person, limit=50):
        """Complete impeachment package organized by category."""
        result = {
            "target": person,
            "categories": {},
            "total_items": 0,
            "avg_severity": 0,
            "cross_exam_questions": [],
        }
        like = "%" + person + "%"

        items = self._q("""
            SELECT id, category, evidence_summary, source_file,
                   impeachment_value, cross_exam_question,
                   filing_relevance, event_date
            FROM impeachment_matrix
            WHERE evidence_summary LIKE ? OR cross_exam_question LIKE ?
            ORDER BY impeachment_value DESC LIMIT ?
        """, [like, like, limit])

        cats = defaultdict(list)
        total_value = 0
        seen_questions = set()

        for item in items:
            cat = item.get("category", "UNCATEGORIZED")
            cats[cat].append(item)
            val = item.get("impeachment_value", 0) or 0
            total_value += val
            q = item.get("cross_exam_question", "")
            if q and q not in seen_questions:
                seen_questions.add(q)
                result["cross_exam_questions"].append({
                    "question": q,
                    "severity": val,
                    "category": cat,
                })

        result["total_items"] = len(items)
        result["avg_severity"] = round(total_value / max(1, len(items)), 1)
        result["categories"] = dict(cats)

        result["cross_exam_questions"].sort(
            key=lambda x: x["severity"], reverse=True
        )

        return result

    # ----------------------------------------------------------------
    # DAMAGES - Aggregate damages
    # ----------------------------------------------------------------
    def damages(self, lane=None):
        """Aggregate damages calculations."""
        result = {
            "by_lane": {},
            "totals": {"conservative": 0, "aggressive": 0},
        }

        sql = "SELECT * FROM damages_calculation"
        params = []
        if lane:
            sql += " WHERE lane = ?"
            params = [lane]

        rows = self._q(sql, params)
        lanes_dict = defaultdict(list)

        for row in rows:
            ln = row.get("lane", "?")
            cons = row.get("conservative_amount", 0) or 0
            aggr = row.get("aggressive_amount", 0) or 0

            lanes_dict[ln].append({
                "category": row.get("category", ""),
                "description": row.get("description", ""),
                "conservative": cons,
                "aggressive": aggr,
                "basis": row.get("basis", ""),
            })

            if not row.get("is_summary"):
                result["totals"]["conservative"] += cons
                result["totals"]["aggressive"] += aggr

        result["by_lane"] = dict(lanes_dict)
        result["lane_count"] = len(result["by_lane"])

        return result

    # ----------------------------------------------------------------
    # BRIEF - Full case briefing
    # ----------------------------------------------------------------
    def brief(self, case_type=None):
        """Full multi-case briefing."""
        if case_type:
            return {
                "case_map": self.case_map(case_type),
                "readiness": self.readiness(
                    CASE_PROFILES.get(case_type, {}).get("lanes", [None])[0]
                ),
            }

        return {
            "priorities": self.priorities(),
            "case_maps": {ct: self.case_map(ct) for ct in CASE_PROFILES},
            "readiness": self.readiness(),
            "damages": self.damages(),
        }

    # ----------------------------------------------------------------
    # ALIENATION - Baker's 17 strategies detection
    # ----------------------------------------------------------------
    def alienation(self, strategy=None, limit=30):
        """Detect parental alienation using Baker's 17 strategies."""
        BAKER_STRATEGIES = {
            "badmouthing": "badmouth OR disparage OR negative OR talk bad",
            "limiting_contact": "withhold OR deny OR refuse OR limit contact OR gatekeep",
            "interfering_communication": "block OR phone OR call OR communication OR intercept",
            "emotional_manipulation": "guilt OR manipulat OR emotional OR loyalty conflict",
            "undermining_authority": "undermine OR authority OR discipline OR rules",
            "false_allegations": "false allegation OR fabricat OR lie OR accus",
            "forcing_rejection": "reject OR choose OR pick sides OR allegiance",
            "withholding_love": "conditional OR love OR affection OR withhold",
            "telling_child_not_loved": '"not loved" OR unloved OR abandoned OR "doesn t love"',
            "confiding_inappropriately": "confide OR adult OR inappropriate OR details",
            "forcing_choice": "choose OR loyalty OR forced choice",
            "creating_impression_danger": "danger OR unsafe OR afraid OR scared",
            "interrogation_after_visits": "interrogat OR question OR ask about OR debrief",
            "limiting_photos": "photo OR picture OR memento OR memory OR remove",
            "changing_names": "name OR rename OR last name",
            "cultivating_dependency": "depend OR cling OR separation anxiety",
            "programming": "program OR brainwash OR coach OR script",
        }

        result = {"strategies_detected": {}, "total_hits": 0, "evidence": []}
        strategies = {strategy: BAKER_STRATEGIES[strategy]} if strategy and strategy in BAKER_STRATEGIES else BAKER_STRATEGIES

        for strat_name, fts_query in strategies.items():
            safe_q = sanitize_fts5(fts_query)
            items = self._q("""
                SELECT eq.id, eq.source_file, eq.category, eq.lane,
                       eq.relevance_score,
                       snippet(evidence_fts, 0, '>>>', '<<<', '...', 40) AS excerpt
                FROM evidence_fts
                JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                WHERE evidence_fts MATCH ?
                ORDER BY rank LIMIT ?
            """, [safe_q, limit])
            if items:
                result["strategies_detected"][strat_name] = {
                    "count": len(items),
                    "items": items[:5],
                }
                result["total_hits"] += len(items)
                result["evidence"].extend(items[:3])

        result["strategies_count"] = len(result["strategies_detected"])
        result["baker_score"] = "{}/17".format(result["strategies_count"])
        return result

    # ----------------------------------------------------------------
    # RED_TEAM - Adversarial vulnerability assessment
    # ----------------------------------------------------------------
    def red_team(self, claim, lane=None):
        """Red-team a claim by finding weaknesses opposing counsel would exploit."""
        result = {
            "claim": claim, "lane": lane,
            "vulnerabilities": [], "mitigations": [],
            "overall_risk": "LOW",
        }
        like = "%" + claim + "%"

        # Check for contradictions in our own evidence
        contras = self._q("""
            SELECT id, claim_id, source_a, source_b, contradiction_text, severity
            FROM contradiction_map
            WHERE contradiction_text LIKE ? OR claim_id LIKE ?
            ORDER BY severity DESC LIMIT 10
        """, [like, like])
        for c in contras:
            result["vulnerabilities"].append({
                "type": "INTERNAL_CONTRADICTION",
                "severity": c.get("severity", "medium"),
                "detail": c.get("contradiction_text", ""),
                "sources": [c.get("source_a"), c.get("source_b")],
            })

        # Check adversary models for predicted attacks
        attacks = self._q("""
            SELECT attack_type, rebuttal_strategy, rebuttal_authority
            FROM adversary_models
            WHERE attack_type LIKE ? LIMIT 10
        """, [like])
        for a in attacks:
            result["mitigations"].append({
                "attack": a.get("attack_type"),
                "rebuttal": a.get("rebuttal_strategy"),
                "authority": a.get("rebuttal_authority"),
            })

        # Check risk events
        risks = self._q("""
            SELECT title, risk_class, severity, cure_deadline_clock
            FROM risk_events
            WHERE title LIKE ? ORDER BY severity DESC LIMIT 10
        """, [like])
        for r in risks:
            result["vulnerabilities"].append({
                "type": "RISK_EVENT",
                "severity": r.get("severity", "medium"),
                "detail": r.get("title"),
                "risk_class": r.get("risk_class"),
                "cure_deadline": r.get("cure_deadline_clock"),
            })

        vuln_count = len(result["vulnerabilities"])
        crit = sum(1 for v in result["vulnerabilities"] if v.get("severity") in ("critical", "CRITICAL"))
        if crit > 0:
            result["overall_risk"] = "CRITICAL"
        elif vuln_count > 5:
            result["overall_risk"] = "HIGH"
        elif vuln_count > 2:
            result["overall_risk"] = "MEDIUM"

        return result

    # ----------------------------------------------------------------
    # TIMELINE_FORENSICS - Chronological analysis
    # ----------------------------------------------------------------
    def timeline_forensics(self, date_from=None, date_to=None, actor=None,
                           category=None, limit=50):
        """Timeline forensic analysis with gap detection."""
        result = {"events": [], "gaps": [], "patterns": []}

        sql = "SELECT * FROM timeline_events WHERE 1=1"
        params = []
        if date_from:
            sql += " AND event_date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND event_date <= ?"
            params.append(date_to)
        if actor:
            sql += " AND (actor LIKE ? OR description LIKE ?)"
            params.extend(["%" + actor + "%", "%" + actor + "%"])
        if category:
            sql += " AND category LIKE ?"
            params.append("%" + category + "%")
        sql += " ORDER BY event_date ASC LIMIT ?"
        params.append(limit)

        events = self._q(sql, params)
        result["events"] = events
        result["event_count"] = len(events)

        # Gap detection - find date ranges > 14 days with no events
        if len(events) > 1:
            for i in range(1, len(events)):
                d1 = events[i-1].get("event_date", "")
                d2 = events[i].get("event_date", "")
                if d1 and d2 and len(d1) >= 10 and len(d2) >= 10:
                    try:
                        dt1 = datetime.strptime(d1[:10], "%Y-%m-%d")
                        dt2 = datetime.strptime(d2[:10], "%Y-%m-%d")
                        gap_days = (dt2 - dt1).days
                        if gap_days > 14:
                            result["gaps"].append({
                                "from": d1[:10], "to": d2[:10],
                                "days": gap_days,
                            })
                    except ValueError as e:
                        logger.debug("Skipped malformed date pair %r / %r: %s", d1, d2, e)

        return result

    # ----------------------------------------------------------------
    # AUTHORITY_VALIDATE - Citation validation
    # ----------------------------------------------------------------
    def authority_validate(self, citations=None, filing_id=None):
        """Validate legal citations exist in the database."""
        result = {"validated": [], "missing": [], "total": 0, "pass_rate": 0}

        if not citations:
            citations = []

        # Batch citation validation — 1 query instead of up to 3N
        cite_likes = {"%" + c + "%" : c for c in citations}
        found_cites = set()

        if cite_likes:
            like_params = list(cite_likes.keys())

            # Check auth_rules in batch
            auth_sql = "SELECT rule_number, title FROM auth_rules WHERE " + " OR ".join(
                ["rule_number LIKE ?"] * len(like_params)
            )
            for row in self._q(auth_sql, like_params):
                rn = row.get("rule_number", "")
                for like_pat, orig_cite in cite_likes.items():
                    if like_pat.strip("%") in rn and orig_cite not in found_cites:
                        result["validated"].append({"citation": orig_cite, "source": "auth_rules", "title": row.get("title")})
                        found_cites.add(orig_cite)

            # Check michigan_rules_extracted for remaining
            remaining = {k: v for k, v in cite_likes.items() if v not in found_cites}
            if remaining:
                rem_params = list(remaining.keys())
                rules_sql = "SELECT rule, chapter FROM michigan_rules_extracted WHERE " + " OR ".join(
                    ["rule LIKE ?"] * len(rem_params)
                )
                for row in self._q(rules_sql, rem_params):
                    rl = row.get("rule", "")
                    for like_pat, orig_cite in remaining.items():
                        if like_pat.strip("%") in rl and orig_cite not in found_cites:
                            result["validated"].append({"citation": orig_cite, "source": "michigan_rules_extracted", "chapter": row.get("chapter")})
                            found_cites.add(orig_cite)

            # Check master_citations for remaining
            remaining2 = {k: v for k, v in cite_likes.items() if v not in found_cites}
            if remaining2:
                rem2_params = list(remaining2.keys())
                mc_sql = "SELECT citation, cite_type FROM master_citations WHERE " + " OR ".join(
                    ["citation LIKE ?"] * len(rem2_params)
                ) + " LIMIT 500"
                for row in self._q(mc_sql, rem2_params):
                    ct = row.get("citation", "")
                    for like_pat, orig_cite in remaining2.items():
                        if like_pat.strip("%") in ct and orig_cite not in found_cites:
                            result["validated"].append({"citation": orig_cite, "source": "master_citations", "type": row.get("cite_type")})
                            found_cites.add(orig_cite)

            # Collect missing
            result["missing"] = [c for c in citations if c not in found_cites]

        result["total"] = len(citations)
        result["pass_rate"] = round(len(result["validated"]) / max(1, len(citations)) * 100, 1)
        return result

    # ----------------------------------------------------------------
    # GAP_TRACKER - Convergence gaps
    # ----------------------------------------------------------------
    def gap_tracker(self, gap_type=None, lane=None, severity=None):
        """Query convergence gaps preventing filing."""
        result = {"gaps": [], "summary": {}}

        sql = "SELECT * FROM gap_tickets WHERE 1=1"
        params = []
        if gap_type:
            sql += " AND gap_type = ?"
            params.append(gap_type)
        if lane:
            sql += " AND lane LIKE ?"
            params.append("%" + lane + "%")
        if severity:
            sql += " AND severity = ?"
            params.append(severity)
        sql += " ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END LIMIT 50"

        gaps = self._q(sql, params)
        result["gaps"] = gaps
        result["total"] = len(gaps)

        # Summarize
        by_sev = defaultdict(int)
        by_type = defaultdict(int)
        for g in gaps:
            by_sev[g.get("severity", "UNKNOWN")] += 1
            by_type[g.get("gap_type", "UNKNOWN")] += 1
        result["summary"] = {"by_severity": dict(by_sev), "by_type": dict(by_type)}

        return result

    # ----------------------------------------------------------------
    # FILING_PRIORITY - Ranked filing priority matrix
    # ----------------------------------------------------------------
    def filing_priority(self, lane=None):
        """Ranked filing priority combining readiness + urgency."""
        readiness = self.readiness(lane=lane)
        priorities = self.priorities()

        filings = []
        ready_map = {}
        for f in readiness.get("filings", []):
            fid = f.get("filing_id", "")
            ready_map[fid] = f

        # Merge with priority data
        for p in priorities.get("filings", []):
            fid = p.get("filing_id", "")
            r = ready_map.get(fid, {})
            composite = (r.get("readiness_score", 0) or 0) * 0.4 + (p.get("priority_score", 50) or 50) * 0.6
            filings.append({
                "filing_id": fid,
                "lane": p.get("lane", r.get("lane", "")),
                "title": p.get("title", r.get("title", "")),
                "readiness_score": r.get("readiness_score", 0),
                "urgency": p.get("urgency", ""),
                "days_until_deadline": p.get("days_until", ""),
                "composite_priority": round(composite, 1),
                "status": "READY" if (r.get("readiness_score", 0) or 0) >= 75 else "DEVELOPING",
            })

        filings.sort(key=lambda x: x.get("composite_priority", 0), reverse=True)
        return {"filings": filings, "total": len(filings)}

    # ----------------------------------------------------------------
    # CUSTODY_FACTORS - Deep MCL 722.23 analysis
    # ----------------------------------------------------------------
    def custody_factors(self, factor=None):
        """Deep dive into MCL 722.23 best interest factors."""
        factors_to_analyze = {}
        if factor:
            f = factor.lower().strip()
            if f in CUSTODY_FACTORS:
                factors_to_analyze = {f: CUSTODY_FACTORS[f]}
            else:
                # Try to find by keyword
                for k, v in CUSTODY_FACTORS.items():
                    if f in v["name"].lower() or f in v["fts"].lower():
                        factors_to_analyze[k] = v
                if not factors_to_analyze:
                    factors_to_analyze = CUSTODY_FACTORS
        else:
            factors_to_analyze = CUSTODY_FACTORS

        result = {"factors": {}, "totals": {"andrew": 0, "emily": 0}}

        for fkey, fdata in factors_to_analyze.items():
            safe_fts = sanitize_fts5(fdata["fts"])
            evidence = self._q("""
                SELECT eq.id, eq.source_file, eq.category, eq.lane,
                       eq.relevance_score,
                       snippet(evidence_fts, 0, '>>>', '<<<', '...', 40) AS excerpt
                FROM evidence_fts
                JOIN evidence_quotes eq ON evidence_fts.rowid = eq.id
                WHERE evidence_fts MATCH ?
                ORDER BY rank LIMIT 20
            """, [safe_fts])

            result["factors"]["({}) {}".format(fkey, fdata["name"])] = {
                "statute": fdata["statute"],
                "evidence_count": len(evidence),
                "top_evidence": evidence[:5],
            }

        return result

    # ----------------------------------------------------------------
    # EMERGENCE_SCAN - Cross-lane pattern detection
    # ----------------------------------------------------------------
    def emergence_scan(self, signal_type=None, min_novelty=5, limit=30):
        """Detect cross-lane emergence patterns."""
        result = {"signals": [], "summary": {}}

        # Entity overlap across lanes
        overlap_sql = """
            SELECT eq.lane, eq.category, COUNT(*) as cnt
            FROM evidence_quotes eq
            WHERE eq.lane IS NOT NULL AND eq.category IS NOT NULL
            GROUP BY eq.lane, eq.category
            HAVING cnt > 10
            ORDER BY cnt DESC LIMIT ?
        """
        overlaps = self._q(overlap_sql, [limit])
        for o in overlaps:
            novelty = min(10, (o.get("cnt", 0) or 0) // 50 + 3)
            if novelty >= min_novelty:
                result["signals"].append({
                    "type": "CROSS_GRAPH",
                    "lane": o.get("lane"),
                    "category": o.get("category"),
                    "count": o.get("cnt"),
                    "novelty": novelty,
                })

        # Contradiction clusters
        contra_sql = """
            SELECT lane, severity, COUNT(*) as cnt
            FROM contradiction_map
            WHERE severity IN ('critical', 'high')
            GROUP BY lane, severity
            HAVING cnt > 3
            ORDER BY cnt DESC LIMIT ?
        """
        contras = self._q(contra_sql, [limit])
        for c in contras:
            novelty = min(10, (c.get("cnt", 0) or 0) // 5 + 5)
            if novelty >= min_novelty:
                result["signals"].append({
                    "type": "CONTRADICTION",
                    "lane": c.get("lane"),
                    "severity": c.get("severity"),
                    "count": c.get("cnt"),
                    "novelty": novelty,
                })

        result["signals"].sort(key=lambda x: x.get("novelty", 0), reverse=True)
        result["total_signals"] = len(result["signals"])

        by_type = defaultdict(int)
        for s in result["signals"]:
            by_type[s["type"]] += 1
        result["summary"] = dict(by_type)

        return result


# ====================================================================
# CLI INTERFACE
# ====================================================================

ACTIONS = {
    "fuse": lambda eng, req: eng.fuse(
        req["topic"], lanes=req.get("lanes"), limit=req.get("limit", 50)),
    "case_map": lambda eng, req: eng.case_map(req["case_type"]),
    "credibility": lambda eng, req: eng.credibility(
        req["person"], limit=req.get("limit", 25)),
    "readiness": lambda eng, req: eng.readiness(lane=req.get("lane")),
    "priorities": lambda eng, req: eng.priorities(),
    "argue": lambda eng, req: eng.argue(
        req["claim"], lane=req.get("lane"), limit=req.get("limit", 10)),
    "impeach": lambda eng, req: eng.impeach(
        req["person"], limit=req.get("limit", 50)),
    "damages": lambda eng, req: eng.damages(lane=req.get("lane")),
    "brief": lambda eng, req: eng.brief(case_type=req.get("case_type")),
    "profiles": lambda eng, req: {
        k: {"name": v["name"], "case_number": v["case_number"],
             "court": v["court"], "lanes": v["lanes"], "filings": v["filings"]}
        for k, v in CASE_PROFILES.items()
    },
    # --- NEW ACTIONS (OMEGA upgrade) ---
    "alienation": lambda eng, req: eng.alienation(
        strategy=req.get("strategy"), limit=req.get("limit", 30)),
    "red_team": lambda eng, req: eng.red_team(
        req["claim"], lane=req.get("lane")),
    "timeline_forensics": lambda eng, req: eng.timeline_forensics(
        date_from=req.get("date_from"), date_to=req.get("date_to"),
        actor=req.get("actor"), category=req.get("category"),
        limit=req.get("limit", 50)),
    "authority_validate": lambda eng, req: eng.authority_validate(
        citations=req.get("citations"), filing_id=req.get("filing_id")),
    "gap_tracker": lambda eng, req: eng.gap_tracker(
        gap_type=req.get("gap_type"), lane=req.get("lane"),
        severity=req.get("severity")),
    "filing_priority": lambda eng, req: eng.filing_priority(
        lane=req.get("lane")),
    "custody_factors": lambda eng, req: eng.custody_factors(
        factor=req.get("factor")),
    "emergence_scan": lambda eng, req: eng.emergence_scan(
        signal_type=req.get("signal_type"),
        min_novelty=req.get("min_novelty", 5),
        limit=req.get("limit", 30)),
}


def main():
    """CLI: Read JSON from stdin, execute action, write JSON to stdout."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            json.dump({"error": "No input", "actions": list(ACTIONS.keys())},
                      sys.stdout)
            return

        request = json.loads(raw)
        action = request.get("action", "")

        if action not in ACTIONS:
            json.dump({"error": "Unknown action: " + action,
                       "valid_actions": list(ACTIONS.keys())}, sys.stdout)
            return

        engine = NexusEngine(request.get("db_path"))
        result = ACTIONS[action](engine, request)
        json.dump(result, sys.stdout, default=str)

    except json.JSONDecodeError as e:
        json.dump({"error": "Invalid JSON: " + str(e)}, sys.stdout)
    except KeyError as e:
        json.dump({"error": "Missing required field: " + str(e)}, sys.stdout)
    except Exception as e:
        json.dump({"error": str(e), "type": type(e).__name__}, sys.stdout)


if __name__ == "__main__":
    main()
