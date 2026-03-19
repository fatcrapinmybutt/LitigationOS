"""
DELTA9 — L05 Citation Validator
Tier L · Lane 2 Intelligence · MAX LEVEL 9999++

Verifies every MCR/MCL/MRE citation found in atoms.
Checks format correctness, valid ranges, and sanctions risk.
"""
import json
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Known valid citation ranges
VALID_RANGES = {
    "MCL": (1, 800),       # Michigan Compiled Laws: chapters 1–800
    "MCR": (1, 9),         # Michigan Court Rules: chapters 1–9
    "MRE": (100, 1200),    # Michigan Rules of Evidence: rules 100–1200
}

# Citation extraction patterns
CITATION_PATTERNS = [
    re.compile(r'\bMCL\s+(\d+)\.(\d+[a-z]?(?:\(\d+\))?)', re.IGNORECASE),
    re.compile(r'\bMCR\s+(\d+)\.(\d+[a-z]?(?:\(\d+\))?)', re.IGNORECASE),
    re.compile(r'\bMRE\s+(\d+)', re.IGNORECASE),
    re.compile(r'\b42\s+USC\s+[§]?\s*(\d+)', re.IGNORECASE),
    re.compile(r'\b28\s+USC\s+[§]?\s*(\d+)', re.IGNORECASE),
]

# Pattern to parse citation type and primary number
_CITE_TYPE_RE = re.compile(r'^(MCL|MCR|MRE)\s+(\d+)', re.IGNORECASE)


class CitationValidator(Agent9999):
    """Validate all MCR/MCL/MRE citations in atoms for format and range correctness."""

    def __init__(self):
        super().__init__(agent_id="L05-CITE-VALID")
        self.parallel_workers = 4   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='atoms'"
        )
        if not cursor.fetchone():
            raise FatalAgentError("Required table 'atoms' missing — run Tier 1 first")

    def _ensure_tables(self) -> None:
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS atoms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                atom_type   TEXT,
                content     TEXT,
                posture     TEXT,
                meek_lane   TEXT,
                source_file TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def _get_work_items(self) -> list:
        rows = self._db_execute(
            "SELECT id, atom_type, content, meek_lane FROM atoms "
            "WHERE content IS NOT NULL AND LENGTH(content) > 0"
        ).fetchall()
        return rows

    def _process_item(self, item: Any) -> None:
        atom_id = item["id"]
        content = item["content"] or ""
        meek_lane = item["meek_lane"] or ""
        atom_type = (item["atom_type"] or "").upper()

        # Extract all citations from content
        citations = self._extract_citations(content)
        if not citations:
            # Sanctions risk: claims lacking any citation backing
            if atom_type in ("FACT", "FACT_ATOM", "ALLEGATION") and len(content) > 100:
                self._insert_validation(
                    atom_id, meek_lane, "sanctions_risk",
                    "Substantive claim with no citation backing — potential Rule 11 issue",
                    {"atom_id": atom_id, "content_preview": content[:200]}
                )
            return

        for cite_raw, cite_type, primary_num in citations:
            issues = []

            # Check format correctness
            if cite_type in VALID_RANGES:
                low, high = VALID_RANGES[cite_type]
                if primary_num < low or primary_num > high:
                    issues.append(
                        f"Out of range: {cite_type} {primary_num} "
                        f"(valid: {low}–{high})"
                    )

            # Check for incomplete citations (just a chapter with no section)
            if cite_type in ("MCL", "MCR") and "." not in cite_raw.split()[-1]:
                issues.append(f"Incomplete citation: {cite_raw} — missing section number")

            status = "INVALID" if issues else "VALID"
            detail = "; ".join(issues) if issues else "Format and range OK"

            self._insert_validation(
                atom_id, meek_lane, status,
                f"{cite_raw}: {detail}",
                {"citation": cite_raw, "type": cite_type, "number": primary_num,
                 "issues": issues}
            )

    def _extract_citations(self, text: str) -> List[Tuple[str, str, int]]:
        """Extract (raw_citation, type, primary_number) tuples."""
        results = []
        for pattern in CITATION_PATTERNS:
            for match in pattern.finditer(text):
                raw = match.group(0)
                m2 = _CITE_TYPE_RE.match(raw)
                if m2:
                    cite_type = m2.group(1).upper()
                    primary = int(m2.group(2))
                    results.append((raw, cite_type, primary))
                elif "USC" in raw.upper():
                    results.append((raw, "USC", 0))
        return results

    def _insert_validation(self, atom_id: int, meek_lane: str,
                           status: str, detail: str, data: dict) -> None:
        payload = json.dumps({
            "source_atom_id": atom_id,
            "validation_status": status,
            "detail": detail,
            **data,
        })
        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'citation_validation', 0, ?, ?, 1.0, 'SYSTEM', ?)""",
            (hashlib.sha1(f'L05|cite|{atom_id}'.encode()).hexdigest()[:16],
             meek_lane, payload, f'L05-CITE-VALID/{atom_id}')
        )
        self.db.commit()

    def _finalize(self) -> None:
        valid = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='citation_validation' AND content LIKE '%VALID%' AND content NOT LIKE '%INVALID%'"
        ).fetchone()[0]
        invalid = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='citation_validation' AND content LIKE '%INVALID%'"
        ).fetchone()[0]
        sanctions = self._db_execute(
            "SELECT COUNT(*) FROM atoms WHERE atom_type='citation_validation' AND content LIKE '%sanctions_risk%'"
        ).fetchone()[0]
        self._log("SUMMARY", f"Citations: {valid} valid, {invalid} invalid, {sanctions} sanctions-risk")
