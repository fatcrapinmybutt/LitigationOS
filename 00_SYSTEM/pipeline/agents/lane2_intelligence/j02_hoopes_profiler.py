"""
J02 Hoopes Profiler — Judicial intelligence extraction for Judge Hoopes.
Focus on housing case 2025-002760-CZ procedural compliance.
"""
import re
from typing import Any, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

_PATTERNS = {
    "name": re.compile(r'(?i)hoopes|judge\s+hoopes'),
    "orders": re.compile(r'(?i)order|ruling|opinion|judgment'),
    "ex_parte": re.compile(r'(?i)ex\s*parte|without\s+notice|unilateral'),
    "bias": re.compile(r'(?i)bias|prejudic|partial|unfair'),
    "housing_case": re.compile(r'(?i)2025[-\s]?002760|CZ|habitability|landlord|tenant'),
    "procedural": re.compile(r'(?i)service|notice|hearing|motion|response\s+time|due\s+process'),
}


class HoopesProfiler(Agent9999):
    """Profile Judge Hoopes' judicial actions, especially housing case compliance."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J02-HOOPES", **kwargs)
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
        row = self._db_execute(
            """SELECT COUNT(*) as cnt FROM ready_queue
               WHERE queue_type='judicial' AND status='pending'"""
        ).fetchone()
        if row and row["cnt"] > 0:
            return
        try:
            row2 = self._db_execute(
                """SELECT COUNT(*) as cnt FROM files
                   WHERE LOWER(full_path) LIKE '%hoopes%'
                      OR LOWER(file_name) LIKE '%hoopes%'
                      OR LOWER(full_path) LIKE '%002760%'"""
            ).fetchone()
            if row2 and row2["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No pending judicial items or Hoopes/housing files found")

    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
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

        hits = {name: len(pat.findall(content)) for name, pat in _PATTERNS.items()}

        if hits["name"] == 0:
            self._mark_done(item)
            return

        findings = self._extract_findings(content, hits, file_id)
        for f in findings:
            if f["confidence"] < self.confidence_threshold:
                f["status"] = "NEEDS_REVIEW"
            self._db_execute(
                """INSERT OR IGNORE INTO judicial_findings
                   (judge, finding_type, description, severity,
                    source_file_id, canon_ref, confidence, status, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("Hoopes", f["type"], f["desc"], f["severity"],
                 file_id, f["canon"], f["confidence"], f["status"], self.agent_id),
            )
        self.db.commit()
        self._mark_done(item)

    # ------------------------------------------------------------------
    def _extract_findings(self, content: str, hits: dict, file_id: int) -> List[dict]:
        findings: List[dict] = []
        density = sum(hits.values()) / max(len(content) / 1000, 1)

        if hits["ex_parte"] > 0:
            sev = min(10, 5 + hits["ex_parte"])
            conf = min(1.0, 0.5 + density * 0.1 + hits["name"] * 0.05)
            findings.append({
                "type": "ex_parte",
                "desc": f"Ex parte indicators near Hoopes references ({hits['ex_parte']} hits)",
                "severity": sev,
                "canon": "Canon 3(A)(3)",
                "confidence": round(conf, 3),
                "status": "active",
            })

        if hits["bias"] > 0:
            sev = min(10, 4 + hits["bias"])
            conf = min(1.0, 0.4 + density * 0.1 + hits["name"] * 0.05)
            findings.append({
                "type": "bias_indicator",
                "desc": f"Bias/prejudice language near Hoopes references ({hits['bias']} hits)",
                "severity": sev,
                "canon": "Canon 2; Canon 3(B)(2)",
                "confidence": round(conf, 3),
                "status": "active",
            })

        if hits["housing_case"] > 0:
            sev = min(10, 3 + hits["housing_case"])
            conf = min(1.0, 0.6 + hits["name"] * 0.05)
            findings.append({
                "type": "housing_compliance",
                "desc": (f"Housing case 2025-002760-CZ procedural references "
                         f"({hits['housing_case']} hits, {hits['procedural']} procedural)"),
                "severity": sev,
                "canon": None,
                "confidence": round(conf, 3),
                "status": "active",
            })

        if hits["procedural"] > 2 and hits["name"] >= 2:
            sev = min(10, 3 + int(density))
            conf = min(1.0, 0.55 + hits["name"] * 0.05)
            findings.append({
                "type": "procedural_issue",
                "desc": f"Procedural compliance concerns ({hits['procedural']} refs)",
                "severity": sev,
                "canon": None,
                "confidence": round(conf, 3),
                "status": "active",
            })

        return findings

    # ------------------------------------------------------------------
    def _mark_done(self, item: Any) -> None:
        item_id = item["id"] if "id" in item.keys() else item["rowid"]
        self._db_execute(
            "UPDATE ready_queue SET status = 'done' WHERE id = ?", (item_id,)
        )
        self.db.commit()
