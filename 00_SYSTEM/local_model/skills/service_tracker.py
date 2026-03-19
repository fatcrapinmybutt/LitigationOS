#!/usr/bin/env python3
"""
THE MANBEARPIG — EPOCH v8.0 — Service of Process Tracker
==========================================================
Multi-jurisdiction service compliance and proof tracking for
simultaneous filings across 5 forums: Circuit Court, COA, MSC, USDC, JTC.

Case: Andrew Pigors v. Tiffany Watson
Courts: 14th Circuit (Lane A/D), COA 366810 (Lane F), MSC (Lane G),
        USDC WD Mich (§1983), JTC (Lane E)
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
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

# ── Service Table DDL (created on first use if missing) ──────────────
_SERVICE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS service_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_name     TEXT NOT NULL,
    jurisdiction    TEXT NOT NULL,
    recipient       TEXT NOT NULL,
    method          TEXT NOT NULL,
    service_date    TEXT,
    proof_type      TEXT,
    proof_detail    TEXT,
    tracking_number TEXT,
    status          TEXT DEFAULT 'pending',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);
"""


def _get_db(read_only: bool = True) -> Optional[sqlite3.Connection]:
    """Get DB connection. read_only=False for writes to service_events."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        if read_only:
            conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _ensure_service_table(conn: sqlite3.Connection) -> bool:
    """Create service_events table if it does not exist."""
    try:
        conn.executescript(_SERVICE_TABLE_DDL)
        return True
    except Exception:
        return False


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sqlite_master "
            "WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return bool(row and row["cnt"] > 0)
    except Exception:
        return False


# ── Service Rules Per Jurisdiction ───────────────────────────────────
SERVICE_RULES: Dict[str, Dict[str, Any]] = {
    "circuit_court": {
        "rule": "MCR 2.107(C)",
        "methods": ["personal", "mail", "electronic"],
        "timing": "MCR 2.119(C)(1) — 9 days before hearing + 3 if mailed = 12 days min",
        "timing_days": 9,
        "mail_add_days": 3,
        "proof": "MCR 2.104 — Affidavit of Service or Acknowledgment",
        "parties": ["Tiffany Watson", "Jennifer Barnes (attorney)"],
    },
    "court_of_appeals": {
        "rule": "MCR 7.209(A)",
        "methods": ["mail", "electronic via TrueFiling"],
        "timing": "Same day as filing",
        "timing_days": 0,
        "mail_add_days": 0,
        "proof": "Certificate of Service attached to filing",
        "parties": ["Ron Berry (appellate counsel)", "Tiffany Watson"],
    },
    "supreme_court": {
        "rule": "MCR 7.305(A)",
        "methods": ["mail", "personal"],
        "timing": "Same day as filing",
        "timing_days": 0,
        "mail_add_days": 0,
        "proof": "Certificate of Service",
        "copies": 13,
        "parties": ["All parties of record", "Court of Appeals"],
    },
    "federal_court": {
        "rule": "FRCP 5(b)(2)",
        "methods": ["CM/ECF electronic", "mail", "personal"],
        "timing": "FRCP 5(d)(1) — reasonable time after service",
        "timing_days": 3,
        "mail_add_days": 3,
        "proof": "Certificate of Service per FRCP 5(d)(1)(B)",
        "parties": ["All defendants via registered agent"],
    },
    "jtc": {
        "rule": "MCR 9.220",
        "methods": ["mail to JTC office"],
        "timing": "Upon filing",
        "timing_days": 0,
        "mail_add_days": 0,
        "proof": "Certified mail receipt",
        "address": "3034 W. Grand Blvd, Suite 8-450, Detroit MI 48202",
        "parties": ["JTC only — no service on judge required"],
    },
}


class ServiceTracker:
    """Multi-forum service of process tracker with compliance checking."""

    def __init__(self):
        self._cache: Dict = {}

    # ── 1. Track Service ─────────────────────────────────────────────

    def track_service(self, params: Dict) -> Dict:
        """
        Record a service event.

        params:
            filing_name:     str — name of the filing (e.g. 'MSC Complaint Superintending Control')
            jurisdiction:    str — key from SERVICE_RULES
            method:          str — service method used
            recipient:       str — who was served
            date:            str — ISO date (YYYY-MM-DD), defaults to today
            proof_type:      str — type of proof (affidavit, certificate, receipt)
            proof_detail:    str — details (tracking number, etc.)
            tracking_number: str — optional mail tracking number
        """
        filing_name = params.get("filing_name", "").strip()
        jurisdiction = params.get("jurisdiction", "").strip().lower()
        method = params.get("method", "").strip()
        recipient = params.get("recipient", "").strip()
        service_date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        proof_type = params.get("proof_type", "")
        proof_detail = params.get("proof_detail", "")
        tracking_number = params.get("tracking_number", "")

        if not filing_name:
            return {"error": "filing_name is required"}
        if not jurisdiction:
            return {"error": "jurisdiction is required"}
        if jurisdiction not in SERVICE_RULES:
            return {
                "error": f"Unknown jurisdiction: {jurisdiction}",
                "valid_jurisdictions": list(SERVICE_RULES.keys()),
            }
        if not recipient:
            return {"error": "recipient is required"}

        rules = SERVICE_RULES[jurisdiction]
        method_valid = any(
            method.lower() in m.lower() for m in rules["methods"]
        )

        conn = _get_db(read_only=False)
        if not conn:
            return {"error": "Database connection failed"}

        _ensure_service_table(conn)

        try:
            conn.execute(
                "INSERT INTO service_events "
                "(filing_name, jurisdiction, recipient, method, service_date, "
                "proof_type, proof_detail, tracking_number, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    filing_name,
                    jurisdiction,
                    recipient,
                    method,
                    service_date,
                    proof_type,
                    proof_detail,
                    tracking_number,
                    "completed",
                ),
            )
            conn.commit()
            event_id = conn.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]
            conn.close()

            result: Dict[str, Any] = {
                "status": "recorded",
                "event_id": event_id,
                "filing_name": filing_name,
                "jurisdiction": jurisdiction,
                "recipient": recipient,
                "method": method,
                "service_date": service_date,
                "rule": rules["rule"],
            }
            if not method_valid:
                result["warning"] = (
                    f"Method '{method}' may not comply with {rules['rule']}. "
                    f"Accepted methods: {', '.join(rules['methods'])}"
                )
            return result

        except Exception as e:
            conn.close()
            return {"error": f"Failed to record service: {str(e)[:200]}"}

    # ── 2. Check Compliance ──────────────────────────────────────────

    def check_compliance(self, params: Dict) -> Dict:
        """
        Check if all required service has been completed for a filing.

        params:
            filing_name:  str — name of the filing
            jurisdiction: str — target jurisdiction (optional; checks all if omitted)
        """
        filing_name = params.get("filing_name", "").strip()
        target_jur = params.get("jurisdiction", "").strip().lower()

        if not filing_name:
            return {"error": "filing_name is required"}

        jurisdictions = (
            {target_jur: SERVICE_RULES[target_jur]}
            if target_jur and target_jur in SERVICE_RULES
            else SERVICE_RULES
        )

        conn = _get_db()
        if not conn:
            return {"error": "Database connection failed"}

        if not _table_exists(conn, "service_events"):
            conn.close()
            return self._build_compliance_from_rules(filing_name, jurisdictions, [])

        try:
            rows = conn.execute(
                "SELECT jurisdiction, recipient, method, service_date, "
                "proof_type, status FROM service_events "
                "WHERE filing_name = ? AND status = 'completed'",
                (filing_name,),
            ).fetchall()
            events = [dict(r) for r in rows]
            conn.close()
        except Exception:
            conn.close()
            events = []

        return self._build_compliance_from_rules(filing_name, jurisdictions, events)

    def _build_compliance_from_rules(
        self,
        filing_name: str,
        jurisdictions: Dict,
        events: List[Dict],
    ) -> Dict:
        """Build compliance report comparing rules to completed events."""
        results: Dict[str, Any] = {
            "filing_name": filing_name,
            "overall_compliant": True,
            "jurisdictions": {},
            "total_required": 0,
            "total_served": 0,
            "missing_service": [],
        }

        for jur_key, rules in jurisdictions.items():
            jur_events = [e for e in events if e["jurisdiction"] == jur_key]
            served_recipients = {e["recipient"].lower() for e in jur_events}

            required_parties = rules["parties"]
            missing = [
                p for p in required_parties
                if not any(p.lower() in sr for sr in served_recipients)
            ]

            has_valid_method = all(
                any(
                    m.lower() in am.lower()
                    for am in rules["methods"]
                )
                for e in jur_events
                for m in [e["method"]]
            ) if jur_events else False

            compliant = len(missing) == 0 and len(jur_events) > 0
            results["total_required"] += len(required_parties)
            results["total_served"] += len(required_parties) - len(missing)

            if not compliant:
                results["overall_compliant"] = False
                for p in missing:
                    results["missing_service"].append({
                        "jurisdiction": jur_key,
                        "party": p,
                        "required_methods": rules["methods"],
                        "rule": rules["rule"],
                    })

            results["jurisdictions"][jur_key] = {
                "compliant": compliant,
                "rule": rules["rule"],
                "required_parties": required_parties,
                "served_count": len(jur_events),
                "missing_parties": missing,
                "valid_method": has_valid_method,
                "proof_required": rules["proof"],
            }

        return results

    # ── 3. Generate Certificate of Service ───────────────────────────

    def generate_cos(self, params: Dict) -> Dict:
        """
        Generate Certificate of Service text for a specific filing/jurisdiction.

        params:
            filing_name:  str — name of the filing
            jurisdiction: str — target jurisdiction
            case_number:  str — case number (e.g. '2024-001507-DC')
            filing_date:  str — ISO date (defaults to today)
        """
        filing_name = params.get("filing_name", "").strip()
        jurisdiction = params.get("jurisdiction", "").strip().lower()
        case_number = params.get("case_number", "2024-001507-DC")
        filing_date = params.get(
            "filing_date", datetime.now().strftime("%Y-%m-%d")
        )

        if not filing_name:
            return {"error": "filing_name is required"}
        if jurisdiction not in SERVICE_RULES:
            return {
                "error": f"Unknown jurisdiction: {jurisdiction}",
                "valid_jurisdictions": list(SERVICE_RULES.keys()),
            }

        rules = SERVICE_RULES[jurisdiction]

        # Retrieve completed service events for this filing
        served_parties: List[Dict] = []
        conn = _get_db()
        if conn and _table_exists(conn, "service_events"):
            try:
                rows = conn.execute(
                    "SELECT recipient, method, service_date, proof_type "
                    "FROM service_events "
                    "WHERE filing_name = ? AND jurisdiction = ? "
                    "AND status = 'completed' "
                    "ORDER BY service_date",
                    (filing_name, jurisdiction),
                ).fetchall()
                served_parties = [dict(r) for r in rows]
            except Exception:
                pass
            conn.close()

        # Build COS text
        date_obj = datetime.strptime(filing_date, "%Y-%m-%d")
        date_formatted = date_obj.strftime("%B %d, %Y")

        lines = [
            "CERTIFICATE OF SERVICE",
            "",
            f"Case No. {case_number}",
            "",
            (
                f"I, Andrew Pigors, Plaintiff/Appellant, pro se, hereby certify "
                f"that on {date_formatted}, I served a true and correct copy of "
                f"the foregoing {filing_name} upon the following:"
            ),
            "",
        ]

        if served_parties:
            for sp in served_parties:
                lines.append(
                    f"  {sp['recipient']}\n"
                    f"    via {sp['method']} on {sp['service_date']}"
                )
                if sp.get("proof_type"):
                    lines.append(f"    Proof: {sp['proof_type']}")
                lines.append("")
        else:
            # Use required parties from rules as placeholders
            for party in rules["parties"]:
                default_method = rules["methods"][0]
                lines.append(f"  {party}")
                lines.append(f"    via {default_method}")
                lines.append("")

        if jurisdiction == "supreme_court":
            lines.append(
                f"  (13 copies filed with the Clerk per MCR 7.306(B))"
            )
            lines.append("")

        if jurisdiction == "jtc":
            lines.append(
                f"  Michigan Judicial Tenure Commission\n"
                f"  {rules['address']}\n"
                f"  via Certified Mail"
            )
            lines.append("")

        lines.extend([
            f"Authority: {rules['rule']}",
            "",
            "Respectfully submitted,",
            "",
            "____________________________",
            "Andrew Pigors, pro se",
            f"Date: {date_formatted}",
        ])

        cos_text = "\n".join(lines)

        return {
            "filing_name": filing_name,
            "jurisdiction": jurisdiction,
            "rule": rules["rule"],
            "date": filing_date,
            "parties_served": len(served_parties),
            "parties_required": len(rules["parties"]),
            "certificate_of_service": cos_text,
        }

    # ── 4. Upcoming Service Deadlines ────────────────────────────────

    def upcoming_service_deadlines(self, params: Dict) -> Dict:
        """
        List all pending service obligations with deadlines.

        params:
            days_ahead: int — look-ahead window (default 30)
        """
        days_ahead = int(params.get("days_ahead", 30))

        conn = _get_db()
        if not conn:
            return {"error": "Database connection failed"}

        pending_obligations: List[Dict] = []

        # Pull upcoming deadlines from the deadlines table
        try:
            cutoff = (
                datetime.now() + timedelta(days=days_ahead)
            ).strftime("%Y-%m-%d")
            today = datetime.now().strftime("%Y-%m-%d")

            rows = conn.execute(
                "SELECT deadline_id, case_id, title, due_date_iso, "
                "basis, basis_authority, status "
                "FROM deadlines "
                "WHERE due_date_iso >= ? AND due_date_iso <= ? "
                "AND status NOT IN ('satisfied') "
                "ORDER BY due_date_iso ASC",
                (today, cutoff),
            ).fetchall()

            for row in rows:
                title_lower = (row["title"] or "").lower()
                # Identify filing-related deadlines that need service
                if any(
                    kw in title_lower
                    for kw in [
                        "motion", "brief", "appeal", "complaint",
                        "response", "objection", "application",
                    ]
                ):
                    # Determine which jurisdictions this filing targets
                    target_jurs = self._infer_jurisdictions(
                        row["title"] or "", row["basis_authority"] or ""
                    )

                    for jur_key in target_jurs:
                        rules = SERVICE_RULES[jur_key]
                        service_due = row["due_date_iso"][:10]

                        # Check if service already recorded
                        served = False
                        if _table_exists(conn, "service_events"):
                            srow = conn.execute(
                                "SELECT COUNT(*) as cnt FROM service_events "
                                "WHERE filing_name LIKE ? "
                                "AND jurisdiction = ? "
                                "AND status = 'completed'",
                                (f"%{row['title'][:30]}%", jur_key),
                            ).fetchone()
                            served = srow and srow["cnt"] > 0

                        pending_obligations.append({
                            "filing": row["title"],
                            "case_id": row["case_id"],
                            "jurisdiction": jur_key,
                            "service_due": service_due,
                            "rule": rules["rule"],
                            "parties": rules["parties"],
                            "methods": rules["methods"],
                            "proof_required": rules["proof"],
                            "already_served": bool(served),
                            "timing_note": rules["timing"],
                        })

        except Exception:
            pass
        finally:
            conn.close()

        # Separate pending vs completed
        still_pending = [o for o in pending_obligations if not o["already_served"]]
        already_done = [o for o in pending_obligations if o["already_served"]]

        return {
            "days_ahead": days_ahead,
            "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_obligations": len(pending_obligations),
            "pending_count": len(still_pending),
            "completed_count": len(already_done),
            "pending": still_pending,
            "completed": already_done,
        }

    def _infer_jurisdictions(self, title: str, authority: str) -> List[str]:
        """Infer target jurisdiction(s) from filing title and authority cites."""
        combined = (title + " " + authority).lower()
        jurs: List[str] = []

        if any(kw in combined for kw in ["mcr 7.306", "msc", "supreme", "superintending"]):
            jurs.append("supreme_court")
        if any(kw in combined for kw in ["mcr 7.2", "coa", "appeal", "366810"]):
            jurs.append("court_of_appeals")
        if any(kw in combined for kw in ["frcp", "1983", "federal", "usdc"]):
            jurs.append("federal_court")
        if any(kw in combined for kw in ["jtc", "9.2", "judicial tenure", "misconduct"]):
            jurs.append("jtc")
        if any(kw in combined for kw in ["mcr 2.", "mcr 3.", "circuit", "custody", "ppo"]):
            jurs.append("circuit_court")

        # Default to circuit court if nothing matched
        if not jurs:
            jurs.append("circuit_court")

        return jurs

    # ── 5. Service Matrix ────────────────────────────────────────────

    def service_matrix(self, params: Dict) -> Dict:
        """
        Full matrix of all filings × all parties × service status.

        params:
            jurisdiction: str — filter to one jurisdiction (optional)
        """
        target_jur = params.get("jurisdiction", "").strip().lower()

        conn = _get_db()
        if not conn:
            return {"error": "Database connection failed"}

        # Get all distinct filings from service_events
        events: List[Dict] = []
        if _table_exists(conn, "service_events"):
            try:
                if target_jur and target_jur in SERVICE_RULES:
                    rows = conn.execute(
                        "SELECT filing_name, jurisdiction, recipient, method, "
                        "service_date, proof_type, status "
                        "FROM service_events WHERE jurisdiction = ? "
                        "ORDER BY filing_name, recipient",
                        (target_jur,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT filing_name, jurisdiction, recipient, method, "
                        "service_date, proof_type, status "
                        "FROM service_events "
                        "ORDER BY filing_name, jurisdiction, recipient"
                    ).fetchall()
                events = [dict(r) for r in rows]
            except Exception:
                pass

        # Also pull filing names from filing_readiness if available
        known_filings: List[str] = []
        if _table_exists(conn, "filing_readiness"):
            try:
                frows = conn.execute(
                    "SELECT DISTINCT filing_name FROM filing_readiness"
                ).fetchall()
                known_filings = [r["filing_name"] for r in frows]
            except Exception:
                pass

        conn.close()

        # Build the matrix
        filing_names = sorted(
            set(
                [e["filing_name"] for e in events] + known_filings
            )
        )

        jurisdictions = (
            {target_jur: SERVICE_RULES[target_jur]}
            if target_jur and target_jur in SERVICE_RULES
            else SERVICE_RULES
        )

        matrix: List[Dict] = []
        for filing in filing_names:
            for jur_key, rules in jurisdictions.items():
                for party in rules["parties"]:
                    # Find matching event
                    match = next(
                        (
                            e for e in events
                            if e["filing_name"] == filing
                            and e["jurisdiction"] == jur_key
                            and party.lower() in e["recipient"].lower()
                        ),
                        None,
                    )

                    matrix.append({
                        "filing": filing,
                        "jurisdiction": jur_key,
                        "party": party,
                        "required_rule": rules["rule"],
                        "status": match["status"] if match else "NOT SERVED",
                        "method": match["method"] if match else "",
                        "date": match["service_date"] if match else "",
                        "proof": match["proof_type"] if match else "",
                    })

        total = len(matrix)
        served = sum(1 for m in matrix if m["status"] == "completed")
        not_served = total - served

        return {
            "as_of": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_cells": total,
            "served": served,
            "not_served": not_served,
            "compliance_pct": round(served / total * 100, 1) if total else 0,
            "matrix": matrix,
            "service_rules_reference": {
                k: {"rule": v["rule"], "timing": v["timing"]}
                for k, v in jurisdictions.items()
            },
        }


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tracker = ServiceTracker()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--rules":
            result = SERVICE_RULES
        elif cmd == "--compliance" and len(sys.argv) > 2:
            result = tracker.check_compliance({"filing_name": sys.argv[2]})
        elif cmd == "--cos" and len(sys.argv) > 3:
            result = tracker.generate_cos({
                "filing_name": sys.argv[2],
                "jurisdiction": sys.argv[3],
            })
        elif cmd == "--deadlines":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            result = tracker.upcoming_service_deadlines({"days_ahead": days})
        elif cmd == "--matrix":
            jur = sys.argv[2] if len(sys.argv) > 2 else ""
            result = tracker.service_matrix({"jurisdiction": jur})
        elif cmd == "--track" and len(sys.argv) > 5:
            result = tracker.track_service({
                "filing_name": sys.argv[2],
                "jurisdiction": sys.argv[3],
                "recipient": sys.argv[4],
                "method": sys.argv[5],
            })
        else:
            result = {
                "error": "Unknown command",
                "usage": (
                    "python service_tracker.py "
                    "--rules | "
                    "--compliance <filing> | "
                    "--cos <filing> <jurisdiction> | "
                    "--deadlines [days] | "
                    "--matrix [jurisdiction] | "
                    "--track <filing> <jurisdiction> <recipient> <method>"
                ),
            }
    else:
        result = {
            "service_rules": SERVICE_RULES,
            "jurisdictions": list(SERVICE_RULES.keys()),
            "total_parties": sum(
                len(v["parties"]) for v in SERVICE_RULES.values()
            ),
        }

    cycle_json(result)
