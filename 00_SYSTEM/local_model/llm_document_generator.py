#!/usr/bin/env python3
"""
MBP LitigationOS — LLM Document Generation Engine
===================================================
AI-powered court document generation using TF-IDF model + doc_templates.
Queries litigation_context.db for authorities, evidence, and existing
document patterns, then fills MCR 2.113 compliant templates.

Case: Andrew Pigors v. Tiffany Watson
Courts: 14th Circuit (Muskegon), Michigan COA (366810)

Usage:
    # Python API
    from llm_document_generator import DocumentGenerator
    gen = DocumentGenerator()
    doc = gen.generate_motion("Motion to Compel Discovery", ["FOC failed to respond"], lane='A')

    # CLI
    python llm_document_generator.py motion --topic "Motion to Compel" --lane A

    # JSON-RPC via stdin/stdout pipe (for Electron integration)
    python llm_document_generator.py --pipe
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Cycle Method I/O ───────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda o, **k: print(json.dumps(o, default=str))
    cycle_print = print

# ── Local imports ──────────────────────────────────────────────────────
from doc_templates import (
    TEMPLATES, get_template, motion_template, brief_template,
    affidavit_template, response_template, order_template,
    _caption, _signature_block, _certificate_of_service,
    _numbered_paragraphs, PLAINTIFF_FULL, DEFENDANT_FULL, JUDGE,
)

# ── Constants ──────────────────────────────────────────────────────────
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# Lane mapping: user-friendly lane letters → doc_templates lane keys
LANE_MAP = {
    "A": "MEEK2",   # Watson Custody — 2024-001507-DC
    "B": "MEEK2",   # Shady Oaks Housing — same circuit
    "C": "MEEK2",   # Convergence — multi-lane
    "D": "MEEK1",   # PPO — 2023-5907-PP
    "E": "MEEK3",   # Judicial Misconduct — appellate/JTC
    "F": "MEEK3",   # Appellate — COA 366810
}

LANE_DESCRIPTIONS = {
    "A": "Watson Custody (2024-001507-DC)",
    "B": "Shady Oaks Housing",
    "C": "Cross-Lane Convergence",
    "D": "PPO (2023-5907-PP)",
    "E": "Judicial Misconduct",
    "F": "Appellate (COA 366810)",
}

# Alienation theme constants — injected into every custody-related document
ALIENATION_AUTHORITY = [
    "MCL 722.23(j) — willingness to facilitate close relationship with other parent",
    "Harvey v Harvey, 470 Mich 186 (2004) — alienation as factor in custody",
    "Berger v Berger, 277 Mich App 700, 715 (2008) — deliberate interference",
]

ALIENATION_IRAC = {
    "issue": ("Whether Defendant's conduct constitutes parental alienation "
              "under MCL 722.23(j) and Michigan case law"),
    "rule": ("MCL 722.23(j) requires the court to consider 'the willingness and "
             "ability of each of the parties to facilitate and encourage a close and "
             "continuing parent-child relationship between the child and the other "
             "parent.' Harvey v Harvey, 470 Mich 186, 190 (2004), recognizes that "
             "a parent's alienating behavior is a significant factor weighing "
             "against that parent in custody determinations."),
    "application": ("Defendant has engaged in a pattern of alienating conduct "
                    "resulting in 329+ days of parent-child separation, "
                    "directly undermining Factor (j)."),
    "conclusion": ("The Court should weigh Factor (j) heavily against Defendant "
                   "and order immediate restoration of parenting time."),
}


class DocumentGenerator:
    """
    AI document generation engine.
    Combines TF-IDF retrieval from litigation_context.db with
    doc_templates.py to produce court-ready documents.
    """

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None
        self._error_log: List[Dict[str, Any]] = []

    # ── Database ───────────────────────────────────────────────────────

    def _get_db(self) -> Optional[sqlite3.Connection]:
        """Get DB connection with self-healing reconnect."""
        if self._db:
            try:
                self._db.execute("SELECT 1")
                return self._db
            except Exception:
                self._db = None

        for attempt in range(3):
            try:
                self._db = sqlite3.connect(DB_PATH, timeout=60)
                self._db.execute("PRAGMA journal_mode=WAL")
                self._db.execute("PRAGMA cache_size=-65536")
                self._db.execute("PRAGMA query_only=ON")
                self._db.execute("PRAGMA temp_store=MEMORY")
                self._db.row_factory = sqlite3.Row
                return self._db
            except Exception as e:
                self._log_error("db_connect", f"Attempt {attempt+1}: {e}")
                time.sleep(0.5 * (attempt + 1))
                self._db = None
        return None

    def _log_error(self, component: str, msg: str):
        entry = {"ts": time.time(), "component": component, "msg": str(msg)[:300]}
        self._error_log.append(entry)
        if len(self._error_log) > 500:
            self._error_log = self._error_log[-250:]

    # ── DB Query Helpers ───────────────────────────────────────────────

    def _query_authorities(self, topic: str, limit: int = 10) -> List[Dict]:
        """Search auth_rules via FTS5 for relevant authorities."""
        conn = self._get_db()
        if not conn:
            return []
        results = []
        try:
            # FTS5 search on auth_rules_fts
            rows = conn.execute(
                "SELECT rule_number, title, full_text FROM auth_rules "
                "WHERE id IN (SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
                "LIMIT ?",
                (topic, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "rule_number": r["rule_number"],
                    "title": r["title"],
                    "text": (r["full_text"] or "")[:500],
                })
        except Exception as e:
            self._log_error("query_authorities_fts", str(e))
            # Fallback: LIKE search
            try:
                kw = f"%{topic.split()[0] if topic.split() else topic}%"
                rows = conn.execute(
                    "SELECT rule_number, title, full_text FROM auth_rules "
                    "WHERE rule_number LIKE ? OR title LIKE ? LIMIT ?",
                    (kw, kw, limit),
                ).fetchall()
                for r in rows:
                    results.append({
                        "rule_number": r["rule_number"],
                        "title": r["title"],
                        "text": (r["full_text"] or "")[:500],
                    })
            except Exception as e2:
                self._log_error("query_authorities_fallback", str(e2))
        return results

    def _query_evidence(self, topic: str, limit: int = 10) -> List[Dict]:
        """Search evidence_quotes via FTS5 for supporting evidence."""
        conn = self._get_db()
        if not conn:
            return []
        results = []
        try:
            rows = conn.execute(
                "SELECT quote_text, speaker, legal_significance, evidence_category "
                "FROM evidence_quotes "
                "WHERE id IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?) "
                "LIMIT ?",
                (topic, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "quote_text": r["quote_text"],
                    "speaker": r["speaker"],
                    "legal_significance": r["legal_significance"],
                    "category": r["evidence_category"],
                })
        except Exception as e:
            self._log_error("query_evidence_fts", str(e))
            # Fallback: LIKE search
            try:
                kw = f"%{topic.split()[0] if topic.split() else topic}%"
                rows = conn.execute(
                    "SELECT quote_text, speaker, legal_significance, evidence_category "
                    "FROM evidence_quotes WHERE quote_text LIKE ? OR legal_significance LIKE ? "
                    "LIMIT ?",
                    (kw, kw, limit),
                ).fetchall()
                for r in rows:
                    results.append({
                        "quote_text": r["quote_text"],
                        "speaker": r["speaker"],
                        "legal_significance": r["legal_significance"],
                        "category": r["evidence_category"],
                    })
            except Exception as e2:
                self._log_error("query_evidence_fallback", str(e2))
        return results

    def _query_existing_documents(self, lane: str, limit: int = 5) -> List[Dict]:
        """Retrieve existing document patterns from court_documents_v4."""
        conn = self._get_db()
        if not conn:
            return []
        results = []
        try:
            rows = conn.execute(
                "SELECT title, lane, citation_count_mcr, citation_count_mcl, "
                "citation_count_caselaw, paragraph_count "
                "FROM court_documents_v4 WHERE lane = ? ORDER BY created_at DESC LIMIT ?",
                (lane, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "title": r["title"],
                    "lane": r["lane"],
                    "mcr_cites": r["citation_count_mcr"],
                    "mcl_cites": r["citation_count_mcl"],
                    "caselaw_cites": r["citation_count_caselaw"],
                    "paragraphs": r["paragraph_count"],
                })
        except Exception as e:
            self._log_error("query_existing_docs", str(e))
        return results

    def _verify_citation(self, citation: str) -> bool:
        """Verify a citation exists in auth_rules or master_citations."""
        conn = self._get_db()
        if not conn:
            return False
        try:
            row = conn.execute(
                "SELECT 1 FROM auth_rules WHERE rule_number = ? LIMIT 1",
                (citation,),
            ).fetchone()
            if row:
                return True
            row = conn.execute(
                "SELECT 1 FROM master_citations WHERE citation LIKE ? LIMIT 1",
                (f"%{citation}%",),
            ).fetchone()
            return row is not None
        except Exception:
            return False

    # ── Alienation Theme ───────────────────────────────────────────────

    def _should_inject_alienation(self, lane: str, topic: str) -> bool:
        """Determine if alienation theme should be injected."""
        custody_lanes = {"A", "C", "D", "F"}
        alienation_keywords = [
            "custody", "parenting", "alienat", "factor", "best interest",
            "visitation", "separation", "child", "722.23",
        ]
        if lane.upper() in custody_lanes:
            return True
        topic_lower = topic.lower()
        return any(kw in topic_lower for kw in alienation_keywords)

    def _build_alienation_argument(self) -> Dict[str, str]:
        """Build IRAC argument for alienation theme."""
        return dict(ALIENATION_IRAC)

    # ── Document Generation ────────────────────────────────────────────

    def generate_motion(
        self,
        topic: str,
        facts: Optional[List[str]] = None,
        lane: str = "A",
        authority_list: Optional[List[str]] = None,
        relief: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a motion document with DB-enriched content.

        Returns dict with 'document' (markdown string), 'metadata', 'db_context'.
        """
        try:
            template_lane = LANE_MAP.get(lane.upper(), "MEEK2")

            # Query DB for context
            db_authorities = self._query_authorities(topic)
            db_evidence = self._query_evidence(topic)
            db_existing = self._query_existing_documents(lane.upper())

            # Build authority list
            authorities = list(authority_list or [])
            for auth in db_authorities[:5]:
                cite_str = f"{auth['rule_number']} — {auth['title']}"
                if cite_str not in authorities:
                    authorities.append(cite_str)

            # Build facts from evidence
            fact_list = list(facts or [])
            for ev in db_evidence[:3]:
                fact_str = f"{ev['quote_text'][:200]} (Source: {ev['speaker'] or 'record'})"
                if fact_str not in fact_list:
                    fact_list.append(fact_str)

            # Build IRAC arguments
            arguments = []
            for auth in db_authorities[:3]:
                arguments.append({
                    "issue": f"Whether {auth['rule_number']} ({auth['title']}) applies to the present matter",
                    "rule": f"{auth['rule_number']}: {auth['text'][:300]}",
                    "application": f"Applied to the facts of this case, {auth['rule_number']} supports Plaintiff's position.",
                    "conclusion": f"The Court should apply {auth['rule_number']} in Plaintiff's favor.",
                })

            # Inject alienation theme if applicable
            if self._should_inject_alienation(lane, topic):
                arguments.append(self._build_alienation_argument())
                for a in ALIENATION_AUTHORITY:
                    if a not in authorities:
                        authorities.append(a)

            # Generate document
            doc_title = f"MOTION {topic.upper()}"
            document = motion_template(
                title=doc_title,
                lane=template_lane,
                statement_of_issues=[topic],
                statement_of_facts=fact_list if fact_list else None,
                arguments=arguments if arguments else None,
                relief_requested=relief,
                authorities_cited=authorities if authorities else None,
            )

            metadata = {
                "document_type": "motion",
                "lane": lane.upper(),
                "lane_description": LANE_DESCRIPTIONS.get(lane.upper(), "Unknown"),
                "topic": topic,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "authority_count": len(authorities),
                "fact_count": len(fact_list),
                "argument_count": len(arguments),
                "alienation_injected": self._should_inject_alienation(lane, topic),
            }

            return {
                "ok": True,
                "document": document,
                "metadata": metadata,
                "db_context": {
                    "authorities_found": len(db_authorities),
                    "evidence_found": len(db_evidence),
                    "existing_docs_found": len(db_existing),
                },
                "errors": [e["msg"] for e in self._error_log[-5:]],
            }

        except Exception as e:
            self._log_error("generate_motion", str(e))
            return {"ok": False, "error": str(e), "document": ""}

    def generate_brief(
        self,
        issues: Optional[List[str]] = None,
        arguments: Optional[List[Dict[str, str]]] = None,
        lane: str = "F",
        facts: Optional[List[str]] = None,
        standard_of_review: str = "",
    ) -> Dict[str, Any]:
        """Generate an appellate brief with DB-enriched content."""
        try:
            template_lane = LANE_MAP.get(lane.upper(), "MEEK3")
            topic = " OR ".join(issues[:3]) if issues else "appeal"

            db_authorities = self._query_authorities(topic)
            db_evidence = self._query_evidence(topic)

            # Build index of authorities from DB
            index_of_authorities = []
            for auth in db_authorities:
                auth_type = "rule"
                rn = auth["rule_number"] or ""
                if "MCL" in rn:
                    auth_type = "statute"
                elif "MCR" not in rn and "MRE" not in rn:
                    auth_type = "case"
                index_of_authorities.append({
                    "authority": f"{rn} — {auth['title']}",
                    "pages": "",
                    "type": auth_type,
                })

            # Build arguments from issues
            brief_arguments = list(arguments or [])
            if not brief_arguments and issues:
                for issue in issues:
                    matching = [a for a in db_authorities
                                if issue.lower().split()[0] in (a["title"] or "").lower()]
                    if matching:
                        a = matching[0]
                        brief_arguments.append({
                            "issue": issue,
                            "rule": f"{a['rule_number']}: {a['text'][:300]}",
                            "application": f"The trial court erred in its application of {a['rule_number']}.",
                            "conclusion": "This Court should reverse.",
                        })
                    else:
                        brief_arguments.append({
                            "issue": issue,
                            "rule": "[Governing authority — to be supplemented]",
                            "application": "[Application to facts of this case]",
                            "conclusion": "This Court should reverse.",
                        })

            # Alienation in appellate context
            if self._should_inject_alienation(lane, topic):
                brief_arguments.append(self._build_alienation_argument())
                for a in ALIENATION_AUTHORITY:
                    index_of_authorities.append({
                        "authority": a, "pages": "", "type": "statute",
                    })

            document = brief_template(
                lane=template_lane,
                questions_presented=issues,
                statement_of_facts=facts,
                arguments=brief_arguments if brief_arguments else None,
                index_of_authorities=index_of_authorities if index_of_authorities else None,
                standard_of_review=standard_of_review,
            )

            return {
                "ok": True,
                "document": document,
                "metadata": {
                    "document_type": "brief",
                    "lane": lane.upper(),
                    "lane_description": LANE_DESCRIPTIONS.get(lane.upper(), ""),
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "issue_count": len(issues or []),
                    "argument_count": len(brief_arguments),
                    "authority_count": len(index_of_authorities),
                },
                "db_context": {
                    "authorities_found": len(db_authorities),
                    "evidence_found": len(db_evidence),
                },
                "errors": [e["msg"] for e in self._error_log[-5:]],
            }

        except Exception as e:
            self._log_error("generate_brief", str(e))
            return {"ok": False, "error": str(e), "document": ""}

    def generate_affidavit(
        self,
        facts: Optional[List[str]] = None,
        declarant: str = "Andrew Pigors",
        lane: str = "A",
    ) -> Dict[str, Any]:
        """Generate an affidavit with DB-enriched factual statements."""
        try:
            template_lane = LANE_MAP.get(lane.upper(), "MEEK2")

            # Enrich facts from evidence_quotes
            fact_list = list(facts or [])
            if facts:
                topic = " OR ".join(w for f in facts[:3] for w in f.split()[:3])
                db_evidence = self._query_evidence(topic)
                for ev in db_evidence[:3]:
                    ev_fact = (f"Based on my personal knowledge and records, "
                               f"{ev['quote_text'][:200]}")
                    if ev_fact not in fact_list:
                        fact_list.append(ev_fact)
            else:
                db_evidence = []

            # Always include personal knowledge statement first
            if fact_list and not any("personal knowledge" in f.lower() for f in fact_list[:1]):
                fact_list.insert(0,
                    "I am the Plaintiff in the above-captioned matter and I make "
                    "this Affidavit based upon my own personal knowledge.")

            document = affidavit_template(
                lane=template_lane,
                statements=fact_list if fact_list else None,
                affiant=declarant,
            )

            return {
                "ok": True,
                "document": document,
                "metadata": {
                    "document_type": "affidavit",
                    "lane": lane.upper(),
                    "declarant": declarant,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "statement_count": len(fact_list),
                },
                "db_context": {"evidence_found": len(db_evidence)},
                "errors": [e["msg"] for e in self._error_log[-5:]],
            }

        except Exception as e:
            self._log_error("generate_affidavit", str(e))
            return {"ok": False, "error": str(e), "document": ""}

    def generate_response(
        self,
        opposing_motion: str,
        counter_arguments: Optional[List[Dict[str, str]]] = None,
        lane: str = "A",
        facts: Optional[List[str]] = None,
        relief: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a response to opposing party's motion."""
        try:
            template_lane = LANE_MAP.get(lane.upper(), "MEEK2")

            db_authorities = self._query_authorities(opposing_motion)
            db_evidence = self._query_evidence(opposing_motion)

            # Build response arguments
            resp_arguments = list(counter_arguments or [])
            if not resp_arguments:
                for auth in db_authorities[:3]:
                    resp_arguments.append({
                        "issue": f"Defendant's claims fail under {auth['rule_number']}",
                        "rule": f"{auth['rule_number']}: {auth['text'][:300]}",
                        "application": (f"Defendant's {opposing_motion} misapplies "
                                        f"{auth['rule_number']} to the facts of this case."),
                        "conclusion": f"Defendant's {opposing_motion} should be denied.",
                    })

            # Alienation counter-argument
            if self._should_inject_alienation(lane, opposing_motion):
                resp_arguments.append(self._build_alienation_argument())

            document = response_template(
                lane=template_lane,
                responding_to=opposing_motion,
                statement_of_facts=facts,
                arguments=resp_arguments if resp_arguments else None,
                relief_requested=relief,
            )

            return {
                "ok": True,
                "document": document,
                "metadata": {
                    "document_type": "response",
                    "lane": lane.upper(),
                    "responding_to": opposing_motion,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "argument_count": len(resp_arguments),
                },
                "db_context": {
                    "authorities_found": len(db_authorities),
                    "evidence_found": len(db_evidence),
                },
                "errors": [e["msg"] for e in self._error_log[-5:]],
            }

        except Exception as e:
            self._log_error("generate_response", str(e))
            return {"ok": False, "error": str(e), "document": ""}

    def list_templates(self) -> Dict[str, Any]:
        """List all available document templates and lanes."""
        try:
            return {
                "ok": True,
                "templates": list(TEMPLATES.keys()),
                "lanes": LANE_DESCRIPTIONS,
                "lane_map": LANE_MAP,
                "alienation_authority": ALIENATION_AUTHORITY,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def status(self) -> Dict[str, Any]:
        """System health check."""
        db_ok = False
        try:
            conn = self._get_db()
            if conn:
                conn.execute("SELECT 1")
                db_ok = True
        except Exception:
            pass

        return {
            "ok": True,
            "db_connected": db_ok,
            "db_path": DB_PATH,
            "templates_available": list(TEMPLATES.keys()),
            "error_count": len(self._error_log),
            "recent_errors": [e["msg"] for e in self._error_log[-3:]],
        }


# ── JSON-RPC Pipe Mode ────────────────────────────────────────────────

def _handle_rpc(gen: DocumentGenerator, request: Dict) -> Dict:
    """Handle a single JSON-RPC request."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id", None)

    dispatch = {
        "generate_motion": lambda p: gen.generate_motion(
            topic=p.get("topic", ""),
            facts=p.get("facts"),
            lane=p.get("lane", "A"),
            authority_list=p.get("authority_list"),
            relief=p.get("relief"),
        ),
        "generate_brief": lambda p: gen.generate_brief(
            issues=p.get("issues"),
            arguments=p.get("arguments"),
            lane=p.get("lane", "F"),
            facts=p.get("facts"),
            standard_of_review=p.get("standard_of_review", ""),
        ),
        "generate_affidavit": lambda p: gen.generate_affidavit(
            facts=p.get("facts"),
            declarant=p.get("declarant", "Andrew Pigors"),
            lane=p.get("lane", "A"),
        ),
        "generate_response": lambda p: gen.generate_response(
            opposing_motion=p.get("opposing_motion", ""),
            counter_arguments=p.get("counter_arguments"),
            lane=p.get("lane", "A"),
            facts=p.get("facts"),
            relief=p.get("relief"),
        ),
        "list_templates": lambda p: gen.list_templates(),
        "status": lambda p: gen.status(),
    }

    handler = dispatch.get(method)
    if not handler:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    try:
        result = handler(params)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": str(e)[:500]},
        }


def _run_pipe(gen: DocumentGenerator):
    """Run JSON-RPC pipe mode — reads JSON from stdin, writes to stdout."""
    cycle_print("[DocGen] JSON-RPC pipe mode ready. Send JSON requests on stdin.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = _handle_rpc(gen, request)
            cycle_json(response)
        except json.JSONDecodeError as e:
            cycle_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            })
        except Exception as e:
            cycle_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(e)[:500]},
            })


# ── CLI ────────────────────────────────────────────────────────────────

def _cli():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MBP LitigationOS — AI Document Generator"
    )
    parser.add_argument("--pipe", action="store_true",
                        help="JSON-RPC pipe mode for Electron integration")
    parser.add_argument("command", nargs="?", default="status",
                        choices=["motion", "brief", "affidavit", "response",
                                 "templates", "status", "selftest"],
                        help="Document type to generate")
    parser.add_argument("--topic", default="Discovery Compliance",
                        help="Motion/document topic")
    parser.add_argument("--lane", default="A",
                        help="Case lane (A-F)")
    parser.add_argument("--facts", nargs="*",
                        help="List of facts")
    parser.add_argument("--issues", nargs="*",
                        help="List of issues (for briefs)")
    parser.add_argument("--opposing", default="",
                        help="Opposing motion title (for responses)")

    args = parser.parse_args()
    gen = DocumentGenerator()

    if args.pipe:
        _run_pipe(gen)
        return

    if args.command == "status":
        cycle_json(gen.status(), pretty=True)
    elif args.command == "templates":
        cycle_json(gen.list_templates(), pretty=True)
    elif args.command == "motion":
        result = gen.generate_motion(
            topic=args.topic, facts=args.facts, lane=args.lane,
        )
        cycle_json(result, pretty=True)
    elif args.command == "brief":
        result = gen.generate_brief(
            issues=args.issues, lane=args.lane,
        )
        cycle_json(result, pretty=True)
    elif args.command == "affidavit":
        result = gen.generate_affidavit(
            facts=args.facts, lane=args.lane,
        )
        cycle_json(result, pretty=True)
    elif args.command == "response":
        result = gen.generate_response(
            opposing_motion=args.opposing or "Motion", lane=args.lane,
        )
        cycle_json(result, pretty=True)
    elif args.command == "selftest":
        _selftest(gen)


def _selftest(gen: DocumentGenerator):
    """Self-test: exercise all generation functions."""
    cycle_print("[DocGen] Self-test starting...")
    tests_passed = 0
    tests_failed = 0

    # Test 1: Status
    try:
        result = gen.status()
        assert result["ok"], "Status check failed"
        cycle_print(f"  [PASS] status — db_connected={result['db_connected']}")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] status — {e}")
        tests_failed += 1

    # Test 2: List templates
    try:
        result = gen.list_templates()
        assert result["ok"], "list_templates failed"
        assert len(result["templates"]) >= 5, f"Expected >=5 templates, got {len(result['templates'])}"
        cycle_print(f"  [PASS] list_templates — {len(result['templates'])} templates")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] list_templates — {e}")
        tests_failed += 1

    # Test 3: Generate motion
    try:
        result = gen.generate_motion(
            topic="Discovery Compliance",
            facts=["Defendant failed to respond to interrogatories within 28 days per MCR 2.309(B)."],
            lane="A",
        )
        assert result["ok"], f"generate_motion failed: {result.get('error')}"
        assert len(result["document"]) > 200, "Document too short"
        assert "PLAINTIFF" in result["document"], "Missing caption"
        cycle_print(f"  [PASS] generate_motion — {len(result['document'])} chars, "
                    f"{result['metadata']['authority_count']} authorities")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] generate_motion — {e}")
        tests_failed += 1

    # Test 4: Generate brief
    try:
        result = gen.generate_brief(
            issues=["Whether the trial court erred in denying parenting time"],
            lane="F",
        )
        assert result["ok"], f"generate_brief failed: {result.get('error')}"
        assert "APPELLANT" in result["document"], "Missing appellate caption"
        cycle_print(f"  [PASS] generate_brief — {len(result['document'])} chars")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] generate_brief — {e}")
        tests_failed += 1

    # Test 5: Generate affidavit
    try:
        result = gen.generate_affidavit(
            facts=["I have been denied parenting time for 329+ days."],
            declarant="Andrew Pigors",
            lane="A",
        )
        assert result["ok"], f"generate_affidavit failed: {result.get('error')}"
        assert "AFFIDAVIT" in result["document"]
        cycle_print(f"  [PASS] generate_affidavit — {len(result['document'])} chars")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] generate_affidavit — {e}")
        tests_failed += 1

    # Test 6: Generate response
    try:
        result = gen.generate_response(
            opposing_motion="Motion to Dismiss",
            lane="A",
        )
        assert result["ok"], f"generate_response failed: {result.get('error')}"
        assert "RESPONSE" in result["document"]
        cycle_print(f"  [PASS] generate_response — {len(result['document'])} chars")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] generate_response — {e}")
        tests_failed += 1

    # Test 7: Alienation injection
    try:
        result = gen.generate_motion(
            topic="Custody Modification", facts=["Child separation ongoing."], lane="A",
        )
        assert result["ok"]
        assert result["metadata"]["alienation_injected"], "Alienation not injected for custody motion"
        assert "722.23(j)" in result["document"], "MCL 722.23(j) not in document"
        cycle_print(f"  [PASS] alienation_injection — theme present in custody motion")
        tests_passed += 1
    except Exception as e:
        cycle_print(f"  [FAIL] alienation_injection — {e}")
        tests_failed += 1

    cycle_print(f"\n[DocGen] Self-test complete: {tests_passed} passed, {tests_failed} failed")


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    _cli()
