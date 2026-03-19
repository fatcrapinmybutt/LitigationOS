"""
J05 JTC Compiler — Compiles Judicial Tenure Commission complaint exhibits
from aggregated judicial_findings. Groups by type, scores cumulative severity.
"""
import json
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Finding types that roll into JTC exhibits
JTC_CATEGORIES = {
    "ex_parte": "Ex Parte Communications",
    "bias_indicator": "Bias and Prejudice",
    "benchbook_violation": "Benchbook Non-Compliance",
    "canon_violation": "Canon Violations",
    "procedural_issue": "Procedural Irregularities",
    "order_analysis": "Judicial Order Irregularities",
    "housing_compliance": "Housing Case Compliance",
}


class JtcCompiler(Agent9999):
    """Compile JTC complaint exhibits from judicial findings."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J05-JTC", **kwargs)
        self.confidence_threshold = 0.7

    # ------------------------------------------------------------------
    def _ensure_tables(self) -> None:
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS judicial_findings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                judge       TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                description TEXT,
                severity    INTEGER DEFAULT 0,
                source_file_id INTEGER,
                canon_ref   TEXT,
                confidence  REAL DEFAULT 0.0,
                status      TEXT DEFAULT 'active',
                agent_id    TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS atoms (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                atom_type    TEXT NOT NULL,
                title        TEXT,
                content      TEXT,
                metadata     TEXT,
                source_ids   TEXT,
                severity     INTEGER DEFAULT 0,
                confidence   REAL DEFAULT 0.0,
                status       TEXT DEFAULT 'active',
                agent_id     TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        try:
            row = self._db_execute(
                "SELECT COUNT(*) as cnt FROM judicial_findings WHERE status = 'active'"
            ).fetchone()
            if row and row["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No active judicial findings to compile into JTC exhibits")

    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        """Group findings by judge — each judge is one work item."""
        try:
            judges = self._db_execute(
                "SELECT DISTINCT judge FROM judicial_findings WHERE status = 'active'"
            ).fetchall()
            return judges if judges else []
        except Exception:
            return []

    # ------------------------------------------------------------------
    def _process_item(self, item: Any) -> None:
        judge = item["judge"]
        findings = self._db_execute(
            """SELECT * FROM judicial_findings
               WHERE judge = ? AND status = 'active'
               ORDER BY finding_type, severity DESC""",
            (judge,),
        ).fetchall()

        if not findings:
            raise SkipItemError(f"No active findings for judge {judge}")

        # Group by category
        grouped: Dict[str, List[dict]] = {}
        for f in findings:
            ftype = f["finding_type"]
            grouped.setdefault(ftype, []).append(dict(f))

        # Build one JTC exhibit atom per category
        for category, items in grouped.items():
            category_label = JTC_CATEGORIES.get(category, category.replace("_", " ").title())
            cumulative_severity = min(10, sum(i["severity"] for i in items) // max(len(items), 1) + len(items))
            avg_confidence = sum(i["confidence"] for i in items) / len(items)
            source_ids = [i["id"] for i in items]
            canon_refs = set()
            for i in items:
                if i["canon_ref"]:
                    canon_refs.update(i["canon_ref"].split("; "))

            exhibit_content = self._format_exhibit(judge, category_label, items, canon_refs)

            metadata = json.dumps({
                "judge": judge,
                "category": category,
                "finding_count": len(items),
                "canon_refs": sorted(canon_refs),
                "cumulative_severity": cumulative_severity,
            })

            status = "active" if avg_confidence >= self.confidence_threshold else "NEEDS_REVIEW"

            import hashlib
            atom_id = hashlib.sha1(
                f"JTC|{judge}|{category_label}".encode()
            ).hexdigest()[:16]
            self._db_execute(
                """INSERT OR REPLACE INTO atoms
                   (id, atom_type, source_file_id, meek_lane, content,
                    confidence, posture, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"JTC-{atom_id}", "jtc_exhibit",
                 source_ids[0] if source_ids else None, "C",
                 exhibit_content, round(avg_confidence, 3),
                 "RECORD_FACT", self.agent_id),
            )
        self.db.commit()
        self._log("INFO", f"Compiled {len(grouped)} JTC exhibit categories for {judge}")

    # ------------------------------------------------------------------
    def _format_exhibit(self, judge: str, category: str,
                        items: List[dict], canon_refs: set) -> str:
        lines = [
            f"JUDICIAL TENURE COMMISSION — COMPLAINT EXHIBIT",
            f"Judge: {judge}",
            f"Category: {category}",
            f"Findings Count: {len(items)}",
            f"Applicable Canons: {', '.join(sorted(canon_refs)) if canon_refs else 'None mapped'}",
            "",
            "FINDINGS DETAIL:",
            "=" * 60,
        ]
        for idx, item in enumerate(items, 1):
            lines.append(f"\n  [{idx}] Severity: {item['severity']}/10 | "
                         f"Confidence: {item['confidence']:.2f}")
            lines.append(f"      {item['description']}")
            if item["canon_ref"]:
                lines.append(f"      Canon: {item['canon_ref']}")
        return "\n".join(lines)
