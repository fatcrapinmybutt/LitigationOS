"""
J07 Ex Parte Detector — Scans ALL content for ex parte communication indicators.
Detects orders without notice, one-sided hearings, improper communications.
"""
import re
from typing import Any, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Ex parte detection patterns
_EXPARTE_PATTERNS = {
    "direct": re.compile(r'(?i)ex\s*parte'),
    "no_notice": re.compile(r'(?i)without\s+notice|no\s+notice|lack\s+of\s+notice'),
    "no_hearing": re.compile(r'(?i)no\s+hearing|without\s+(?:a\s+)?hearing|denied\s+hearing'),
    "unilateral": re.compile(r'(?i)unilateral\s+order|unilateral\s+action|unilateral\s+decision'),
    "one_party": re.compile(
        r'(?i)one[- ]party|(?:only|just)\s+(?:plaintiff|defendant|petitioner|respondent)\s+'
        r'(?:present|appeared|attended)'
    ),
    "communication": re.compile(
        r'(?i)communicat(?:ion|ed|ing)\s+(?:with|between)\s+'
        r'(?:judge|court|(?:one|single)\s+party)'
    ),
}

# Context patterns: help confirm ex parte vs general mention
_CONTEXT_PATTERNS = {
    "judge_ref": re.compile(r'(?i)judge|court|honor|bench'),
    "docket_ref": re.compile(r'(?i)case\s+no|docket|file\s+no|\d{4}[-]\d{6}'),
    "order_ref": re.compile(r'(?i)order|ruling|judgment|decree|stipulation'),
}


class ExParteDetector(Agent9999):
    """Detect ex parte communications across all ingested content."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J07-EXPARTE", **kwargs)
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
                "SELECT COUNT(*) as cnt FROM files"
            ).fetchone()
            if row2 and row2["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No pending queue items or files to scan for ex parte")

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
        if rows:
            return rows
        # Fallback: scan files table directly
        try:
            return self._db_execute(
                "SELECT id, full_path FROM files ORDER BY id LIMIT ?",
                (self.batch_size,),
            ).fetchall()
        except Exception:
            return []

    # ------------------------------------------------------------------
    def _process_item(self, item: Any) -> None:
        keys = item.keys()
        file_id = item["file_id"] if "file_id" in keys else item["id"]
        content = self._read_file_content(file_id)
        if not content:
            raise SkipItemError(f"No readable content for file_id={file_id}")

        # Scan for ex parte patterns
        hits = {name: pat.findall(content) for name, pat in _EXPARTE_PATTERNS.items()}
        total_hits = sum(len(v) for v in hits.values())

        if total_hits == 0:
            self._mark_done(item)
            return

        # Context analysis
        ctx = {name: bool(pat.search(content)) for name, pat in _CONTEXT_PATTERNS.items()}
        ctx_score = sum(ctx.values())  # 0-3

        severity = self._compute_severity(hits, ctx_score)
        confidence = self._compute_confidence(hits, ctx_score, len(content))
        judge = self._detect_judge(content)
        status = "active" if confidence >= self.confidence_threshold else "NEEDS_REVIEW"

        description = self._build_description(hits)

        self._db_execute(
            """INSERT OR IGNORE INTO judicial_findings
               (judge, finding_type, description, severity,
                source_file_id, canon_ref, confidence, status, agent_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (judge, "ex_parte", description, severity,
             file_id, "Canon 3(A)(3)", round(confidence, 3),
             status, self.agent_id),
        )
        self.db.commit()
        self._mark_done(item)

    # ------------------------------------------------------------------
    def _compute_severity(self, hits: dict, ctx_score: int) -> int:
        base = 3
        if len(hits.get("direct", [])) > 0:
            base += 2
        if len(hits.get("no_notice", [])) > 0:
            base += 2
        if len(hits.get("unilateral", [])) > 0:
            base += 1
        if ctx_score >= 2:
            base += 1
        return min(10, base)

    def _compute_confidence(self, hits: dict, ctx_score: int,
                            content_length: int) -> float:
        total = sum(len(v) for v in hits.values())
        base = 0.4
        base += min(0.3, total * 0.05)
        base += ctx_score * 0.1
        if len(hits.get("direct", [])) > 0:
            base += 0.1
        return min(1.0, base)

    def _build_description(self, hits: dict) -> str:
        parts = []
        for name, matches in hits.items():
            if matches:
                label = name.replace("_", " ").title()
                parts.append(f"{label}: {len(matches)} hit(s)")
        return "Ex parte indicators — " + "; ".join(parts)

    def _detect_judge(self, content: str) -> str:
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
        keys = item.keys()
        if "queue_type" in keys or "claimed_by" in keys:
            item_id = item["id"] if "id" in keys else item["rowid"]
            self._db_execute(
                "UPDATE ready_queue SET status = 'done' WHERE id = ?", (item_id,)
            )
            self.db.commit()
