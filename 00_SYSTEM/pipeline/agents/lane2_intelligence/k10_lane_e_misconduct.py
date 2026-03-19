"""
DELTA9 — K10 Lane E Judicial Misconduct Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Identifies judicial bias, canon violations, procedural misconduct, and
McNeill-specific patterns across the entire case file universe.
"""
import json
import hashlib
import re
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_E_SIGNALS,
)

# Bias elements
BIAS_ELEMENTS = {
    'appearance_of_bias': {
        'description': 'Appearance of bias or prejudgment',
        'keywords': ['bias', 'prejudice', 'predetermin', 'preconceiv', 'one-sided', 'favor'],
    },
    'actual_bias': {
        'description': 'Actual bias through personal interest or relationship',
        'keywords': ['personal interest', 'relationship', 'financial', 'family connection'],
    },
    'demonstrated_bias': {
        'description': 'Demonstrated bias through hostile or dismissive conduct',
        'keywords': ['hostile', 'dismissive', 'disregard', 'ignore', 'refuse to hear'],
    },
}

# Canon violation elements
CANON_VIOLATION_ELEMENTS = {
    'canon_1': {
        'description': 'Canon 1 — Integrity and independence of the judiciary',
        'keywords': ['integrity', 'independence', 'judicial system'],
    },
    'canon_2': {
        'description': 'Canon 2 — Avoiding impropriety and appearance of impropriety',
        'keywords': ['appearance of impropriety', 'confidence', 'avoid impropriety'],
    },
    'canon_3': {
        'description': 'Canon 3 — Impartial and diligent performance of duties',
        'keywords': ['impartially', 'diligently', 'fair', 'equal', 'without prejudice', 'ex parte'],
    },
    'canon_4': {
        'description': 'Canon 4 — Extrajudicial activities and political conduct',
        'keywords': ['extrajudicial', 'outside activities', 'political'],
    },
}

# Procedural misconduct elements
PROCEDURAL_MISCONDUCT_ELEMENTS = {
    'ex_parte': {
        'description': 'Ex parte communications or one-sided proceedings',
        'keywords': ['ex parte', 'one-sided', 'without notice', 'unilateral communication'],
    },
    'denial_hearing': {
        'description': 'Denial of hearing or opportunity to be heard',
        'keywords': ['denied hearing', 'refused hearing', 'no opportunity', 'not heard'],
    },
    'arbitrary_action': {
        'description': 'Arbitrary or capricious judicial action',
        'keywords': ['arbitrary', 'capricious', 'without basis', 'no finding', 'no record'],
    },
}

# McNeill-specific pattern markers
MCNEILL_SPECIFIC = {
    'mcneill_pattern': {
        'description': 'Direct references to Judge McNeill conduct',
        'keywords': ['mcneill', 'judge mcneill', 'hon. mcneill'],
    },
}


class LaneEMisconductIntel(Agent9999):
    """Lane E Misconduct Intelligence — judicial bias, canon violations, and procedural misconduct mapping."""

    def __init__(self):
        super().__init__(agent_id="K10-MISCONDUCT")
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

        # Detect lane E signals
        lane_e_hits = [s for s in LANE_E_SIGNALS if s in content_lower]

        if not lane_e_hits:
            raise SkipItemError(f"No misconduct signals in {file_name}")

        # Map bias elements
        bias_results = self._map_elements(content, content_lower, BIAS_ELEMENTS)

        # Map canon violation elements
        canon_results = self._map_elements(content, content_lower, CANON_VIOLATION_ELEMENTS)

        # Map procedural misconduct elements
        procedural_results = self._map_elements(content, content_lower, PROCEDURAL_MISCONDUCT_ELEMENTS)

        # Map McNeill-specific patterns
        mcneill_results = self._map_elements(content, content_lower, MCNEILL_SPECIFIC)

        # Score
        misconduct_score = 0.0
        misconduct_score += min(3.0, len(lane_e_hits) * 0.5)
        bias_present = [k for k, v in bias_results.items() if v['hit_count'] > 0]
        canon_present = [k for k, v in canon_results.items() if v['hit_count'] > 0]
        procedural_present = [k for k, v in procedural_results.items() if v['hit_count'] > 0]
        mcneill_present = [k for k, v in mcneill_results.items() if v['hit_count'] > 0]
        misconduct_score += len(bias_present) * 0.5
        misconduct_score += len(canon_present) * 0.5
        misconduct_score += len(procedural_present) * 0.5
        # McNeill-specific hits get extra weight
        misconduct_score += len(mcneill_present) * 1.0
        misconduct_score = min(10.0, misconduct_score)

        analysis = {
            'file_name': file_name,
            'lane_e_signals': lane_e_hits[:10],
            'bias': bias_results,
            'canon_violations': canon_results,
            'procedural_misconduct': procedural_results,
            'mcneill_specific': mcneill_results,
            'misconduct_score': misconduct_score,
        }

        metadata = {
            'bias_elements': bias_present,
            'canon_elements': canon_present,
            'procedural_elements': procedural_present,
            'mcneill_elements': mcneill_present,
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'misconduct_pattern', ?, 'E', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K10|misconduct|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), misconduct_score, self.agent_id)
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
