"""
J03 Benchbook Auditor — Audits judicial actions against benchbook procedures.
Checks DV Benchbook, Best Interest factors, Civil Proceedings standards.
"""
import re
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Benchbook sections and their expected procedure patterns
BENCHBOOK_SECTIONS: Dict[str, Dict[str, Any]] = {
    "DV_5.4": {
        "label": "DV Benchbook §5.4 — Ex Parte Procedures",
        "required": re.compile(
            r'(?i)notice\s+(to|of)\s+(respondent|other\s+party)|'
            r'hearing\s+within\s+(14|fourteen)\s+days|'
            r'served\s+(with|a)\s+copy'
        ),
        "violation": re.compile(
            r'(?i)no\s+notice|without\s+hearing|'
            r'ex\s*parte.*(?:permanent|extended|indefinite)|'
            r'never\s+served'
        ),
    },
    "BI_4.2": {
        "label": "Best Interest §4.2 — Factor Weighing",
        "required": re.compile(
            r'(?i)best\s+interest\s+factor|'
            r'mcl\s+722\.23|'
            r'factor\s+[a-l]|'
            r'weigh(?:ed|ing)\s+(?:each|all)\s+factor'
        ),
        "violation": re.compile(
            r'(?i)fail(?:ed|ure)\s+to\s+(?:consider|weigh|address)\s+factor|'
            r'no\s+analysis\s+of\s+(?:best\s+interest|factor)|'
            r'conclusory\s+finding'
        ),
    },
    "BI_4.6": {
        "label": "Best Interest §4.6 — Established Custodial Environment",
        "required": re.compile(
            r'(?i)established\s+custodial\s+environment|'
            r'clear\s+and\s+convincing|'
            r'burden\s+of\s+proof'
        ),
        "violation": re.compile(
            r'(?i)preponderance.*(?:custodial|change)|'
            r'wrong\s+(?:burden|standard)|'
            r'fail(?:ed)?\s+to\s+(?:find|determine)\s+(?:custodial|ECE)'
        ),
    },
    "CIVIL_DISQUAL": {
        "label": "Civil Proceedings — Disqualification Procedures",
        "required": re.compile(
            r'(?i)mcr\s+2\.003|'
            r'disqualif(?:ication|y)|'
            r'motion\s+(?:to\s+)?disqualif|'
            r'recus(?:al|e)'
        ),
        "violation": re.compile(
            r'(?i)refus(?:ed|al)\s+to\s+(?:disqualify|recuse)|'
            r'denied\s+(?:without|no)\s+(?:hearing|explanation)|'
            r'fail(?:ed)?\s+to\s+(?:acknowledge|address)\s+(?:motion|bias)'
        ),
    },
}


class BenchbookAuditor(Agent9999):
    """Audit judicial actions against benchbook compliance standards."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J03-BENCHBOOK", **kwargs)
        self.confidence_threshold = 0.7
        self.batch_size = 5000

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
        self.db.commit()

    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        # Need either pending queue items or existing judicial findings to audit
        row = self._db_execute(
            """SELECT COUNT(*) as cnt FROM ready_queue
               WHERE queue_type='judicial' AND status='pending'"""
        ).fetchone()
        if row and row["cnt"] > 0:
            return
        try:
            row2 = self._db_execute(
                "SELECT COUNT(*) as cnt FROM judicial_findings"
            ).fetchone()
            if row2 and row2["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No judicial queue items or existing findings to audit")

    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        # Primary: claim from ready_queue
        self._db_execute(
            """UPDATE ready_queue
               SET claimed_by = ?, status = 'processing'
               WHERE rowid IN (
                   SELECT rowid FROM ready_queue
                   WHERE queue_type = 'judicial'
                     AND status = 'pending'
                   LIMIT ?
               )""",
            (self.agent_id, self.batch_size),
        )
        self.db.commit()
        rows = self._db_execute(
            """SELECT * FROM ready_queue
               WHERE claimed_by = ? AND status = 'processing'""",
            (self.agent_id,),
        ).fetchall()
        return rows if rows else []

    # ------------------------------------------------------------------
    def _process_item(self, item: Any) -> None:
        file_id = item["file_id"] if "file_id" in item.keys() else item["id"]
        content = self._read_file_content(file_id)
        if not content:
            raise SkipItemError(f"No readable content for file_id={file_id}")

        for section_key, section in BENCHBOOK_SECTIONS.items():
            violations = section["violation"].findall(content)
            if not violations:
                continue

            required_present = bool(section["required"].search(content))
            severity = min(10, 4 + len(violations) * 2)
            confidence = 0.6 if not required_present else 0.8
            confidence = min(1.0, confidence + len(violations) * 0.05)
            status = "active" if confidence >= self.confidence_threshold else "NEEDS_REVIEW"

            # Determine judge from context
            judge = self._detect_judge(content)

            self._db_execute(
                """INSERT OR IGNORE INTO judicial_findings
                   (judge, finding_type, description, severity,
                    source_file_id, canon_ref, confidence, status, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (judge, "benchbook_violation",
                 f"{section['label']}: {len(violations)} violation(s) detected",
                 severity, file_id, section_key,
                 round(confidence, 3), status, self.agent_id),
            )
        self.db.commit()
        self._mark_done(item)

    # ------------------------------------------------------------------
    def _detect_judge(self, content: str) -> str:
        """Determine which judge is referenced in the content."""
        mcneill = len(re.findall(r'(?i)mcneill|mc\s*neill', content))
        hoopes = len(re.findall(r'(?i)hoopes', content))
        if mcneill > hoopes:
            return "McNeill"
        if hoopes > mcneill:
            return "Hoopes"
        if mcneill > 0:
            return "McNeill"
        return "UNKNOWN"

    def _mark_done(self, item: Any) -> None:
        item_id = item["id"] if "id" in item.keys() else item["rowid"]
        self._db_execute(
            "UPDATE ready_queue SET status = 'done' WHERE id = ?", (item_id,)
        )
        self.db.commit()
