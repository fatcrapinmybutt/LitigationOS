"""
DELTA9 — K04 Lane C Convergence Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Identifies cross-lane convergence evidence touching BOTH Lane A and Lane B.
Builds Monell patterns: policy/custom → constitutional harm.
Maps §1983/§1985 elements from cross-lane evidence.

THIS IS THE ONE AGENT THAT CAN REFERENCE BOTH LANES — no lane purity check.
"""
import json
import hashlib
import re
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
    LaneCrossContaminationError,
)

# §1983 elements
SECTION_1983_ELEMENTS = {
    'state_action': {
        'description': 'Action under color of state law',
        'keywords': ['under color of', 'state action', 'color of law', 'official capacity',
                     'government actor', 'state actor', 'county', 'municipal',
                     'judge', 'court officer', 'foc', 'public official'],
    },
    'constitutional_deprivation': {
        'description': 'Deprivation of constitutional right',
        'keywords': ['due process', 'equal protection', 'first amendment', 'fourth amendment',
                     'fourteenth amendment', 'constitutional right', 'liberty interest',
                     'property interest', 'fundamental right', 'substantive due process',
                     'procedural due process'],
    },
    'causation': {
        'description': 'Causal connection between action and deprivation',
        'keywords': ['caused', 'resulted in', 'directly', 'but for', 'proximate cause',
                     'consequence', 'as a result', 'led to', 'deprivation'],
    },
}

# §1985 conspiracy elements
SECTION_1985_ELEMENTS = {
    'conspiracy': {
        'description': 'Two or more persons conspiring',
        'keywords': ['conspir', 'agreement', 'coordinated', 'concert', 'joint action',
                     'common plan', 'scheme', 'collu', 'working together'],
    },
    'class_based_animus': {
        'description': 'Class-based discriminatory animus',
        'keywords': ['discriminat', 'animus', 'class of persons', 'invidious',
                     'targeted', 'bias', 'prejudice', 'hostility'],
    },
}

# Monell pattern elements
MONELL_ELEMENTS = {
    'policy': {
        'description': 'Official policy or widespread custom',
        'keywords': ['policy', 'custom', 'practice', 'standard procedure', 'standing order',
                     'municipal policy', 'county policy', 'deliberate indifference',
                     'final policymaker', 'ratif'],
    },
    'pattern': {
        'description': 'Pattern of similar violations',
        'keywords': ['pattern', 'repeated', 'systematic', 'ongoing', 'persistent',
                     'multiple instances', 'history of', 'series of', 'frequent'],
    },
    'constitutional_harm': {
        'description': 'Resulting constitutional harm',
        'keywords': ['deprivation', 'violated', 'infringed', 'denied', 'deprived',
                     'constitutional injury', 'harm', 'damage'],
    },
}


class LaneCConvergence(Agent9999):
    """Lane C Convergence Intelligence — cross-lane pattern mapping for §1983/§1985/Monell."""

    def __init__(self):
        super().__init__(agent_id="K04-CONVERGE")
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

        content_lower = content.lower()

        # Detect lane signals present in this file
        lane_a_hits = [s for s in LANE_A_SIGNALS if s in content_lower]
        lane_b_hits = [s for s in LANE_B_SIGNALS if s in content_lower]
        lane_c_hits = [s for s in LANE_C_SIGNALS if s in content_lower]

        has_lane_a = len(lane_a_hits) > 0
        has_lane_b = len(lane_b_hits) > 0
        is_convergence = has_lane_a and has_lane_b

        # Skip files that don't touch at least Lane C signals or convergence
        if not is_convergence and not lane_c_hits:
            raise SkipItemError(f"No convergence pattern in {file_name}")

        # Map §1983 elements
        s1983_results = self._map_elements(content, content_lower, SECTION_1983_ELEMENTS)

        # Map §1985 elements
        s1985_results = self._map_elements(content, content_lower, SECTION_1985_ELEMENTS)

        # Map Monell elements
        monell_results = self._map_elements(content, content_lower, MONELL_ELEMENTS)

        # Score: convergence evidence is highest value
        convergence_score = 0.0
        if is_convergence:
            convergence_score += 5.0
        convergence_score += min(2.0, len(lane_c_hits) * 0.5)
        s1983_present = [k for k, v in s1983_results.items() if v['hit_count'] > 0]
        s1985_present = [k for k, v in s1985_results.items() if v['hit_count'] > 0]
        monell_present = [k for k, v in monell_results.items() if v['hit_count'] > 0]
        convergence_score += len(s1983_present) * 0.5
        convergence_score += len(s1985_present) * 0.5
        convergence_score += len(monell_present) * 0.5
        convergence_score = min(10.0, convergence_score)

        analysis = {
            'file_name': file_name,
            'is_convergence': is_convergence,
            'lane_a_signals': lane_a_hits[:10],
            'lane_b_signals': lane_b_hits[:10],
            'lane_c_signals': lane_c_hits[:10],
            'section_1983': s1983_results,
            'section_1985': s1985_results,
            'monell': monell_results,
            'convergence_score': convergence_score,
        }

        metadata = {
            'is_convergence': is_convergence,
            's1983_elements': s1983_present,
            's1985_elements': s1985_present,
            'monell_elements': monell_present,
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'convergence_pattern', ?, 'C', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K04|convergence|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), convergence_score, self.agent_id)
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
