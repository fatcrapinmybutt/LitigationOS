"""
DELTA9 — K09 Lane D PPO Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Identifies PPO violation evidence, contempt patterns, and bond condition breaches.
Maps protective-order elements from case files touching Lane D (PPO) or Lane A (custody overlap).
"""
import json
import hashlib
import re
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_D_SIGNALS,
)

# PPO violation elements
PPO_VIOLATION_ELEMENTS = {
    'active_order': {
        'description': 'Existence of an active protection order',
        'keywords': ['ppo', 'protection order', 'no contact', 'restrain'],
    },
    'violation_conduct': {
        'description': 'Conduct constituting a violation of the order',
        'keywords': ['violat', 'contact', 'approach', 'harass', 'stalk', 'threaten', 'within feet'],
    },
    'law_enforcement': {
        'description': 'Law enforcement involvement or reporting',
        'keywords': ['police', 'arrest', 'report', '911', 'officer', 'incident'],
    },
}

# Contempt elements
CONTEMPT_ELEMENTS = {
    'court_order': {
        'description': 'Existence of a clear and definite court order',
        'keywords': ['ordered', 'shall not', 'prohibited', 'restrain'],
    },
    'willful_violation': {
        'description': 'Willful and deliberate violation of the order',
        'keywords': ['willful', 'knowing', 'intentional', 'deliberate'],
    },
    'ability_to_comply': {
        'description': 'Respondent had the ability to comply with the order',
        'keywords': ['able to', 'capable', 'ability', 'could have'],
    },
}

# Bond condition elements
BOND_ELEMENTS = {
    'conditions': {
        'description': 'Specific bond conditions imposed',
        'keywords': ['bond', 'condition', 'release', 'tether', 'gps', 'no contact'],
    },
    'violation': {
        'description': 'Violation of bond conditions',
        'keywords': ['violat bond', 'breach condition'],
    },
}


class LaneDPPOIntel(Agent9999):
    """Lane D PPO Intelligence — protective-order violation, contempt, and bond breach mapping."""

    def __init__(self):
        super().__init__(agent_id="K09-PPO-INTEL")
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
              AND (meek_lane LIKE '%D%' OR meek_lane LIKE '%A%')
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

        # Detect lane D signals
        lane_d_hits = [s for s in LANE_D_SIGNALS if s in content_lower]

        if not lane_d_hits:
            raise SkipItemError(f"No PPO signals in {file_name}")

        # Map PPO violation elements
        ppo_results = self._map_elements(content, content_lower, PPO_VIOLATION_ELEMENTS)

        # Map contempt elements
        contempt_results = self._map_elements(content, content_lower, CONTEMPT_ELEMENTS)

        # Map bond elements
        bond_results = self._map_elements(content, content_lower, BOND_ELEMENTS)

        # Score
        ppo_score = 0.0
        ppo_score += min(3.0, len(lane_d_hits) * 0.5)
        ppo_present = [k for k, v in ppo_results.items() if v['hit_count'] > 0]
        contempt_present = [k for k, v in contempt_results.items() if v['hit_count'] > 0]
        bond_present = [k for k, v in bond_results.items() if v['hit_count'] > 0]
        ppo_score += len(ppo_present) * 0.5
        ppo_score += len(contempt_present) * 0.5
        ppo_score += len(bond_present) * 0.5
        ppo_score = min(10.0, ppo_score)

        analysis = {
            'file_name': file_name,
            'lane_d_signals': lane_d_hits[:10],
            'ppo_violation': ppo_results,
            'contempt': contempt_results,
            'bond': bond_results,
            'ppo_score': ppo_score,
        }

        metadata = {
            'ppo_elements': ppo_present,
            'contempt_elements': contempt_present,
            'bond_elements': bond_present,
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'ppo_pattern', ?, 'D', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K09|ppo|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), ppo_score, self.agent_id)
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
