"""Dashboard Home Screen Engine.

Aggregates case health metrics from all DB tables into a single view.
Provides per-filing status, evidence arsenal counts, deadline urgency,
financial summary, lane health, and system diagnostics — all from live
queries against ``litigation_context.db``.

Usage::

    engine = DashboardEngine()
    health = engine.get_case_health()
    md = engine.generate_full_dashboard()
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Separation date — ex parte order suspending Andrew's parenting time
SEPARATION_DATE = date(2025, 8, 8)

# Six case lanes
LANE_REGISTRY: Dict[str, Dict[str, str]] = {
    "A": {"name": "Custody", "cases": "2024-001507-DC, 2023-5907-PP"},
    "B": {"name": "Housing (Shady Oaks)", "cases": "2025-002760-CZ"},
    "C": {"name": "Convergence", "cases": "Multi-lane"},
    "D": {"name": "PPO / Protection Orders", "cases": "2024-001507-DC, 2023-5907-PP"},
    "E": {"name": "Judicial Misconduct / JTC", "cases": "2024-001507-DC"},
    "F": {"name": "Appellate (COA/MSC)", "cases": "Assigned on filing"},
}

# Filing metadata (mirrors filing_priority.py FILING_REGISTRY)
FILING_NAMES: Dict[str, str] = {
    "F1": "Emergency TRO",
    "F2": "Shady Oaks Housing",
    "F3": "Judicial Disqualification",
    "F4": "Federal §1983 Complaint",
    "F5": "MSC Bypass Application",
    "F6": "JTC Formal Complaint",
    "F7": "Custody Modification",
    "F8": "PPO Modification/Dismissal",
    "F9": "COA Appeal Brief",
    "F10": "COA Emergency Motion",
}

FILING_LANES: Dict[str, str] = {
    "F1": "A", "F2": "B", "F3": "E", "F4": "A", "F5": "F",
    "F6": "E", "F7": "A", "F8": "D", "F9": "F", "F10": "F",
}


class DashboardEngine:
    """Aggregate case health metrics from the litigation database."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        logger.info("DashboardEngine ready  db=%s", self.db_path)

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
        return (
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                (name,),
            ).fetchone()[0]
            > 0
        )

    @staticmethod
    def _safe_count(conn: sqlite3.Connection, table: str, where: str = "") -> int:
        """Return COUNT(*) for *table*, or 0 if the table does not exist."""
        exists = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()[0]
        if not exists:
            return 0
        sql = f"SELECT COUNT(*) FROM [{table}]"
        if where:
            sql += f" WHERE {where}"
        return conn.execute(sql).fetchone()[0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_separation_days(self) -> int:
        """Days since L.D.W. separation (Aug 8 2025 ex parte order)."""
        delta = date.today() - SEPARATION_DATE
        return max(delta.days, 0)

    def get_evidence_stats(self) -> Dict[str, Any]:
        """Evidence arsenal counts via a single consolidated query."""
        conn = self._connect()
        try:
            stats: Dict[str, Any] = {}
            stats["evidence_quotes"] = self._safe_count(conn, "evidence_quotes")
            stats["citations"] = self._safe_count(conn, "citation_audit")
            stats["impeachment_items"] = self._safe_count(conn, "impeachment_matrix")
            stats["bias_events"] = self._safe_count(
                conn, "judicial_bias_chronology"
            )
            stats["alienation_events"] = self._safe_count(
                conn, "alienation_timeline"
            )
            stats["exhibits"] = self._safe_count(conn, "exhibit_binders")
            stats["irac_claims"] = self._safe_count(conn, "irac_analysis")

            # Authority chain completeness
            stats["total_chains"] = self._safe_count(
                conn, "authority_chain_audit"
            )
            if self._table_exists(conn, "authority_chain_audit"):
                # Verify column name before querying
                cols = {
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(authority_chain_audit)"
                    ).fetchall()
                }
                complete_col = (
                    "chain_complete" if "chain_complete" in cols else None
                )
                if complete_col:
                    stats["complete_chains"] = conn.execute(
                        f"SELECT COUNT(*) FROM authority_chain_audit WHERE {complete_col} = 1"
                    ).fetchone()[0]
                else:
                    stats["complete_chains"] = 0
            else:
                stats["complete_chains"] = 0

            # Alienation cumulative days (if column exists)
            if self._table_exists(conn, "alienation_timeline"):
                at_cols = {
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(alienation_timeline)"
                    ).fetchall()
                }
                if "days" in at_cols:
                    row = conn.execute(
                        "SELECT COALESCE(SUM(days), 0) FROM alienation_timeline"
                    ).fetchone()
                    stats["alienation_cumulative_days"] = row[0]
                else:
                    stats["alienation_cumulative_days"] = 0
            else:
                stats["alienation_cumulative_days"] = 0

            return stats
        finally:
            conn.close()

    def get_filing_status(self) -> List[Dict[str, Any]]:
        """Per-filing readiness: status, completeness %, authority strength."""
        conn = self._connect()
        try:
            results: List[Dict[str, Any]] = []
            for fid, fname in FILING_NAMES.items():
                entry: Dict[str, Any] = {
                    "filing_id": fid,
                    "name": fname,
                    "lane": FILING_LANES.get(fid, "?"),
                    "status": "DRAFT",
                    "completeness_pct": 0.0,
                    "authority_strength": 0.0,
                    "irac_score": 0.0,
                    "exhibit_count": 0,
                }

                # Filing status from filing_vulnerability_scores
                if self._table_exists(conn, "filing_vulnerability_scores"):
                    fvs_cols = {
                        r[1]
                        for r in conn.execute(
                            "PRAGMA table_info(filing_vulnerability_scores)"
                        ).fetchall()
                    }
                    if "filing_id" in fvs_cols and "overall_vulnerability" in fvs_cols:
                        row = conn.execute(
                            "SELECT overall_vulnerability FROM filing_vulnerability_scores WHERE filing_id = ?",
                            (fid,),
                        ).fetchone()
                        if row:
                            vuln = float(row[0])
                            entry["completeness_pct"] = round(
                                max(0.0, min(100.0, (10 - vuln) * 10)), 1
                            )

                # Authority chain strength
                if self._table_exists(conn, "authority_chain_summary"):
                    acs_cols = {
                        r[1]
                        for r in conn.execute(
                            "PRAGMA table_info(authority_chain_summary)"
                        ).fetchall()
                    }
                    if "filing_id" in acs_cols and "score" in acs_cols:
                        row = conn.execute(
                            "SELECT score FROM authority_chain_summary WHERE filing_id = ?",
                            (fid,),
                        ).fetchone()
                        if row:
                            entry["authority_strength"] = round(float(row[0]), 2)

                # IRAC score
                if self._table_exists(conn, "irac_analysis"):
                    ia_cols = {
                        r[1]
                        for r in conn.execute(
                            "PRAGMA table_info(irac_analysis)"
                        ).fetchall()
                    }
                    if "filing_id" in ia_cols and "score" in ia_cols:
                        row = conn.execute(
                            "SELECT score FROM irac_analysis WHERE filing_id = ?",
                            (fid,),
                        ).fetchone()
                        if row:
                            entry["irac_score"] = round(float(row[0]), 2)

                # Exhibit count
                if self._table_exists(conn, "exhibit_binders"):
                    eb_cols = {
                        r[1]
                        for r in conn.execute(
                            "PRAGMA table_info(exhibit_binders)"
                        ).fetchall()
                    }
                    if "filing_id" in eb_cols:
                        row = conn.execute(
                            "SELECT COUNT(*) FROM exhibit_binders WHERE filing_id = ?",
                            (fid,),
                        ).fetchone()
                        entry["exhibit_count"] = row[0]

                # Derive status from completeness
                pct = entry["completeness_pct"]
                if pct >= 90:
                    entry["status"] = "READY"
                elif pct >= 50:
                    entry["status"] = "REVIEW"
                else:
                    entry["status"] = "DRAFT"

                results.append(entry)
            return results
        finally:
            conn.close()

    def get_deadline_urgency(self) -> List[Dict[str, Any]]:
        """Upcoming deadlines colour-coded by urgency."""
        conn = self._connect()
        try:
            if not self._table_exists(conn, "deadlines"):
                return []

            cols = {
                r[1]
                for r in conn.execute("PRAGMA table_info(deadlines)").fetchall()
            }
            # Determine date column name
            date_col: Optional[str] = None
            for candidate in ("due_date_iso", "due_date", "deadline_date", "date"):
                if candidate in cols:
                    date_col = candidate
                    break
            if date_col is None:
                logger.warning("deadlines table has no recognisable date column")
                return []

            today_str = date.today().isoformat()
            rows = conn.execute(
                f"SELECT * FROM deadlines WHERE [{date_col}] >= ? ORDER BY [{date_col}] ASC LIMIT 50",
                (today_str,),
            ).fetchall()

            results: List[Dict[str, Any]] = []
            for r in rows:
                d = dict(r)
                due = d.get(date_col, "")
                try:
                    due_date = date.fromisoformat(str(due)[:10])
                    days_left = (due_date - date.today()).days
                except (ValueError, TypeError):
                    days_left = 999

                if days_left < 7:
                    urgency = "RED"
                elif days_left < 30:
                    urgency = "YELLOW"
                else:
                    urgency = "GREEN"

                results.append({
                    "due_date": str(due)[:10],
                    "days_left": days_left,
                    "urgency": urgency,
                    "description": d.get("description", d.get("title", d.get("name", ""))),
                    "filing_id": d.get("filing_id", d.get("vehicle_name", "")),
                })
            return results
        finally:
            conn.close()

    def get_financial_summary(self) -> Dict[str, Any]:
        """Damages totals and filing fee estimates."""
        conn = self._connect()
        try:
            summary: Dict[str, Any] = {
                "damages_low": 0.0,
                "damages_high": 0.0,
                "filing_fees_total": 0.0,
                "ifp_savings": 0.0,
            }

            if self._table_exists(conn, "damages_calculation"):
                dc_cols = {
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(damages_calculation)"
                    ).fetchall()
                }
                if "amount_low" in dc_cols and "amount_high" in dc_cols:
                    row = conn.execute(
                        "SELECT COALESCE(SUM(amount_low), 0), COALESCE(SUM(amount_high), 0) "
                        "FROM damages_calculation"
                    ).fetchone()
                    summary["damages_low"] = round(float(row[0]), 2)
                    summary["damages_high"] = round(float(row[1]), 2)
                elif "amount" in dc_cols:
                    row = conn.execute(
                        "SELECT COALESCE(SUM(amount), 0) FROM damages_calculation"
                    ).fetchone()
                    summary["damages_low"] = round(float(row[0]), 2)
                    summary["damages_high"] = summary["damages_low"]

            if self._table_exists(conn, "filing_fees"):
                ff_cols = {
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(filing_fees)"
                    ).fetchall()
                }
                fee_col = "fee" if "fee" in ff_cols else ("amount" if "amount" in ff_cols else None)
                if fee_col:
                    row = conn.execute(
                        f"SELECT COALESCE(SUM([{fee_col}]), 0) FROM filing_fees"
                    ).fetchone()
                    summary["filing_fees_total"] = round(float(row[0]), 2)

                waived_col = "waived" if "waived" in ff_cols else None
                if waived_col and fee_col:
                    row = conn.execute(
                        f"SELECT COALESCE(SUM([{fee_col}]), 0) FROM filing_fees WHERE [{waived_col}] = 1"
                    ).fetchone()
                    summary["ifp_savings"] = round(float(row[0]), 2)

            return summary
        finally:
            conn.close()

    def get_lane_health(self) -> Dict[str, Dict[str, Any]]:
        """Per-lane evidence count, filing count, and readiness score."""
        conn = self._connect()
        try:
            filings = self.get_filing_status()
            lane_data: Dict[str, Dict[str, Any]] = {}
            for lane_id, meta in LANE_REGISTRY.items():
                lane_filings = [f for f in filings if f["lane"] == lane_id]
                total_pct = sum(f["completeness_pct"] for f in lane_filings)
                count = len(lane_filings) or 1
                lane_data[lane_id] = {
                    "name": meta["name"],
                    "cases": meta["cases"],
                    "filing_count": len(lane_filings),
                    "avg_readiness": round(total_pct / count, 1),
                    "filings": [f["filing_id"] for f in lane_filings],
                }

            # Per-lane evidence counts from evidence_quotes if available
            if self._table_exists(conn, "evidence_quotes"):
                eq_cols = {
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(evidence_quotes)"
                    ).fetchall()
                }
                lane_col = None
                for candidate in ("lane", "lane_id", "case_lane"):
                    if candidate in lane_col if lane_col else candidate in eq_cols:
                        lane_col = candidate
                        break
                # Re-check properly
                lane_col = next(
                    (c for c in ("lane", "lane_id", "case_lane") if c in eq_cols),
                    None,
                )
                if lane_col:
                    rows = conn.execute(
                        f"SELECT [{lane_col}], COUNT(*) as cnt FROM evidence_quotes GROUP BY [{lane_col}]"
                    ).fetchall()
                    for r in rows:
                        lid = str(r[0]).upper()
                        if lid in lane_data:
                            lane_data[lid]["evidence_count"] = r[1]

            # Ensure evidence_count exists for all lanes
            for lid in lane_data:
                lane_data[lid].setdefault("evidence_count", 0)

            return lane_data
        finally:
            conn.close()

    def get_system_health(self) -> Dict[str, Any]:
        """DB size, table count, and last pipeline run."""
        health: Dict[str, Any] = {}

        # DB file size
        if self.db_path.exists():
            size_bytes = self.db_path.stat().st_size
            health["db_size_mb"] = round(size_bytes / (1024 * 1024), 1)
        else:
            health["db_size_mb"] = 0.0

        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()
            health["table_count"] = row[0]

            # Last pipeline run (from pipeline_runs if it exists)
            if self._table_exists(conn, "pipeline_runs"):
                pr_cols = {
                    r[1]
                    for r in conn.execute(
                        "PRAGMA table_info(pipeline_runs)"
                    ).fetchall()
                }
                ts_col = next(
                    (c for c in ("completed_at", "timestamp", "created_at", "run_date") if c in pr_cols),
                    None,
                )
                if ts_col:
                    row = conn.execute(
                        f"SELECT [{ts_col}] FROM pipeline_runs ORDER BY [{ts_col}] DESC LIMIT 1"
                    ).fetchone()
                    health["last_pipeline_run"] = str(row[0]) if row else "Never"
                else:
                    health["last_pipeline_run"] = "Unknown"
            else:
                health["last_pipeline_run"] = "N/A"
        finally:
            conn.close()

        return health

    def get_case_health(self) -> Dict[str, Any]:
        """Top-level health summary combining all sub-metrics."""
        evidence = self.get_evidence_stats()
        filings = self.get_filing_status()
        deadlines = self.get_deadline_urgency()
        financial = self.get_financial_summary()
        system = self.get_system_health()

        ready_count = sum(1 for f in filings if f["status"] == "READY")
        red_deadlines = sum(1 for d in deadlines if d["urgency"] == "RED")

        return {
            "separation_days": self.get_separation_days(),
            "active_lanes": len(LANE_REGISTRY),
            "phase": "Filing Preparation",
            "filings_total": len(filings),
            "filings_ready": ready_count,
            "filings_in_review": sum(1 for f in filings if f["status"] == "REVIEW"),
            "filings_draft": sum(1 for f in filings if f["status"] == "DRAFT"),
            "red_deadlines": red_deadlines,
            "evidence": evidence,
            "financial": financial,
            "system": system,
        }

    # ------------------------------------------------------------------
    # Markdown generation
    # ------------------------------------------------------------------

    def generate_full_dashboard(self) -> str:
        """Render a complete Markdown dashboard for CLI or GUI display."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        sep_days = self.get_separation_days()
        evidence = self.get_evidence_stats()
        filings = self.get_filing_status()
        deadlines = self.get_deadline_urgency()
        financial = self.get_financial_summary()
        lanes = self.get_lane_health()
        system = self.get_system_health()

        lines: List[str] = []

        # ── Case Header ──────────────────────────────────────────────
        lines.append("# LitigationOS — Dashboard")
        lines.append(f"_Generated: {now_str}_\n")
        lines.append("## Case Header")
        lines.append(f"- **Plaintiff:** Andrew James Pigors (pro se)")
        lines.append(f"- **Defendant:** Emily A. Watson")
        lines.append(f"- **Child:** L.D.W. (initials per MCR 8.119(H))")
        lines.append(f"- **Days since separation from L.D.W.:** {sep_days}")
        lines.append(f"- **Active lanes:** {len(LANE_REGISTRY)}")
        lines.append(f"- **Current phase:** Filing Preparation\n")

        # ── Filing Readiness ─────────────────────────────────────────
        lines.append("## Filing Readiness\n")
        lines.append("| Filing | Name | Lane | Status | Complete% | Authority | IRAC | Exhibits |")
        lines.append("|--------|------|------|--------|-----------|-----------|------|----------|")
        for f in filings:
            status_icon = {"READY": "🟢", "REVIEW": "🟡", "DRAFT": "🔴", "FILED": "✅"}.get(
                f["status"], "⬜"
            )
            lines.append(
                f"| **{f['filing_id']}** | {f['name']} | {f['lane']} | "
                f"{status_icon} {f['status']} | {f['completeness_pct']}% | "
                f"{f['authority_strength']} | {f['irac_score']} | "
                f"{f['exhibit_count']:,} |"
            )

        ready_count = sum(1 for f in filings if f["status"] == "READY")
        lines.append(f"\n_Ready to file: {ready_count}/{len(filings)}_\n")

        # ── Evidence Arsenal ─────────────────────────────────────────
        lines.append("## Evidence Arsenal\n")
        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Evidence Quotes | {evidence['evidence_quotes']:,} |")
        lines.append(f"| Citations Audited | {evidence['citations']:,} |")
        lines.append(f"| Impeachment Items | {evidence['impeachment_items']:,} |")
        lines.append(f"| Judicial Bias Events | {evidence['bias_events']:,} |")
        lines.append(f"| Alienation Events | {evidence['alienation_events']:,} |")
        lines.append(f"| Alienation Cumulative Days | {evidence['alienation_cumulative_days']:,} |")
        lines.append(f"| Authority Chains (complete/total) | {evidence['complete_chains']}/{evidence['total_chains']} |")
        lines.append(f"| Exhibits | {evidence['exhibits']:,} |")
        lines.append(f"| IRAC Claims | {evidence['irac_claims']:,} |")
        lines.append("")

        # ── Deadline Tracker ─────────────────────────────────────────
        lines.append("## Deadline Tracker\n")
        if deadlines:
            lines.append("| Due Date | Days Left | Urgency | Description | Filing |")
            lines.append("|----------|-----------|---------|-------------|--------|")
            for d in deadlines[:20]:
                icon = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(
                    d["urgency"], "⬜"
                )
                lines.append(
                    f"| {d['due_date']} | {d['days_left']} | {icon} {d['urgency']} | "
                    f"{d['description'][:60]} | {d['filing_id']} |"
                )
        else:
            lines.append("_No upcoming deadlines found._")
        lines.append("")

        # ── Financial Summary ────────────────────────────────────────
        lines.append("## Financial Summary\n")
        lines.append(f"- **Damages range:** ${financial['damages_low']:,.2f} – ${financial['damages_high']:,.2f}")
        lines.append(f"- **Filing fees total:** ${financial['filing_fees_total']:,.2f}")
        lines.append(f"- **IFP savings potential:** ${financial['ifp_savings']:,.2f}")
        lines.append("")

        # ── Lane Health ──────────────────────────────────────────────
        lines.append("## Lane Health\n")
        lines.append("| Lane | Name | Filings | Evidence | Avg Readiness |")
        lines.append("|------|------|---------|----------|---------------|")
        for lid in sorted(lanes):
            lh = lanes[lid]
            lines.append(
                f"| **{lid}** | {lh['name']} | {lh['filing_count']} | "
                f"{lh['evidence_count']:,} | {lh['avg_readiness']}% |"
            )
        lines.append("")

        # ── System Health ────────────────────────────────────────────
        lines.append("## System Health\n")
        lines.append(f"- **DB size:** {system['db_size_mb']} MB")
        lines.append(f"- **Table count:** {system['table_count']}")
        lines.append(f"- **Last pipeline run:** {system['last_pipeline_run']}")
        lines.append("")

        return "\n".join(lines)
