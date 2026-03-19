"""
DELTA9 — K01 Lane A Custody Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Scores custody evidence per MCL 722.23 best interest factors (a–l).
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

# MCL 722.23 best interest factors (a–l) with keyword sets for scoring
BEST_INTEREST_FACTORS = {
    'a': {
        'name': 'love_affection_emotional_ties',
        'description': 'Love, affection, and other emotional ties',
        'keywords': ['love', 'affection', 'bond', 'emotional', 'attachment', 'close',
                     'relationship', 'nurtur', 'caring', 'devoted'],
    },
    'b': {
        'name': 'capacity_to_give_love',
        'description': 'Capacity to give love, affection, and guidance',
        'keywords': ['capacity', 'guidance', 'discipline', 'encourage', 'education',
                     'upbringing', 'values', 'moral', 'continue education', 'raise'],
    },
    'c': {
        'name': 'provide_food_clothing_medical',
        'description': 'Capacity to provide food, clothing, medical care',
        'keywords': ['food', 'clothing', 'medical', 'shelter', 'basic needs', 'insurance',
                     'healthcare', 'necessities', 'provide', 'financial'],
    },
    'd': {
        'name': 'length_stable_environment',
        'description': 'Length of time in a stable, satisfactory environment',
        'keywords': ['stable', 'stability', 'environment', 'length of time', 'years',
                     'months', 'resided', 'lived', 'continuous', 'established'],
    },
    'e': {
        'name': 'permanence_family_unit',
        'description': 'Permanence as a family unit of existing or proposed custodial home',
        'keywords': ['permanent', 'family unit', 'custodial home', 'proposed', 'existing',
                     'household', 'intact', 'family structure', 'step-parent', 'cohabit'],
    },
    'f': {
        'name': 'moral_fitness',
        'description': 'Moral fitness of the parties',
        'keywords': ['moral', 'fitness', 'character', 'criminal', 'conviction', 'substance',
                     'alcohol', 'drug', 'abuse', 'conduct', 'integrity'],
    },
    'g': {
        'name': 'mental_physical_health',
        'description': 'Mental and physical health of the parties',
        'keywords': ['mental health', 'physical health', 'disability', 'illness', 'diagnosis',
                     'therapy', 'treatment', 'medication', 'psychological', 'condition'],
    },
    'h': {
        'name': 'home_school_community_record',
        'description': 'Home, school, and community record of the child',
        'keywords': ['school', 'community', 'record', 'grades', 'activities', 'friends',
                     'teacher', 'extracurricular', 'attendance', 'neighborhood'],
    },
    'i': {
        'name': 'child_preference',
        'description': "Reasonable preference of the child if of sufficient age",
        'keywords': ['preference', 'child wants', 'child wishes', 'expressed', 'prefers',
                     'choose', 'sufficient age', 'mature enough', 'opinion'],
    },
    'j': {
        'name': 'willingness_facilitate_relationship',
        'description': 'Willingness to facilitate close relationship with other parent',
        'keywords': ['facilitate', 'willingness', 'cooperate', 'co-parent', 'access',
                     'parenting time', 'visitation', 'encourage relationship', 'alienat'],
    },
    'k': {
        'name': 'domestic_violence',
        'description': 'Domestic violence regardless of directed at child',
        'keywords': ['domestic violence', 'assault', 'threat', 'ppo', 'protection order',
                     'abuse', 'physical harm', 'stalking', 'intimidat', 'fear'],
    },
    'l': {
        'name': 'other_relevant_factor',
        'description': 'Any other factor considered by the court to be relevant',
        'keywords': ['sibling', 'special needs', 'relocation', 'work schedule', 'daycare',
                     'extended family', 'cultural', 'religious', 'other factor'],
    },
}


class LaneACustody(Agent9999):
    """Lane A Custody Factor Intelligence — MCL 722.23 scoring."""

    def __init__(self):
        super().__init__(agent_id="K01-CUSTODY")
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
            WHERE meek_lane LIKE '%A%' AND processed = 1
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

        # LANE PURITY CHECK
        self._lane_purity_check(content, file_name)

        content_lower = content.lower()
        factor_results = {}

        for factor_key, factor_def in BEST_INTEREST_FACTORS.items():
            hits = []
            for kw in factor_def['keywords']:
                matches = list(re.finditer(re.escape(kw), content_lower))
                if matches:
                    for m in matches:
                        start = max(0, m.start() - 100)
                        end = min(len(content), m.end() + 100)
                        hits.append(content[start:end].strip())

            hit_count = len(hits)
            # Score 0-10 based on keyword density (capped)
            score = min(10, hit_count * 2) if hit_count > 0 else 0

            factor_results[factor_key] = {
                'factor': factor_key,
                'name': factor_def['name'],
                'description': factor_def['description'],
                'score': score,
                'hit_count': hit_count,
                'excerpts': hits[:5],  # cap excerpts
            }

        total_score = sum(f['score'] for f in factor_results.values())

        analysis = {
            'file_name': file_name,
            'factors': factor_results,
            'total_score': total_score,
            'factors_present': [k for k, v in factor_results.items() if v['score'] > 0],
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'custody_factor', ?, 'A', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K01|custody|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), total_score, self.agent_id)
        )
        self.db.commit()

    def _lane_purity_check(self, content: str, file_name: str) -> None:
        """Raise LaneCrossContaminationError if Lane B signals detected."""
        content_lower = content.lower()
        for signal in LANE_B_SIGNALS:
            if signal in content_lower:
                raise LaneCrossContaminationError(
                    f"Lane B signal '{signal}' detected in Lane A file: {file_name}"
                )
