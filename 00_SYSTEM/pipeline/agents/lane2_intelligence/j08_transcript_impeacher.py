"""
J08 Transcript Impeacher — Processes hearing transcripts to extract testimony,
identify prior inconsistent statements (MRE 613/801(d)(1)), and build
impeachment indices per witness.
"""
import re
from typing import Any, Dict, List, Optional

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
)

# Transcript detection patterns
_TRANSCRIPT_MARKERS = re.compile(
    r'(?i)transcript|hearing|deposition|Q:|A:|THE COURT:|MR\.|MS\.'
)

# Speaker extraction
_SPEAKER_LINE = re.compile(
    r'^(?:\s*\d+\s+)?'                           # optional line number
    r'(Q|A|THE COURT|MR\.\s*\w+|MS\.\s*\w+|'
    r'THE WITNESS|BY\s+\w+[\s\w]*)'               # speaker label
    r'[:\.]?\s*(.*)',                               # colon/period + content
    re.MULTILINE,
)

# Inconsistency triggers
_CONTRADICTION_PATTERNS = [
    re.compile(r'(?i)(?:I\s+)?(?:never|did\s+not|didn\'t)\s+(?:say|state|testif)', re.IGNORECASE),
    re.compile(r'(?i)(?:that\'?s?\s+)?(?:not\s+(?:what|how)\s+(?:I|you))', re.IGNORECASE),
    re.compile(r'(?i)(?:correct|true)\s+that\s+(?:you\s+)?(?:previously|earlier|before)', re.IGNORECASE),
    re.compile(r'(?i)prior\s+(?:statement|testimony|deposition)', re.IGNORECASE),
    re.compile(r'(?i)inconsisten(?:t|cy)|contradic(?:t|tion)', re.IGNORECASE),
    re.compile(r'(?i)(?:do\s+you\s+)?recall\s+(?:saying|stating|testifying)', re.IGNORECASE),
    re.compile(r'(?i)impeach|MRE\s+613|MRE\s+801', re.IGNORECASE),
]


