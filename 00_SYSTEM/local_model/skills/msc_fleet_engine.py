#!/usr/bin/env python3
"""
MSC Fleet Engine — Supreme Court Action Intelligence
=====================================================
Provides methods for MSC original action evidence mapping, element checking,
and filing assembly. Function-based skill for THE MANBEARPIG LitigationOS.

JSON-RPC methods: msc_element_check, msc_evidence_map, msc_filing_assemble,
msc_compliance_validate, msc_fleet_status, msc_cross_reference, msc_rank_actions,
msc_exhaustion_check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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

MSC_FLEET_DIR = os.environ.get(
    "MSC_FLEET_DIR",
    r"C:\Users\andre\LitigationOS\MSC_FLEET",
)

# ── 10 MSC Original Actions ────────────────────────────────────────────────
MSC_ACTIONS: Dict[str, Dict[str, Any]] = {
    "superintending_control": {
        "label": "Superintending Control",
        "authority": "MCR 7.306; Const 1963 art 6 § 4",
        "file_pattern": "01_SUPERINTENDING_CONTROL_EVIDENCE",
        "viability": 5,
        "elements": [
            "lower court exceeded jurisdiction or acted contrary to law",
            "no adequate legal remedy available",
            "clear legal right to relief",
            "clear legal duty by respondent",
        ],
    },
    "mandamus": {
        "label": "Mandamus",
        "authority": "MCR 7.306",
        "file_pattern": "02_MANDAMUS_EVIDENCE",
        "viability": 5,
        "elements": [
            "clear legal right to performance of duty",
            "clear legal duty by respondent",
            "no other adequate legal remedy",
        ],
    },
    "habeas_corpus": {
        "label": "Habeas Corpus",
        "authority": "Const 1963 art 1 § 12; MCL 600.4301",
        "file_pattern": "03_HABEAS_CORPUS_EVIDENCE",
        "viability": 4,
        "elements": [
            "unlawful restraint of liberty or custody",
            "deprivation without due process",
            "no adequate alternative remedy",
        ],
    },
    "prohibition": {
        "label": "Prohibition",
        "authority": "MCR 7.306",
        "file_pattern": "04_PROHIBITION_EVIDENCE",
        "viability": 4,
        "elements": [
            "lower court about to exceed jurisdiction",
            "no adequate legal remedy",
            "irreparable harm if not stayed",
        ],
    },
    "emergency_application": {
        "label": "Emergency Application",
        "authority": "MCR 7.305(F); MCR 7.315(C)",
        "file_pattern": "05_EMERGENCY_APPLICATION_EVIDENCE",
        "viability": 5,
        "elements": [
            "immediate and irreparable harm",
            "likelihood of success on merits",
            "urgency that precludes normal briefing",
        ],
    },
    "declaratory_judgment": {
        "label": "Declaratory Judgment",
        "authority": "MCL 600.605; MCR 2.605",
        "file_pattern": "06_DECLARATORY_JUDGMENT_EVIDENCE",
        "viability": 4,
        "elements": [
            "actual controversy between parties",
            "adverse legal interests",
            "declaration will resolve controversy",
        ],
    },
    "leave_to_appeal": {
        "label": "Leave to Appeal (bypass COA)",
        "authority": "MCR 7.305(B)(2)",
        "file_pattern": "07_LEAVE_TO_APPEAL_BYPASS_EVIDENCE",
        "viability": 3,
        "elements": [
            "issue of significant public interest",
            "COA decision conflicts with MSC precedent",
            "need for immediate MSC review",
        ],
    },
    "quo_warranto": {
        "label": "Quo Warranto",
        "authority": "MCL 600.4501",
        "file_pattern": "08_QUO_WARRANTO_EVIDENCE",
        "viability": 2,
        "elements": [
            "usurpation of public office or authority",
            "lack of legal authority for actions taken",
        ],
    },
    "federal_1983": {
        "label": "42 USC § 1983",
        "authority": "28 USC § 1343",
        "file_pattern": "09_FEDERAL_1983_EVIDENCE",
        "viability": 4,
        "elements": [
            "action under color of state law",
            "deprivation of constitutional right",
            "causation between action and injury",
            "no adequate state remedy",
        ],
    },
    "jtc_complaint": {
        "label": "JTC Complaint",
        "authority": "MCR 9.200-9.252",
        "file_pattern": "10_JTC_COMPLAINT_EVIDENCE",
        "viability": 5,
        "elements": [
            "judicial misconduct or disability",
            "specific canon violations with dates",
            "pattern of conduct",
            "harm to litigant or public confidence",
        ],
    },
}


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


def _safe_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict]:
    """Execute a query and return list of dicts, empty list on error."""
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ── 1. msc_element_check ───────────────────────────────────────────────────

def msc_element_check(action_type: str) -> Dict[str, Any]:
    """Check if all required legal elements for an MSC action have supporting evidence.

    Queries judicial_violations, evidence_quotes, and claims to find
    evidence supporting each element of the given action type.
    """
    if action_type not in MSC_ACTIONS:
        return {"error": f"Unknown action: {action_type}", "valid_actions": list(MSC_ACTIONS.keys())}

    action = MSC_ACTIONS[action_type]
    conn = _get_db()
    if not conn:
        return {"error": "Database unavailable"}

    results: Dict[str, Any] = {
        "action_type": action_type,
        "label": action["label"],
        "authority": action["authority"],
        "elements": [],
        "all_elements_met": True,
        "summary": "",
    }

    for element in action["elements"]:
        element_result: Dict[str, Any] = {
            "element": element,
            "supported": False,
            "evidence_count": 0,
            "sources": [],
        }
        keywords = [w for w in element.split() if len(w) > 3]
        like_pat = f"%{'%'.join(keywords[:4])}%"

        # Check judicial_violations
        violations = _safe_query(
            conn,
            "SELECT violation_id, violation_description, severity "
            "FROM judicial_violations WHERE violation_description LIKE ? LIMIT 5",
            (like_pat,),
        )
        if violations:
            element_result["sources"].append({"table": "judicial_violations", "count": len(violations),
                                               "samples": [v["violation_description"][:200] for v in violations[:3]]})
            element_result["evidence_count"] += len(violations)

        # Check evidence_quotes
        evidence = _safe_query(
            conn,
            "SELECT quote_text, speaker, legal_significance "
            "FROM evidence_quotes WHERE quote_text LIKE ? OR legal_significance LIKE ? LIMIT 5",
            (like_pat, like_pat),
        )
        if evidence:
            element_result["sources"].append({"table": "evidence_quotes", "count": len(evidence),
                                               "samples": [e["quote_text"][:200] for e in evidence[:3]]})
            element_result["evidence_count"] += len(evidence)

        # Check claims
        claims = _safe_query(
            conn,
            "SELECT claim_id, proposition, status "
            "FROM claims WHERE proposition LIKE ? AND status = 'supported' LIMIT 5",
            (like_pat,),
        )
        if claims:
            element_result["sources"].append({"table": "claims", "count": len(claims),
                                               "samples": [c["proposition"][:200] for c in claims[:3]]})
            element_result["evidence_count"] += len(claims)

        element_result["supported"] = element_result["evidence_count"] > 0
        if not element_result["supported"]:
            results["all_elements_met"] = False

        results["elements"].append(element_result)

    conn.close()

    met = sum(1 for e in results["elements"] if e["supported"])
    total = len(results["elements"])
    results["summary"] = f"{met}/{total} elements supported for {action['label']}"
    return results


# ── 2. msc_evidence_map ───────────────────────────────────────────────────

def msc_evidence_map(action_type: str) -> Dict[str, Any]:
    """Map all evidence to the elements of a specific MSC action.

    Returns structured dict with evidence mapped per element including
    judicial violations, evidence quotes, and claims.
    """
    if action_type not in MSC_ACTIONS:
        return {"error": f"Unknown action: {action_type}", "valid_actions": list(MSC_ACTIONS.keys())}

    action = MSC_ACTIONS[action_type]
    conn = _get_db()
    if not conn:
        return {"error": "Database unavailable"}

    result: Dict[str, Any] = {
        "action_type": action_type,
        "label": action["label"],
        "authority": action["authority"],
        "evidence_map": {},
        "total_evidence_items": 0,
    }

    # Check for MSC fleet evidence file
    fleet_file = None
    for ext in [".md", ".json", "_full.json"]:
        candidate = os.path.join(MSC_FLEET_DIR, action["file_pattern"] + ext)
        if os.path.isfile(candidate):
            fleet_file = candidate
            break
    result["fleet_evidence_file"] = fleet_file
    result["fleet_file_exists"] = fleet_file is not None

    for element in action["elements"]:
        keywords = [w for w in element.split() if len(w) > 3]
        search_terms = " ".join(keywords[:4])
        like_pat = f"%{search_terms}%"

        mapped: Dict[str, Any] = {
            "element": element,
            "judicial_violations": [],
            "evidence_quotes": [],
            "claims": [],
        }

        # Judicial violations
        for v in _safe_query(
            conn,
            "SELECT violation_id, judge_name, canon_number, violation_description, "
            "severity, evidence_refs FROM judicial_violations "
            "WHERE violation_description LIKE ? LIMIT 10",
            (like_pat,),
        ):
            mapped["judicial_violations"].append(v)

        # Evidence quotes (FTS with fallback)
        eq_rows = _safe_query(
            conn,
            "SELECT rowid, quote_text, speaker, legal_significance, evidence_category "
            "FROM evidence_quotes WHERE rowid IN "
            "(SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?) LIMIT 10",
            (search_terms,),
        )
        if not eq_rows:
            eq_rows = _safe_query(
                conn,
                "SELECT rowid, quote_text, speaker, legal_significance, evidence_category "
                "FROM evidence_quotes WHERE quote_text LIKE ? OR legal_significance LIKE ? LIMIT 10",
                (like_pat, like_pat),
            )
        for e in eq_rows:
            mapped["evidence_quotes"].append(e)

        # Claims
        for c in _safe_query(
            conn,
            "SELECT claim_id, proposition, status, actor "
            "FROM claims WHERE proposition LIKE ? LIMIT 10",
            (like_pat,),
        ):
            mapped["claims"].append(c)

        item_count = len(mapped["judicial_violations"]) + len(mapped["evidence_quotes"]) + len(mapped["claims"])
        result["total_evidence_items"] += item_count
        result["evidence_map"][element] = mapped

    conn.close()
    return result


# ── 3. msc_filing_assemble ────────────────────────────────────────────────

def msc_filing_assemble(action_types: List[str]) -> Dict[str, Any]:
    """Given a list of action types, identify evidence packages and filing readiness.

    Checks MSC_FLEET directory for evidence files and filing_readiness DB table
    for assembly scores. Returns an assembly plan.
    """
    conn = _get_db()
    plan: Dict[str, Any] = {
        "requested_actions": action_types,
        "assembly_plan": [],
        "missing_actions": [],
        "fleet_dir": MSC_FLEET_DIR,
        "fleet_dir_exists": os.path.isdir(MSC_FLEET_DIR),
    }

    for at in action_types:
        if at not in MSC_ACTIONS:
            plan["missing_actions"].append(at)
            continue

        action = MSC_ACTIONS[at]
        entry: Dict[str, Any] = {
            "action_type": at,
            "label": action["label"],
            "authority": action["authority"],
            "evidence_files": [],
            "filing_readiness": None,
            "msc_tracker": None,
        }

        # Find evidence files in MSC_FLEET
        if os.path.isdir(MSC_FLEET_DIR):
            for f in os.listdir(MSC_FLEET_DIR):
                if action["file_pattern"].lower() in f.lower():
                    fpath = os.path.join(MSC_FLEET_DIR, f)
                    entry["evidence_files"].append({
                        "filename": f,
                        "path": fpath,
                        "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                    })

        # Check filing_readiness
        if conn:
            rows = _safe_query(
                conn,
                "SELECT vehicle_name, authority_score, evidence_score, compliance_score, "
                "total_score, gaps, status FROM filing_readiness "
                "WHERE vehicle_name LIKE ? LIMIT 3",
                (f"%{action['label'].split()[0]}%",),
            )
            if rows:
                entry["filing_readiness"] = rows[0]

            # Check msc_filing_tracker
            tracker = _safe_query(
                conn,
                "SELECT document_name, status, word_count, citation_count, notes "
                "FROM msc_filing_tracker WHERE document_name LIKE ? LIMIT 3",
                (f"%{action['label'].split()[0]}%",),
            )
            if tracker:
                entry["msc_tracker"] = tracker[0]

        plan["assembly_plan"].append(entry)

    if conn:
        conn.close()
    return plan


# ── 4. msc_compliance_validate ────────────────────────────────────────────

def msc_compliance_validate(filing_path: str) -> Dict[str, Any]:
    """Run MCR 7.306 compliance checks on a filing.

    Checks for: caption, numbered paragraphs, signature block,
    Certificate of Service, proper formatting.
    """
    result: Dict[str, Any] = {
        "filing_path": filing_path,
        "exists": os.path.isfile(filing_path),
        "checks": [],
        "score": 0,
        "total_checks": 0,
        "passed": 0,
        "mcr_rule": "MCR 7.306",
    }

    if not result["exists"]:
        result["checks"].append({"check": "file_exists", "passed": False, "detail": "Filing file not found"})
        return result

    try:
        with open(filing_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        result["checks"].append({"check": "file_readable", "passed": False, "detail": str(e)})
        return result

    upper = content.upper()

    # 1. Caption check
    has_caption = any(kw in upper for kw in ["STATE OF MICHIGAN", "SUPREME COURT", "COURT OF APPEALS",
                                              "CIRCUIT COURT", "IN THE", "CASE NO"])
    result["checks"].append({"check": "caption_present", "passed": has_caption,
                              "detail": "Caption block detected" if has_caption else "No caption found — MCR 7.306(B)"})

    # 2. Numbered paragraphs
    numbered = len(re.findall(r'^\s*\d+\.\s+', content, re.MULTILINE))
    has_numbered = numbered >= 3
    result["checks"].append({"check": "numbered_paragraphs", "passed": has_numbered,
                              "detail": f"Found {numbered} numbered paragraphs" if has_numbered else
                              "Insufficient numbered paragraphs — MCR 2.113(A)"})

    # 3. Signature block
    has_sig = any(kw in content for kw in ["Respectfully submitted", "respectfully submitted",
                                            "/s/", "___________", "Pro Se", "pro se"])
    result["checks"].append({"check": "signature_block", "passed": has_sig,
                              "detail": "Signature block found" if has_sig else "Missing signature block — MCR 2.114"})

    # 4. Certificate of Service
    has_cos = "CERTIFICATE OF SERVICE" in upper or "PROOF OF SERVICE" in upper
    result["checks"].append({"check": "certificate_of_service", "passed": has_cos,
                              "detail": "Certificate of Service present" if has_cos else
                              "Missing Certificate of Service — MCR 2.107"})

    # 5. Authority citations
    cite_count = len(re.findall(r'(MCR|MCL|MRE|Const|USC)\s+\d', content))
    has_cites = cite_count >= 2
    result["checks"].append({"check": "authority_citations", "passed": has_cites,
                              "detail": f"Found {cite_count} authority citations" if has_cites else
                              "Insufficient authority citations"})

    # 6. Relief requested
    has_relief = any(kw in upper for kw in ["WHEREFORE", "RELIEF REQUESTED", "PRAYER FOR RELIEF",
                                             "RESPECTFULLY REQUESTS", "THIS COURT SHOULD"])
    result["checks"].append({"check": "relief_requested", "passed": has_relief,
                              "detail": "Relief/prayer section found" if has_relief else "No relief requested section"})

    # 7. Word count (MSC briefs typically capped)
    word_count = len(content.split())
    result["checks"].append({"check": "word_count", "passed": True,
                              "detail": f"Word count: {word_count}"})

    # 8. Placeholder check
    placeholders = re.findall(r'\[(?:DATE|NAME|CASE NUMBER|ADDRESS|SPECIFY|COURT|JUDGE)[^\]]*\]', content, re.IGNORECASE)
    no_placeholders = len(placeholders) == 0
    result["checks"].append({"check": "no_placeholders", "passed": no_placeholders,
                              "detail": "No placeholders found" if no_placeholders else
                              f"Found {len(placeholders)} unresolved placeholder(s): {', '.join(placeholders[:5])}"})

    result["total_checks"] = len(result["checks"])
    result["passed"] = sum(1 for c in result["checks"] if c["passed"])
    result["score"] = round((result["passed"] / result["total_checks"]) * 100) if result["total_checks"] else 0
    return result


# ── 5. msc_fleet_status ──────────────────────────────────────────────────

def msc_fleet_status() -> Dict[str, Any]:
    """Return status of all 10 MSC fleet evidence packages.

    Checks file existence, size, and filing_readiness scores.
    """
    conn = _get_db()
    status: Dict[str, Any] = {
        "fleet_dir": MSC_FLEET_DIR,
        "fleet_dir_exists": os.path.isdir(MSC_FLEET_DIR),
        "actions": [],
        "total_files_found": 0,
        "actions_with_evidence": 0,
    }

    for action_type, action in MSC_ACTIONS.items():
        entry: Dict[str, Any] = {
            "action_type": action_type,
            "label": action["label"],
            "authority": action["authority"],
            "viability": action["viability"],
            "files": [],
            "filing_readiness_score": None,
            "legal_action_score": None,
        }

        # Find fleet files
        if os.path.isdir(MSC_FLEET_DIR):
            for f in os.listdir(MSC_FLEET_DIR):
                if action["file_pattern"].lower() in f.lower():
                    fpath = os.path.join(MSC_FLEET_DIR, f)
                    entry["files"].append({
                        "filename": f,
                        "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                    })
                    status["total_files_found"] += 1

        if entry["files"]:
            status["actions_with_evidence"] += 1

        # filing_readiness score
        if conn:
            fr = _safe_query(
                conn,
                "SELECT total_score, status, gaps FROM filing_readiness "
                "WHERE vehicle_name LIKE ? LIMIT 1",
                (f"%{action['label'].split()[0]}%",),
            )
            if fr:
                entry["filing_readiness_score"] = fr[0].get("total_score")

            # legal_action_scores
            la = _safe_query(
                conn,
                "SELECT overall_score, evidence_score, authority_score, compliance_score "
                "FROM legal_action_scores WHERE action_name LIKE ? LIMIT 1",
                (f"%{action['label'].split()[0]}%",),
            )
            if la:
                entry["legal_action_score"] = la[0]

        status["actions"].append(entry)

    if conn:
        conn.close()
    return status


# ── 6. msc_cross_reference ───────────────────────────────────────────────

def msc_cross_reference() -> Dict[str, Any]:
    """Read CROSS_REFERENCE_MATRIX.md and return structured data.

    Parses the cross-reference matrix linking MSC actions to shared evidence.
    """
    matrix_path = os.path.join(MSC_FLEET_DIR, "CROSS_REFERENCE_MATRIX.md")
    result: Dict[str, Any] = {
        "matrix_path": matrix_path,
        "exists": os.path.isfile(matrix_path),
        "sections": [],
        "raw_length": 0,
    }

    if not result["exists"]:
        return result

    try:
        with open(matrix_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        result["raw_length"] = len(content)

        # Parse markdown sections
        current_section = None
        current_content: List[str] = []
        for line in content.split("\n"):
            if line.startswith("#"):
                if current_section:
                    result["sections"].append({
                        "heading": current_section,
                        "content": "\n".join(current_content).strip(),
                    })
                current_section = line.lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            result["sections"].append({
                "heading": current_section,
                "content": "\n".join(current_content).strip(),
            })

        # Extract cross-references (table rows with pipes)
        table_rows = re.findall(r'^\|(.+)\|$', content, re.MULTILINE)
        if table_rows:
            result["table_row_count"] = len(table_rows)

    except Exception as e:
        result["error"] = str(e)

    return result


# ── 7. msc_rank_actions ──────────────────────────────────────────────────

def msc_rank_actions() -> Dict[str, Any]:
    """Return ranked list of MSC actions by composite viability score.

    Combines base viability rating with DB-sourced filing_readiness and
    legal_action_scores for a composite ranking.
    """
    conn = _get_db()
    rankings: List[Dict[str, Any]] = []

    for action_type, action in MSC_ACTIONS.items():
        entry: Dict[str, Any] = {
            "action_type": action_type,
            "label": action["label"],
            "authority": action["authority"],
            "base_viability": action["viability"],
            "filing_readiness_score": 0.0,
            "legal_action_score": 0.0,
            "evidence_file_exists": False,
            "composite_score": 0.0,
        }

        # Check file
        if os.path.isdir(MSC_FLEET_DIR):
            for f in os.listdir(MSC_FLEET_DIR):
                if action["file_pattern"].lower() in f.lower():
                    entry["evidence_file_exists"] = True
                    break

        if conn:
            fr = _safe_query(
                conn,
                "SELECT total_score FROM filing_readiness WHERE vehicle_name LIKE ? LIMIT 1",
                (f"%{action['label'].split()[0]}%",),
            )
            if fr and fr[0].get("total_score"):
                try:
                    entry["filing_readiness_score"] = float(fr[0]["total_score"])
                except (ValueError, TypeError):
                    pass

            la = _safe_query(
                conn,
                "SELECT overall_score FROM legal_action_scores WHERE action_name LIKE ? LIMIT 1",
                (f"%{action['label'].split()[0]}%",),
            )
            if la and la[0].get("overall_score"):
                try:
                    entry["legal_action_score"] = float(la[0]["overall_score"])
                except (ValueError, TypeError):
                    pass

        # Composite: base viability (0-5 → 0-50) + filing_readiness (0-25) + legal_action (0-25)
        entry["composite_score"] = round(
            (entry["base_viability"] * 10)
            + (entry["filing_readiness_score"] * 0.25)
            + (entry["legal_action_score"] * 0.25),
            2,
        )
        rankings.append(entry)

    if conn:
        conn.close()

    rankings.sort(key=lambda x: x["composite_score"], reverse=True)
    return {
        "ranked_actions": rankings,
        "top_action": rankings[0] if rankings else None,
        "total_actions": len(rankings),
    }


# ── 8. msc_exhaustion_check ─────────────────────────────────────────────

def msc_exhaustion_check() -> Dict[str, Any]:
    """Check deadlines and docket_events for exhaustion of remedies status.

    MSC requires showing lower court remedies were exhausted or inadequate.
    Queries deadlines and docket_events to build the exhaustion picture.
    """
    conn = _get_db()
    if not conn:
        return {"error": "Database unavailable"}

    result: Dict[str, Any] = {
        "exhaustion_status": "checking",
        "trial_court_motions": [],
        "appellate_filings": [],
        "deadlines": [],
        "exhaustion_satisfied": False,
        "notes": [],
    }

    # Get docket events showing motions filed and denied
    trial_events = _safe_query(
        conn,
        "SELECT event_id, case_id, event_date_iso, title, event_type, summary "
        "FROM docket_events WHERE event_type IN ('motion_filed', 'motion_denied', "
        "'order_entered', 'motion', 'order') "
        "ORDER BY event_date_iso DESC LIMIT 50",
        (),
    )
    result["trial_court_motions"] = trial_events

    # Get appellate-related events
    appellate = _safe_query(
        conn,
        "SELECT event_id, case_id, event_date_iso, title, event_type, summary "
        "FROM docket_events WHERE title LIKE '%appeal%' OR title LIKE '%COA%' "
        "OR title LIKE '%Supreme%' OR event_type LIKE '%appeal%' "
        "ORDER BY event_date_iso DESC LIMIT 20",
        (),
    )
    result["appellate_filings"] = appellate

    # Get active deadlines
    deadlines = _safe_query(
        conn,
        "SELECT deadline_id, case_id, title, due_date_iso, basis, "
        "basis_authority, risk_if_missed, status "
        "FROM deadlines ORDER BY due_date_iso ASC LIMIT 30",
        (),
    )
    result["deadlines"] = deadlines

    # Check for motions that were denied (showing exhaustion)
    denied = _safe_query(
        conn,
        "SELECT COUNT(*) as cnt FROM docket_events "
        "WHERE event_type LIKE '%denied%' OR title LIKE '%denied%' "
        "OR summary LIKE '%denied%'",
        (),
    )
    denied_count = denied[0]["cnt"] if denied else 0

    # Check for ex parte orders (showing inadequacy of normal process)
    ex_parte = _safe_query(
        conn,
        "SELECT COUNT(*) as cnt FROM judicial_violations "
        "WHERE violation_description LIKE '%ex parte%'",
        (),
    )
    ex_parte_count = ex_parte[0]["cnt"] if ex_parte else 0

    result["denied_motions_count"] = denied_count
    result["ex_parte_violations_count"] = ex_parte_count

    # Exhaustion analysis
    if denied_count > 0 or ex_parte_count > 0:
        result["exhaustion_satisfied"] = True
        result["exhaustion_status"] = "satisfied"
        result["notes"].append(
            f"Exhaustion demonstrated: {denied_count} denied motions, "
            f"{ex_parte_count} ex parte violations showing inadequacy of lower court remedies."
        )
    else:
        result["exhaustion_status"] = "needs_review"
        result["notes"].append(
            "No denied motions or ex parte violations found in DB — verify "
            "exhaustion manually against docket."
        )

    if ex_parte_count >= 5:
        result["notes"].append(
            "STRONG: 5+ ex parte violations support argument that normal remedies "
            "are futile — Const 1963 art 6 § 4 superintending control warranted."
        )

    conn.close()
    return result


# ── CLI Interface ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MSC Fleet Engine — Supreme Court Action Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
  msc_element_check <action_type>     Check element support for an MSC action
  msc_evidence_map <action_type>      Map evidence to action elements
  msc_filing_assemble <action1,action2,...>  Assembly plan for actions
  msc_compliance_validate <filepath>  MCR 7.306 compliance check
  msc_fleet_status                    Status of all 10 MSC evidence packages
  msc_cross_reference                 Parse CROSS_REFERENCE_MATRIX.md
  msc_rank_actions                    Ranked MSC actions by viability
  msc_exhaustion_check                Exhaustion of remedies status

Action types: superintending_control, mandamus, habeas_corpus, prohibition,
  emergency_application, declaratory_judgment, leave_to_appeal,
  quo_warranto, federal_1983, jtc_complaint
""",
    )
    parser.add_argument("method", help="Method to execute")
    parser.add_argument("args", nargs="*", help="Method arguments")
    parser.add_argument("--json", action="store_true", default=True, help="JSON output (default)")

    args = parser.parse_args()
    method = args.method.lower()

    dispatch = {
        "msc_element_check": lambda: msc_element_check(args.args[0] if args.args else "superintending_control"),
        "msc_evidence_map": lambda: msc_evidence_map(args.args[0] if args.args else "superintending_control"),
        "msc_filing_assemble": lambda: msc_filing_assemble(args.args[0].split(",") if args.args else list(MSC_ACTIONS.keys())),
        "msc_compliance_validate": lambda: msc_compliance_validate(args.args[0] if args.args else ""),
        "msc_fleet_status": lambda: msc_fleet_status(),
        "msc_cross_reference": lambda: msc_cross_reference(),
        "msc_rank_actions": lambda: msc_rank_actions(),
        "msc_exhaustion_check": lambda: msc_exhaustion_check(),
    }

    if method not in dispatch:
        print(f"Unknown method: {method}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(dispatch.keys()))}", file=sys.stderr)
        sys.exit(1)

    result = dispatch[method]()
    cycle_json(result)


if __name__ == "__main__":
    main()
