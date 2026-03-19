"""
J04 Canon Mapper — Maps judicial actions to Michigan Code of Judicial Conduct violations.
Canon 1 (integrity), Canon 2 (impartiality), Canon 3 (duties).
"""
import re
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Canon definitions with trigger patterns
CANON_RULES: Dict[str, Dict[str, Any]] = {
    "Canon 1": {
        "label": "Integrity and Independence of the Judiciary",
        "patterns": re.compile(
            r'(?i)integrit(?:y|ies)|independen(?:ce|t)|'
            r'public\s+confidence|dignit(?:y|ies)|'
            r'undermin(?:e|ing)\s+(?:court|judicial|public\s+trust)'
        ),
    },
    "Canon 2": {
        "label": "Impartiality and Appearance of Impropriety",
        "patterns": re.compile(
            r'(?i)impartial|appearance\s+of\s+(?:impropri|bias)|'
            r'(?:un)?fair(?:ness)?|prejudg|predetermin|'
            r'one[- ]sided|favor(?:itism|ing)|appear(?:ance|s)\s+(?:of\s+)?bias'
        ),
    },
    "Canon 3(A)(3)": {
        "label": "Ex Parte Communications",
        "patterns": re.compile(
            r'(?i)ex\s*parte|without\s+notice\s+to|'
            r'unilateral\s+(?:communication|contact|order)|'
            r'one[- ]party\s+(?:communication|contact|hearing)|'
            r'outside\s+(?:the\s+)?presence'
        ),
    },
    "Canon 3(B)(2)": {
        "label": "Bias and Prejudice Indicators",
        "patterns": re.compile(
            r'(?i)bias(?:ed)?|prejudic(?:e|ed|ial)|'
            r'hostil(?:e|ity)|antagoni(?:sm|stic)|'
            r'disparag(?:e|ing)|ridicul(?:e|ed|ing)|'
            r'demean(?:ed|ing)|belittl(?:e|ing)'
        ),
    },
    "Canon 3(C)(1)": {
        "label": "Administrative Duties — Disqualification",
        "patterns": re.compile(
            r'(?i)disqualif(?:y|ication|ied)|recus(?:e|al|ed)|'
            r'personal\s+(?:bias|knowledge|interest)|'
            r'(?:should|must|required\s+to)\s+(?:disqualify|recuse|step\s+aside)|'
            r'mcr\s+2\.003'
        ),
    },
}


class CanonMapper(Agent9999):
    """Map judicial findings to specific Canon violations."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J04-CANON-MAP", **kwargs)
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
        self.db.commit()

    # ------------------------------------------------------------------
    def _validate_preconditions(self) -> None:
        try:
            row = self._db_execute(
                """SELECT COUNT(*) as cnt FROM judicial_findings
                   WHERE (canon_ref IS NULL OR canon_ref = '')"""
            ).fetchone()
            if row and row["cnt"] > 0:
                return
        except Exception:
            pass
        # Also check for queue items we can scan directly
        try:
            row2 = self._db_execute(
                """SELECT COUNT(*) as cnt FROM ready_queue
                   WHERE queue_type='judicial' AND status='pending'"""
            ).fetchone()
            if row2 and row2["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No unmapped findings or pending queue items")

    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        """Get judicial findings that need canon mapping."""
        try:
            rows = self._db_execute(
                """SELECT * FROM judicial_findings
                   WHERE (canon_ref IS NULL OR canon_ref = '')
                   AND status != 'NEEDS_REVIEW'"""
            ).fetchall()
            if rows:
                return rows
        except Exception:
            pass
        # Fallback: also pick up findings from other agents even with canon_ref
        # to validate/augment mapping
        try:
            rows = self._db_execute(
                """SELECT * FROM judicial_findings
                   WHERE agent_id != ?
                   ORDER BY created_at DESC LIMIT 200""",
                (self.agent_id,),
            ).fetchall()
            return rows if rows else []
        except Exception:
            return []

    # ------------------------------------------------------------------
    def _process_item(self, item: Any) -> None:
        finding_id = item["id"]
        description = item["description"] or ""
        existing_canon = item["canon_ref"] or ""
        source_file_id = item["source_file_id"]

        # Scan description text for canon triggers
        matched_canons = self._match_canons(description)

        # Also scan the source file content if available
        if source_file_id:
            content = self._read_file_content(source_file_id)
            if content:
                file_canons = self._match_canons(content)
                matched_canons.update(file_canons)

        if not matched_canons:
            return  # no canon mapping found

        new_canon_ref = "; ".join(sorted(matched_canons))
        # Merge with existing if present
        if existing_canon:
            all_canons = set(existing_canon.split("; ")) | matched_canons
            new_canon_ref = "; ".join(sorted(all_canons))

        self._db_execute(
            "UPDATE judicial_findings SET canon_ref = ? WHERE id = ?",
            (new_canon_ref, finding_id),
        )
        self.db.commit()

    # ------------------------------------------------------------------
    def _match_canons(self, text: str) -> set:
        matched = set()
        for canon_key, rule in CANON_RULES.items():
            if rule["patterns"].search(text):
                matched.add(canon_key)
        return matched
