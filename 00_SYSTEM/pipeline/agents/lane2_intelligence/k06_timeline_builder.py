"""
DELTA9 — K06 Timeline Builder Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Extracts ALL dates/events across processed content. Classifies event types.
Tracks the 329-day separation as a critical timeline marker.
"""
import json
import hashlib
import re
from typing import Any, List, Optional, Tuple

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
    LaneCrossContaminationError,
)

# Date extraction patterns
DATE_PATTERNS = [
    # MM/DD/YYYY or MM/DD/YY
    re.compile(r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b'),
    # YYYY-MM-DD (ISO format)
    re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),
    # Month DD, YYYY
    re.compile(
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)'
        r'\s+\d{1,2},?\s*\d{4})\b',
        re.IGNORECASE
    ),
    # DD Month YYYY
    re.compile(
        r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        r',?\s*\d{4})\b',
        re.IGNORECASE
    ),
    # Mon DD, YYYY (abbreviated)
    re.compile(
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s*\d{4})\b',
        re.IGNORECASE
    ),
]

# Event type classification keywords
EVENT_CLASSIFIERS = {
    'ORDER': ['order', 'ordered', 'it is ordered', 'hereby ordered', 'court order',
              'stipulated order', 'consent order', 'temporary order'],
    'HEARING': ['hearing', 'oral argument', 'motion hearing', 'evidentiary hearing',
                'pretrial', 'conference', 'arraignment', 'show cause'],
    'SERVICE': ['served', 'service', 'proof of service', 'certified mail',
                'personal service', 'process server', 'return of service'],
    'FILING': ['filed', 'filing', 'motion', 'petition', 'complaint', 'answer',
               'response', 'brief', 'appeal', 'claim of appeal', 'application'],
    'INCIDENT': ['incident', 'occurred', 'happened', 'took place', 'event',
                 'arrested', 'assault', 'violation', 'trespass', 'contact'],
}

# Critical timeline marker
SEPARATION_329_DAYS = '329-day'


class TimelineBuilder(Agent9999):
    """Timeline Builder Intelligence — date/event extraction and classification."""

    def __init__(self):
        super().__init__(agent_id="K06-TIMELINE")
        self.parallel_workers = 8   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200

    def _validate_preconditions(self) -> None:
        cursor = self._db_execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('files','atoms')"
        )
        found = {row[0] for row in cursor.fetchall()}
        for tbl in ('files', 'atoms'):
            if tbl not in found:
                raise FatalAgentError(f"Required table '{tbl}' missing — run orchestrator first")

    def _ensure_tables(self) -> None:
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS atoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                atom_type TEXT NOT NULL,
                content TEXT,
                score REAL,
                metadata TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def _get_work_items(self) -> list:
        cursor = self._db_execute("""
            SELECT id, full_path, file_name, meek_lane
            FROM files
            WHERE processed = 1
        """)
        return cursor.fetchall()

    def _process_item(self, item: Any) -> None:
        file_id = item['id']
        full_path = item['full_path']
        file_name = item['file_name']
        meek_lane = item['meek_lane'] or ''

        try:
            with open(self.long_path(full_path), 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except (OSError, PermissionError) as e:
            raise SkipItemError(f"Cannot read {file_name}: {e}")

        if not content.strip():
            raise SkipItemError(f"Empty file: {file_name}")

        events = self._extract_events(content, file_name, meek_lane)

        if not events:
            raise SkipItemError(f"No date/events found in {file_name}")

        # Check for 329-day separation marker
        has_329_marker = bool(re.search(r'(?i)329[\s-]*day', content))

        for event in events:
            event['source_file'] = file_name
            event['meek_lane'] = meek_lane
            event['has_329_marker'] = has_329_marker

            score = self._score_event(event)

            self._db_execute(
                """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
                   VALUES (?, 'event', ?, 'C', ?, ?, 'EVIDENCE_FACT', ?)""",
                (hashlib.sha1(f'K06|event|{file_id}|{event["date"]}'.encode()).hexdigest()[:16],
                 file_id, json.dumps(event), score, self.agent_id)
            )

        self.db.commit()

    def _extract_events(self, content: str, file_name: str, meek_lane: str) -> List[dict]:
        """Extract all date-anchored events from content."""
        events = []
        seen_dates = set()

        for pattern in DATE_PATTERNS:
            for m in pattern.finditer(content):
                date_str = m.group(1)

                # Deduplicate within same file
                dedup_key = (date_str, m.start() // 500)  # group by ~500 char blocks
                if dedup_key in seen_dates:
                    continue
                seen_dates.add(dedup_key)

                # Extract surrounding context
                ctx_start = max(0, m.start() - 200)
                ctx_end = min(len(content), m.end() + 200)
                context = content[ctx_start:ctx_end].strip()

                # Classify event type
                event_type = self._classify_event(context)

                events.append({
                    'date': date_str,
                    'event_type': event_type,
                    'context': context[:500],
                    'position': m.start(),
                })

        return events

    def _classify_event(self, context: str) -> str:
        """Classify event type from surrounding context."""
        context_lower = context.lower()
        scores = {}

        for event_type, keywords in EVENT_CLASSIFIERS.items():
            score = sum(1 for kw in keywords if kw in context_lower)
            if score > 0:
                scores[event_type] = score

        if scores:
            return max(scores, key=scores.get)
        return 'UNKNOWN'

    def _score_event(self, event: dict) -> float:
        """Score event importance."""
        score = 1.0

        # Known event types score higher
        if event['event_type'] != 'UNKNOWN':
            score += 2.0

        # Court orders are highest priority
        if event['event_type'] == 'ORDER':
            score += 3.0
        elif event['event_type'] == 'HEARING':
            score += 2.0
        elif event['event_type'] == 'FILING':
            score += 1.5

        # 329-day marker is critical
        if event.get('has_329_marker'):
            score += 3.0

        return min(10.0, score)
