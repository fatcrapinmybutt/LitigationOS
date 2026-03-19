#!/usr/bin/env python3
"""
MBP LitigationOS -- Narrative Builder Skill
=============================================
Build case narratives from the narrative, case_intelligence_hub,
and master_timeline tables. Constructs statements of facts, opening/
closing narratives, and issue-focused narratives for
Pigors v. Watson (COA 366810, 14th Circuit, Muskegon County).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
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


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


class NarrativeBuilder:
    """Build litigation narratives from DB tables (62k+ narrative rows,
    32k+ case_intelligence_hub rows, 5.5k+ master_timeline rows)."""

    CASE_CAPTION = "Pigors v. Watson"
    COA_DOCKET = "COA 366810"
    CIRCUIT_COURT = "14th Circuit Court, Muskegon County"
    JUDGE = "Hon. Jenny L. McNeill"

    # ── Raw data access ───────────────────────────────────────────────

    def get_narratives(self, limit: int = 200) -> List[Dict]:
        """Query the narrative table (62,027 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM narrative ORDER BY rowid LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_case_intelligence(
        self, topic: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """Query case_intelligence_hub (32,579 rows) with optional FTS."""
        conn = _get_db()
        if not conn:
            return []
        try:
            if topic:
                try:
                    rows = conn.execute(
                        "SELECT * FROM case_intelligence_hub WHERE rowid IN "
                        "(SELECT rowid FROM case_intelligence_hub_fts "
                        " WHERE case_intelligence_hub_fts MATCH ?) LIMIT ?",
                        (topic, limit),
                    ).fetchall()
                    return [dict(r) for r in rows]
                except Exception:
                    rows = conn.execute(
                        "SELECT * FROM case_intelligence_hub "
                        "WHERE rowid IN (SELECT rowid FROM case_intelligence_hub "
                        "               WHERE CAST(rowid AS TEXT) LIKE '%' || ? || '%') "
                        "LIMIT ?",
                        (topic, limit),
                    ).fetchall()
                    return [dict(r) for r in rows]
            else:
                rows = conn.execute(
                    "SELECT * FROM case_intelligence_hub ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_timeline_events(self, limit: int = 200) -> List[Dict]:
        """Query master_timeline (5,536 rows)."""
        conn = _get_db()
        if not conn:
            return []
        try:
            rows = conn.execute(
                "SELECT * FROM master_timeline ORDER BY rowid LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    # ── Narrative builders ────────────────────────────────────────────

    def build_statement_of_facts(self, lane: Optional[str] = None) -> Dict:
        """Construct a chronological statement of facts from narrative +
        timeline data, optionally filtered by case lane (A-F)."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable", "facts": []}
        try:
            # Gather timeline events
            timeline_rows = conn.execute(
                "SELECT * FROM master_timeline ORDER BY rowid LIMIT 500"
            ).fetchall()
            timeline = [dict(r) for r in timeline_rows]

            # Gather narrative entries
            narrative_rows = conn.execute(
                "SELECT * FROM narrative ORDER BY rowid LIMIT 500"
            ).fetchall()
            narratives = [dict(r) for r in narrative_rows]

            # Optional lane filter — search for lane identifier in text fields
            if lane:
                lane_upper = lane.upper()
                narratives = [
                    n for n in narratives
                    if any(
                        lane_upper in str(v).upper()
                        for v in n.values()
                        if v is not None
                    )
                ]

            # Merge into fact entries
            facts: List[Dict] = []
            for t in timeline:
                facts.append({
                    "source": "master_timeline",
                    "content": t,
                })
            for n in narratives[:200]:
                facts.append({
                    "source": "narrative",
                    "content": n,
                })

            return {
                "case": self.CASE_CAPTION,
                "court": self.CIRCUIT_COURT,
                "judge": self.JUDGE,
                "lane_filter": lane,
                "total_facts": len(facts),
                "facts": facts,
            }
        except Exception as e:
            return {"error": str(e), "facts": []}
        finally:
            conn.close()

    def build_opening_narrative(self) -> Dict:
        """Build a compelling opening statement narrative from key facts."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Key evidence quotes for impact
            evidence = conn.execute(
                "SELECT quote_text, speaker, legal_significance, evidence_category "
                "FROM evidence_quotes "
                "WHERE legal_significance IS NOT NULL AND legal_significance != '' "
                "ORDER BY rowid LIMIT 50"
            ).fetchall()
            evidence_list = [dict(r) for r in evidence]

            # Timeline for chronology
            timeline = conn.execute(
                "SELECT * FROM master_timeline ORDER BY rowid LIMIT 100"
            ).fetchall()
            timeline_list = [dict(r) for r in timeline]

            # Case intelligence for themes
            intel = conn.execute(
                "SELECT * FROM case_intelligence_hub ORDER BY rowid LIMIT 50"
            ).fetchall()
            intel_list = [dict(r) for r in intel]

            return {
                "case": self.CASE_CAPTION,
                "docket": self.COA_DOCKET,
                "narrative_type": "opening_statement",
                "theme": (
                    "329+ days of parent-child separation resulting from "
                    "systematic procedural violations and judicial misconduct"
                ),
                "key_evidence": evidence_list,
                "chronology": timeline_list,
                "intelligence": intel_list,
                "structure": [
                    "Introduction — fundamental parental rights at stake",
                    "Background — family history and custodial environment",
                    "The separation — 329+ days without parent-child contact",
                    "Procedural violations — ex parte, due process, MCR noncompliance",
                    "Impact — harm to child and parent",
                    "Relief sought — reunification and corrective orders",
                ],
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def build_closing_narrative(self) -> Dict:
        """Build a closing argument narrative summarizing the case."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # Judicial violations for misconduct argument
            violations = []
            try:
                rows = conn.execute(
                    "SELECT * FROM judicial_violations ORDER BY rowid LIMIT 50"
                ).fetchall()
                violations = [dict(r) for r in rows]
            except Exception:
                pass

            # Contradiction evidence
            contradictions = []
            try:
                rows = conn.execute(
                    "SELECT * FROM contradiction_map ORDER BY rowid LIMIT 30"
                ).fetchall()
                contradictions = [dict(r) for r in rows]
            except Exception:
                pass

            # Impeachment material
            impeachment = []
            try:
                rows = conn.execute(
                    "SELECT * FROM impeachment_items ORDER BY rowid LIMIT 30"
                ).fetchall()
                impeachment = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "case": self.CASE_CAPTION,
                "docket": self.COA_DOCKET,
                "narrative_type": "closing_argument",
                "theme": (
                    "The record demonstrates a pattern of procedural violations "
                    "that deprived Plaintiff of fundamental parental rights"
                ),
                "judicial_violations": violations,
                "contradictions": contradictions,
                "impeachment": impeachment,
                "structure": [
                    "Restatement of issues — what was at stake",
                    "Evidence summary — what the record proved",
                    "Judicial errors — specific MCR/MCL violations",
                    "Harm — 329+ days separation, constitutional deprivation",
                    "Call to action — specific relief requested",
                ],
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def build_issue_narrative(self, issue: str) -> Dict:
        """Build a focused narrative for a specific issue
        (e.g., ex_parte, alienation, custody, misconduct, due_process)."""
        conn = _get_db()
        if not conn:
            return {"error": "DB unavailable"}
        try:
            # FTS search across narrative
            narrative_hits = []
            try:
                rows = conn.execute(
                    "SELECT * FROM narrative WHERE rowid IN "
                    "(SELECT rowid FROM narrative LIMIT 500) "
                    "LIMIT 100"
                ).fetchall()
                # Filter in Python for flexibility
                for r in rows:
                    rd = dict(r)
                    if any(
                        issue.lower() in str(v).lower()
                        for v in rd.values()
                        if v is not None
                    ):
                        narrative_hits.append(rd)
            except Exception:
                pass

            # Evidence quotes matching issue
            evidence_hits = []
            try:
                rows = conn.execute(
                    "SELECT rowid, * FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ?) LIMIT 50",
                    (issue,),
                ).fetchall()
                evidence_hits = [dict(r) for r in rows]
            except Exception:
                pass

            # Case intelligence on issue
            intel_hits = []
            try:
                rows = conn.execute(
                    "SELECT * FROM case_intelligence_hub WHERE rowid IN "
                    "(SELECT rowid FROM case_intelligence_hub_fts "
                    " WHERE case_intelligence_hub_fts MATCH ?) LIMIT 50",
                    (issue,),
                ).fetchall()
                intel_hits = [dict(r) for r in rows]
            except Exception:
                pass

            return {
                "case": self.CASE_CAPTION,
                "issue": issue,
                "narrative_hits": len(narrative_hits),
                "evidence_hits": len(evidence_hits),
                "intelligence_hits": len(intel_hits),
                "narrative": narrative_hits[:50],
                "evidence": evidence_hits,
                "intelligence": intel_hits,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def search_narratives(self, query: str) -> List[Dict]:
        """FTS search across narrative-related tables."""
        conn = _get_db()
        if not conn:
            return []
        results: List[Dict] = []
        try:
            # Search case_intelligence_hub_fts
            try:
                rows = conn.execute(
                    "SELECT * FROM case_intelligence_hub WHERE rowid IN "
                    "(SELECT rowid FROM case_intelligence_hub_fts "
                    " WHERE case_intelligence_hub_fts MATCH ?) LIMIT 30",
                    (query,),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "case_intelligence_hub"
                    results.append(d)
            except Exception:
                pass

            # Search evidence_quotes_fts
            try:
                rows = conn.execute(
                    "SELECT rowid, * FROM evidence_quotes WHERE rowid IN "
                    "(SELECT rowid FROM evidence_quotes_fts "
                    " WHERE evidence_quotes_fts MATCH ?) LIMIT 30",
                    (query,),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "evidence_quotes"
                    results.append(d)
            except Exception:
                pass

            # Search md_sections_fts
            try:
                rows = conn.execute(
                    "SELECT rowid, * FROM md_sections WHERE rowid IN "
                    "(SELECT rowid FROM md_sections_fts "
                    " WHERE md_sections_fts MATCH ?) LIMIT 20",
                    (query,),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "md_sections"
                    results.append(d)
            except Exception:
                pass

        except Exception:
            pass
        finally:
            conn.close()
        return results

    def get_key_facts(self, limit: int = 50) -> List[Dict]:
        """Retrieve the most critical facts for the case."""
        conn = _get_db()
        if not conn:
            return []
        facts: List[Dict] = []
        try:
            # High-significance evidence quotes
            try:
                rows = conn.execute(
                    "SELECT quote_text, speaker, legal_significance, "
                    "evidence_category, date_ref "
                    "FROM evidence_quotes "
                    "WHERE legal_significance IS NOT NULL "
                    "AND legal_significance != '' "
                    "ORDER BY rowid LIMIT ?",
                    (limit,),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "evidence_quotes"
                    facts.append(d)
            except Exception:
                pass

            # Impeachment items (key adversarial facts)
            try:
                rows = conn.execute(
                    "SELECT * FROM impeachment_items ORDER BY rowid LIMIT ?",
                    (max(10, limit // 5),),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "impeachment_items"
                    facts.append(d)
            except Exception:
                pass

            # Judicial violations (key procedural facts)
            try:
                rows = conn.execute(
                    "SELECT * FROM judicial_violations ORDER BY rowid LIMIT ?",
                    (max(10, limit // 5),),
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["_source"] = "judicial_violations"
                    facts.append(d)
            except Exception:
                pass

        except Exception:
            pass
        finally:
            conn.close()
        return facts[:limit]


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    nb = NarrativeBuilder()
    usage = (
        "Narrative Builder Skill\n"
        "Usage:\n"
        "  python narrative_builder.py narratives [LIMIT]\n"
        "  python narrative_builder.py intelligence [TOPIC] [LIMIT]\n"
        "  python narrative_builder.py timeline [LIMIT]\n"
        "  python narrative_builder.py facts [LIMIT]\n"
        "  python narrative_builder.py statement [LANE]\n"
        "  python narrative_builder.py opening\n"
        "  python narrative_builder.py closing\n"
        "  python narrative_builder.py issue <ISSUE>\n"
        "  python narrative_builder.py search <QUERY>\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "narratives":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        cycle_json(nb.get_narratives(lim))
    elif cmd == "intelligence":
        topic = sys.argv[2] if len(sys.argv) > 2 else None
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        cycle_json(nb.get_case_intelligence(topic, lim))
    elif cmd == "timeline":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        cycle_json(nb.get_timeline_events(lim))
    elif cmd == "facts":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        cycle_json(nb.get_key_facts(lim))
    elif cmd == "statement":
        lane = sys.argv[2] if len(sys.argv) > 2 else None
        cycle_json(nb.build_statement_of_facts(lane))
    elif cmd == "opening":
        cycle_json(nb.build_opening_narrative())
    elif cmd == "closing":
        cycle_json(nb.build_closing_narrative())
    elif cmd == "issue":
        if len(sys.argv) < 3:
            print("Error: issue name required", file=sys.stderr)
            sys.exit(1)
        cycle_json(nb.build_issue_narrative(sys.argv[2]))
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Error: search query required", file=sys.stderr)
            sys.exit(1)
        cycle_json(nb.search_narratives(" ".join(sys.argv[2:])))
    else:
        print(usage)