class TranscriptImpeacher(Agent9999):
    """Extract testimony and build impeachment indices from transcripts."""

    def __init__(self, **kwargs):
        super().__init__(agent_id="J08-IMPEACH", **kwargs)
        self.confidence_threshold = 0.7
        self.batch_size = 2000  # transcripts are large

    # ------------------------------------------------------------------
    def _ensure_tables(self) -> None:
        # atoms table already exists with schema:
        # id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by
        # No need to CREATE — just verify it exists
        self._db_execute("SELECT 1 FROM atoms LIMIT 1")
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
                   WHERE LOWER(file_name) LIKE '%transcript%'
                      OR LOWER(file_name) LIKE '%hearing%'
                      OR LOWER(file_name) LIKE '%deposition%'"""
            ).fetchone()
            if row2 and row2["cnt"] > 0:
                return
        except Exception:
            pass
        self._log("WARN", "No pending queue items or transcript files found")

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
        # Resolve the file's actual meek_lane from the database
        file_row = self._db_execute(
            "SELECT meek_lane FROM files WHERE id = ?", (file_id,)
        ).fetchone()
        file_meek_lane = file_row["meek_lane"] if file_row and file_row["meek_lane"] else "A"
        content = self._read_file_content(file_id)
        if not content:
            raise SkipItemError(f"No readable content for file_id={file_id}")

        # Verify this looks like a transcript
        if not _TRANSCRIPT_MARKERS.search(content):
            self._mark_done(item)
            return

        testimony = self._extract_testimony(content)
        contradictions = self._find_contradictions(content, testimony)

        for c in contradictions:
            confidence = c.get("confidence", 0.6)
            status = "active" if confidence >= self.confidence_threshold else "NEEDS_REVIEW"

            import json
            atom_id = f"J08-{file_id}-{hash(c['content']) & 0xFFFFFFFF}"
            self._db_execute(
                """INSERT OR IGNORE INTO atoms
                   (id, atom_type, source_file_id, meek_lane, title, content,
                    confidence, posture, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (atom_id,
                 "contradiction",
                 file_id,
                 file_meek_lane,
                 c['title'],
                 c['content'],
                 round(confidence, 3),
                 "EVIDENCE_FACT" if confidence >= self.confidence_threshold else "ALLEGATION",
                 self.agent_id),
            )
        self.db.commit()

        if testimony:
            self._build_impeachment_index(file_id, testimony, contradictions, file_meek_lane)

        self._mark_done(item)

    # ------------------------------------------------------------------
    def _extract_testimony(self, content: str) -> Dict[str, List[str]]:
        """Group testimony lines by speaker."""
        testimony: Dict[str, List[str]] = {}
        for match in _SPEAKER_LINE.finditer(content):
            speaker = match.group(1).strip().upper()
            text = match.group(2).strip()
            if text:
                testimony.setdefault(speaker, []).append(text)
        return testimony

    def _find_contradictions(self, content: str,
                             testimony: Dict[str, List[str]]) -> List[dict]:
        """Scan for prior inconsistent statement indicators."""
        contradictions: List[dict] = []

        lines = content.split("\n")
        for i, line in enumerate(lines):
            for pat in _CONTRADICTION_PATTERNS:
                if pat.search(line):
                    context_start = max(0, i - 3)
                    context_end = min(len(lines), i + 4)
                    context = "\n".join(lines[context_start:context_end])

                    speaker = self._identify_speaker_at(lines, i)
                    severity = 5
                    confidence = 0.6

                    # Boost if explicit impeachment language
                    if re.search(r'(?i)impeach|MRE\s+613|MRE\s+801', line):
                        severity = 7
                        confidence = 0.85
                    elif re.search(r'(?i)prior\s+(?:statement|testimony)', line):
                        severity = 6
                        confidence = 0.75

                    contradictions.append({
                        "title": f"Potential inconsistency — {speaker or 'Unknown speaker'}",
                        "content": context,
                        "severity": severity,
                        "confidence": confidence,
                        "metadata": {
                            "speaker": speaker,
                            "line_number": i + 1,
                            "rule_basis": "MRE 613 / MRE 801(d)(1)",
                        },
                    })
                    break  # one match per line

        return contradictions

    def _identify_speaker_at(self, lines: List[str], idx: int) -> Optional[str]:
        """Walk backward to find the nearest speaker label."""
        for i in range(idx, max(idx - 10, -1), -1):
            match = _SPEAKER_LINE.match(lines[i])
            if match:
                return match.group(1).strip()
        return None

    def _build_impeachment_index(self, file_id: int,
                                 testimony: Dict[str, List[str]],
                                 contradictions: List[dict],
                                 file_meek_lane: str = "A") -> None:
        """Build per-witness impeachment index atom."""
        import json
        witnesses = set()
        for c in contradictions:
            speaker = c.get("metadata", {}).get("speaker")
            if speaker:
                witnesses.add(speaker)

        for witness in witnesses:
            witness_contradictions = [
                c for c in contradictions
                if c.get("metadata", {}).get("speaker") == witness
            ]
            if not witness_contradictions:
                continue

            index_content = [
                f"IMPEACHMENT INDEX — {witness}",
                f"Contradictions found: {len(witness_contradictions)}",
                f"Rule basis: MRE 613 (prior inconsistent statements), "
                f"MRE 801(d)(1) (prior statement by declarant-witness)",
                "",
            ]
            for idx, c in enumerate(witness_contradictions, 1):
                index_content.append(f"  [{idx}] Line {c['metadata'].get('line_number', '?')}: "
                                     f"{c['title']}")

            avg_conf = sum(c["confidence"] for c in witness_contradictions) / len(witness_contradictions)
            status = "active" if avg_conf >= self.confidence_threshold else "NEEDS_REVIEW"

            self._db_execute(
                """INSERT OR IGNORE INTO atoms
                   (id, atom_type, source_file_id, meek_lane, title, content,
                    confidence, posture, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"J08-imp-{file_id}-{witness[:20]}",
                 "impeachment_index",
                 file_id,
                 file_meek_lane,
                 f"Impeachment Index — {witness}",
                 "\n".join(index_content),
                 round(avg_conf, 3),
                 "EVIDENCE_FACT" if avg_conf >= self.confidence_threshold else "ALLEGATION",
                 self.agent_id),
            )
        self.db.commit()

    # ------------------------------------------------------------------
    def _mark_done(self, item: Any) -> None:
        keys = item.keys()
        if "queue_type" in keys or "claimed_by" in keys:
            item_id = item["id"] if "id" in keys else item["rowid"]
            self._db_execute(
                "UPDATE ready_queue SET status = 'done' WHERE id = ?", (item_id,)
            )
            self.db.commit()
