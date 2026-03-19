"""
Gap Resolver — LitigationOS 2026
Identifies, prioritizes, and resolves knowledge/evidence/authority gaps
for Pigors v. Watson litigation readiness.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")


def _get_db(readonly: bool = True) -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    if readonly:
        conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class GapResolver:
    """Identifies, prioritizes, and resolves litigation gaps."""

    SEVERITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    def get_gap_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query gap_tickets (~15 rows): gap_type, description, severity, resolution_status."""
        conn = _get_db()
        try:
            if status:
                rows = conn.execute(
                    """SELECT * FROM gap_tickets
                       WHERE LOWER(resolution_status) = ?
                       ORDER BY rowid""",
                    (status.lower(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM gap_tickets ORDER BY rowid"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_knowledge_gaps(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Query knowledge_gaps table (~13 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM knowledge_gaps ORDER BY rowid LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_error_prevention(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Query error_prevention_registry (~12 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM error_prevention_registry ORDER BY rowid LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def prioritize_gaps(self) -> List[Dict[str, Any]]:
        """Rank gaps by severity and impact on filing readiness."""
        gaps = self.get_gap_tickets()
        knowledge = self.get_knowledge_gaps()

        all_items: List[Dict[str, Any]] = []

        for g in gaps:
            severity = (g.get("severity") or "medium").lower()
            weight = self.SEVERITY_WEIGHT.get(severity, 2)
            status = (g.get("resolution_status") or "open").lower()
            if status in ("resolved", "closed", "done"):
                continue
            all_items.append({
                "source": "gap_tickets",
                "id": g.get("rowid") or g.get("id"),
                "type": g.get("gap_type", ""),
                "description": g.get("description", ""),
                "severity": severity,
                "weight": weight,
                "status": status,
            })

        for k in knowledge:
            all_items.append({
                "source": "knowledge_gaps",
                "id": k.get("rowid") or k.get("id"),
                "type": "knowledge",
                "description": str(k.get("description") or k.get("gap_description") or ""),
                "severity": (k.get("severity") or "medium").lower(),
                "weight": self.SEVERITY_WEIGHT.get(
                    (k.get("severity") or "medium").lower(), 2
                ),
                "status": (k.get("status") or "open").lower(),
            })

        all_items.sort(key=lambda x: (-x["weight"], x["description"]))
        for rank, item in enumerate(all_items, 1):
            item["priority_rank"] = rank

        return all_items

    def suggest_resolution(self, gap_id: int) -> Dict[str, Any]:
        """Suggest how to resolve a specific gap ticket."""
        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT * FROM gap_tickets WHERE rowid = ?", (gap_id,)
            ).fetchone()
            if not row:
                return {"error": f"Gap ticket {gap_id} not found."}

            gap = dict(row)
            gap_type = (gap.get("gap_type") or "").lower()
            severity = (gap.get("severity") or "medium").lower()

            suggestions: List[str] = []

            if "evidence" in gap_type:
                suggestions.extend([
                    "Search evidence_quotes table for existing supporting evidence",
                    "Review documents table for uningestedfiles that may contain evidence",
                    "Consider issuing discovery requests (interrogatories, RFP) per MCR 2.309/2.310",
                    "Check if subpoena needed per MCR 2.506",
                ])
            elif "authority" in gap_type:
                suggestions.extend([
                    "Search auth_rules and master_citations for on-point authority",
                    "Review legal_reference_docs for secondary authority",
                    "Check if analogous Michigan case law exists via case name search",
                    "Consider whether federal authority supports the position",
                ])
            elif "knowledge" in gap_type:
                suggestions.extend([
                    "Ingest additional documents via the intake pipeline",
                    "Query pages table for raw text that may not be fully indexed",
                    "Review md_sections for analysis that may address this gap",
                ])
            elif "procedural" in gap_type or "compliance" in gap_type:
                suggestions.extend([
                    "Query auth_rules for the specific MCR governing this procedure",
                    "Review deadlines table for timing requirements",
                    "Check SCAO forms for required forms",
                    "Verify service requirements per MCR 2.107",
                ])
            else:
                suggestions.extend([
                    "Review the gap description and identify the specific deficiency",
                    "Search relevant DB tables for existing data that addresses the gap",
                    "Determine if additional document ingestion is needed",
                    "Assess whether this gap blocks any pending filing",
                ])

            if severity == "critical":
                suggestions.insert(0, "⚠️ CRITICAL: Address immediately — may affect pending deadlines")

            return {
                "gap_id": gap_id,
                "gap": gap,
                "suggestions": suggestions,
                "next_step": suggestions[0] if suggestions else "Review gap manually",
            }
        finally:
            conn.close()

    def create_action_items(self) -> List[Dict[str, Any]]:
        """Generate actionable items to close all open gaps."""
        prioritized = self.prioritize_gaps()
        action_items: List[Dict[str, Any]] = []

        for item in prioritized:
            if item.get("status") in ("resolved", "closed", "done"):
                continue

            gap_type = (item.get("type") or "").lower()

            if "evidence" in gap_type:
                action = "Gather evidence: search DB or issue discovery"
            elif "authority" in gap_type:
                action = "Research authority: search auth_rules and case law"
            elif "knowledge" in gap_type:
                action = "Fill knowledge gap: ingest documents or research"
            elif "procedural" in gap_type:
                action = "Check procedure: review MCR requirements"
            else:
                action = "Review and address gap"

            action_items.append({
                "priority": item.get("priority_rank"),
                "source": item.get("source"),
                "gap_id": item.get("id"),
                "severity": item.get("severity"),
                "description": item.get("description", "")[:200],
                "action": action,
                "status": "pending",
            })

        return action_items

    def get_gap_statistics(self) -> Dict[str, Any]:
        """Summary statistics by type, severity, and resolution status."""
        gaps = self.get_gap_tickets()
        knowledge = self.get_knowledge_gaps()

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_status: Dict[str, int] = {}

        for g in gaps:
            t = g.get("gap_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

            s = (g.get("severity") or "unknown").lower()
            by_severity[s] = by_severity.get(s, 0) + 1

            st = (g.get("resolution_status") or "unknown").lower()
            by_status[st] = by_status.get(st, 0) + 1

        open_count = sum(v for k, v in by_status.items() if k not in ("resolved", "closed", "done"))

        return {
            "total_gap_tickets": len(gaps),
            "total_knowledge_gaps": len(knowledge),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
            "open_gaps": open_count,
            "summary": (
                f"{len(gaps)} gap tickets ({open_count} open), "
                f"{len(knowledge)} knowledge gaps."
            ),
        }

    def resolve_gap(self, gap_id: int, note: str) -> Dict[str, Any]:
        """Mark a gap as resolved (writable — skips query_only)."""
        conn = _get_db(readonly=False)
        try:
            row = conn.execute(
                "SELECT * FROM gap_tickets WHERE rowid = ?", (gap_id,)
            ).fetchone()
            if not row:
                return {"error": f"Gap ticket {gap_id} not found."}

            conn.execute(
                """UPDATE gap_tickets
                   SET resolution_status = 'resolved',
                       resolution_note = ?
                   WHERE rowid = ?""",
                (note, gap_id),
            )
            conn.commit()

            updated = conn.execute(
                "SELECT * FROM gap_tickets WHERE rowid = ?", (gap_id,)
            ).fetchone()

            return {
                "action": "resolve_gap",
                "gap_id": gap_id,
                "status": "resolved",
                "note": note,
                "gap": dict(updated) if updated else None,
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify DB connectivity and key gap resolution methods."""
    results = {"status": "ok", "tests": {}}
    resolver = GapResolver()

    # Test 1: DB connectivity
    try:
        conn = _get_db()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        results["tests"]["db_connectivity"] = {"passed": True}
    except Exception as e:
        results["tests"]["db_connectivity"] = {"passed": False, "error": str(e)}

    # Test 2: get_gap_tickets
    try:
        tickets = resolver.get_gap_tickets()
        results["tests"]["get_gap_tickets"] = {
            "passed": isinstance(tickets, list),
            "count": len(tickets),
        }
    except Exception as e:
        results["tests"]["get_gap_tickets"] = {"passed": False, "error": str(e)}

    # Test 3: get_gap_statistics
    try:
        stats = resolver.get_gap_statistics()
        results["tests"]["get_gap_statistics"] = {
            "passed": isinstance(stats, dict) and "total_gap_tickets" in stats,
            "total_tickets": stats.get("total_gap_tickets", 0),
            "open_gaps": stats.get("open_gaps", 0),
        }
    except Exception as e:
        results["tests"]["get_gap_statistics"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    resolver = GapResolver()

    if len(sys.argv) < 2:
        print("Usage: gap_resolver.py <command> [args]")
        print("Commands: tickets [status] | knowledge | errors | prioritize")
        print("          suggest <gap_id> | actions | stats | test")
        print("          resolve <gap_id> <note>")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        print(json.dumps(self_test(), indent=2, default=str))
        sys.exit(0)

    if cmd == "tickets":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        result = resolver.get_gap_tickets(status=status)
    elif cmd == "knowledge":
        result = resolver.get_knowledge_gaps()
    elif cmd == "errors":
        result = resolver.get_error_prevention()
    elif cmd == "prioritize":
        result = resolver.prioritize_gaps()
    elif cmd == "suggest" and len(sys.argv) >= 3:
        result = resolver.suggest_resolution(int(sys.argv[2]))
    elif cmd == "actions":
        result = resolver.create_action_items()
    elif cmd == "stats":
        result = resolver.get_gap_statistics()
    elif cmd == "resolve" and len(sys.argv) >= 4:
        gap_id = int(sys.argv[2])
        note = " ".join(sys.argv[3:])
        result = resolver.resolve_gap(gap_id, note)
    else:
        print(f"Unknown command or missing args: {cmd}")
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))
