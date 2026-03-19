"""
DELTA9 — K02 Lane A PPO Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Analyzes PPO/contempt content: modification grounds, due process, overbreadth.
LANE PURITY: Lane A ONLY — raises LaneCrossContaminationError on Lane B signals.
"""
import json
import hashlib
import re
from typing import Any

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
    LaneCrossContaminationError,
)

PPO_PATTERN = re.compile(
    r'(?i)ppo|personal\s+protection|restraining|mcl\s+600\.2950|contempt'
)

# Analysis dimensions for PPO content
PPO_DIMENSIONS = {
    'modification_grounds': {
        'description': 'Grounds for PPO modification or termination',
        'keywords': ['modify', 'modification', 'terminate', 'termination', 'amend',
                     'change of circumstances', 'good cause', 'burden of proof',
                     'clear and convincing', 'motion to modify', 'motion to terminate'],
    },
    'due_process': {
        'description': 'Due process violation indicators',
        'keywords': ['due process', 'notice', 'hearing', 'opportunity to be heard',
                     'ex parte', 'without notice', 'denied hearing', 'procedural',
                     'constitutional', 'fourteenth amendment', '14th amendment',
                     'right to respond', 'denied opportunity'],
    },
    'overbreadth': {
        'description': 'PPO overbreadth or vagueness issues',
        'keywords': ['overbroad', 'overbreadth', 'vague', 'vagueness', 'unclear',
                     'ambiguous', 'scope', 'narrowly tailored', 'first amendment',
                     'free speech', 'excessive', 'unnecessarily broad', 'chilling effect'],
    },
    'contempt': {
        'description': 'Contempt of PPO proceedings',
        'keywords': ['contempt', 'violation', 'willful', 'knowing', 'indirect contempt',
                     'criminal contempt', 'civil contempt', 'jail', 'incarceration',
                     'sanction', 'fine', 'penalty', 'enforcement'],
    },
    'statutory_basis': {
        'description': 'Statutory and rule references',
        'keywords': ['mcl 600.2950', 'mcl 600.2950a', 'mcr 3.706', 'mcr 3.707',
                     'mcr 3.708', 'mcl 764.15b', 'mcl 600.2950h', 'mcl 750.411h',
                     'mcl 750.411i', 'mcl 750.411s'],
    },
}


class LaneAPpo(Agent9999):
    """Lane A PPO/Contempt Intelligence — due process & overbreadth analysis."""

    def __init__(self):
        super().__init__(agent_id="K02-PPO")
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
            SELECT id, full_path, file_name
            FROM files
            WHERE processed = 1
              AND (full_path LIKE '%ppo%' OR full_path LIKE '%contempt%'
                   OR full_path LIKE '%protection%' OR full_path LIKE '%restraining%'
                   OR full_path LIKE '%600.2950%')
        """)
        return cursor.fetchall()

    def _process_item(self, item: Any) -> None:
        file_id, full_path, file_name = item['id'], item['full_path'], item['file_name']

        try:
            with open(self.long_path(full_path), 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except (OSError, PermissionError) as e:
            raise SkipItemError(f"Cannot read {file_name}: {e}")

        if not content.strip():
            raise SkipItemError(f"Empty file: {file_name}")

        # Must contain PPO signals
        if not PPO_PATTERN.search(content):
            raise SkipItemError(f"No PPO signals in {file_name}")

        # LANE PURITY CHECK
        self._lane_purity_check(content, file_name)

        content_lower = content.lower()
        dimension_results = {}

        for dim_key, dim_def in PPO_DIMENSIONS.items():
            hits = []
            for kw in dim_def['keywords']:
                for m in re.finditer(re.escape(kw), content_lower):
                    start = max(0, m.start() - 120)
                    end = min(len(content), m.end() + 120)
                    hits.append(content[start:end].strip())

            dimension_results[dim_key] = {
                'dimension': dim_key,
                'description': dim_def['description'],
                'hit_count': len(hits),
                'excerpts': hits[:5],
            }

        # Overall relevance score
        total_hits = sum(d['hit_count'] for d in dimension_results.values())
        score = min(10.0, total_hits * 0.5)

        analysis = {
            'file_name': file_name,
            'dimensions': dimension_results,
            'total_hits': total_hits,
            'dimensions_present': [k for k, v in dimension_results.items() if v['hit_count'] > 0],
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'ppo_analysis', ?, 'A', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K02|ppo|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), score, self.agent_id)
        )
        self.db.commit()

    def _lane_purity_check(self, content: str, file_name: str) -> None:
        """Raise LaneCrossContaminationError if Lane B signals detected."""
        content_lower = content.lower()
        for signal in LANE_B_SIGNALS:
            if signal in content_lower:
                raise LaneCrossContaminationError(
                    f"Lane B signal '{signal}' detected in Lane A PPO file: {file_name}"
                )
