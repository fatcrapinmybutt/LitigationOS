"""
DELTA9 — K11 Lane F Appellate Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Identifies appellate preservation, standard-of-review markers, and
appellate vehicle candidates across the entire case file universe.
"""
import json
import hashlib
import re
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_F_SIGNALS,
)

# Preservation elements
PRESERVATION_ELEMENTS = {
    'objection': {
        'description': 'Timely objection or preservation on the record',
        'keywords': ['object', 'objection', 'preserve', 'on the record', 'timely'],
    },
    'motion_denied': {
        'description': 'Motion denied or overruled — preserving error',
        'keywords': ['denied', 'overruled', 'motion denied'],
    },
    'constitutional_issue': {
        'description': 'Constitutional issue raised for appellate review',
        'keywords': ['constitutional', 'due process', 'equal protection', 'fundamental right'],
    },
}

# Standard of review elements
STANDARD_OF_REVIEW_ELEMENTS = {
    'de_novo': {
        'description': 'De novo review for questions of law',
        'keywords': ['de novo', 'question of law', 'constitutional issue', 'statutory interpretation'],
    },
    'abuse_of_discretion': {
        'description': 'Abuse of discretion standard',
        'keywords': ['abuse of discretion', 'discretionary', 'unreasonable', 'no reasonable'],
    },
    'clear_error': {
        'description': 'Clearly erroneous standard for factual findings',
        'keywords': ['clearly erroneous', 'factual finding', 'manifest error'],
    },
}

# Appellate vehicle elements
APPELLATE_VEHICLE_ELEMENTS = {
    'claim_of_right': {
        'description': 'Claim of appeal as of right under MCR 7.203',
        'keywords': ['claim of appeal', 'mcr 7.203', 'final order', 'final judgment'],
    },
    'leave_to_appeal': {
        'description': 'Application for leave to appeal under MCR 7.205',
        'keywords': ['leave to appeal', 'mcr 7.205', 'interlocutory', 'not final'],
    },
    'superintending': {
        'description': 'Superintending control or extraordinary relief under MCR 7.305',
        'keywords': ['superintending control', 'mcr 7.305', 'extraordinary', 'original action', 'mandamus'],
    },
}


class LaneFAppellateIntel(Agent9999):
    """Lane F Appellate Intelligence — preservation, standard-of-review, and appellate vehicle mapping."""

    def __init__(self):
        super().__init__(agent_id="K11-APPELLATE")
        self.parallel_workers = 8
        self.item_timeout = 15
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

        content_lower = content.lower()

        # Detect lane F signals
        lane_f_hits = [s for s in LANE_F_SIGNALS if s in content_lower]

        if not lane_f_hits:
            raise SkipItemError(f"No appellate signals in {file_name}")

        # Map preservation elements
        preservation_results = self._map_elements(content, content_lower, PRESERVATION_ELEMENTS)

        # Map standard of review elements
        standard_results = self._map_elements(content, content_lower, STANDARD_OF_REVIEW_ELEMENTS)

        # Map appellate vehicle elements
        vehicle_results = self._map_elements(content, content_lower, APPELLATE_VEHICLE_ELEMENTS)

        # Score
        appellate_score = 0.0
        appellate_score += min(3.0, len(lane_f_hits) * 0.5)
        preservation_present = [k for k, v in preservation_results.items() if v['hit_count'] > 0]
        standard_present = [k for k, v in standard_results.items() if v['hit_count'] > 0]
        vehicle_present = [k for k, v in vehicle_results.items() if v['hit_count'] > 0]
        appellate_score += len(preservation_present) * 0.5
        appellate_score += len(standard_present) * 0.5
        # Vehicle matches are high value — weight extra
        appellate_score += len(vehicle_present) * 1.0
        appellate_score = min(10.0, appellate_score)

        analysis = {
            'file_name': file_name,
            'lane_f_signals': lane_f_hits[:10],
            'preservation': preservation_results,
            'standard_of_review': standard_results,
            'appellate_vehicles': vehicle_results,
            'appellate_score': appellate_score,
        }

        metadata = {
            'preservation_elements': preservation_present,
            'standard_elements': standard_present,
            'vehicle_elements': vehicle_present,
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'appellate_pattern', ?, 'F', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K11|appellate|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), appellate_score, self.agent_id)
        )
        self.db.commit()

    def _map_elements(self, content: str, content_lower: str,
                      elements: Dict[str, dict]) -> Dict[str, dict]:
        """Map element keywords against content, return results per element."""
        results = {}
        for elem_key, elem_def in elements.items():
            hits = []
            for kw in elem_def['keywords']:
                for m in re.finditer(re.escape(kw), content_lower):
                    start = max(0, m.start() - 120)
                    end = min(len(content), m.end() + 120)
                    hits.append(content[start:end].strip())
            results[elem_key] = {
                'element': elem_key,
                'description': elem_def['description'],
                'hit_count': len(hits),
                'excerpts': hits[:5],
            }
        return results
