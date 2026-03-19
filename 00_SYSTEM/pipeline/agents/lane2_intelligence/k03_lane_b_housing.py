"""
DELTA9 — K03 Lane B Housing Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Scores housing claims per MCL 554.139, MCL 445.903, MCL 554.602-612, MCL 600.5720.
LANE PURITY: Lane B ONLY — raises LaneCrossContaminationError on Lane A signals.
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

HOUSING_CLAIM_ELEMENTS = {
    'habitability_warranty': {
        'statute': 'MCL 554.139',
        'description': 'Implied warranty of habitability',
        'keywords': ['habitability', 'habitable', 'mcl 554.139', 'warranty', 'fit for use',
                     'fit for habitation', 'reasonable repair', 'health and safety',
                     'building code', 'code violation', 'uninhabitable', 'unfit',
                     'mold', 'plumbing', 'electrical', 'heating', 'structural'],
    },
    'consumer_protection': {
        'statute': 'MCL 445.903',
        'description': 'Michigan Consumer Protection Act violations',
        'keywords': ['mcl 445.903', 'consumer protection', 'mcpa', 'unfair practice',
                     'deceptive', 'misleading', 'misrepresent', 'unconscionable',
                     'unfair method', 'trade or commerce', 'consumer transaction'],
    },
    'security_deposit': {
        'statute': 'MCL 554.602-612',
        'description': 'Security deposit violations',
        'keywords': ['security deposit', 'mcl 554.602', 'mcl 554.603', 'mcl 554.604',
                     'mcl 554.605', 'mcl 554.606', 'mcl 554.607', 'mcl 554.608',
                     'mcl 554.609', 'mcl 554.610', 'mcl 554.611', 'mcl 554.612',
                     'damage list', 'itemized', 'return deposit', '30 days',
                     'escrow', 'regulated financial institution', 'double damages'],
    },
    'retaliatory_eviction': {
        'statute': 'MCL 600.5720',
        'description': 'Retaliatory eviction protections',
        'keywords': ['mcl 600.5720', 'retaliat', 'retaliatory eviction', 'complaint to authority',
                     'code enforcement', 'health department', 'building inspector',
                     'tenant rights', 'reprisal', 'evict after complaint',
                     'notice to quit', 'constructive eviction'],
    },
}


class LaneBHousing(Agent9999):
    """Lane B Housing Claim Intelligence — statutory element scoring."""

    def __init__(self):
        super().__init__(agent_id="K03-HOUSING")
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
            WHERE meek_lane LIKE '%B%' AND processed = 1
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
        claim_results = {}

        for claim_key, claim_def in HOUSING_CLAIM_ELEMENTS.items():
            hits = []
            for kw in claim_def['keywords']:
                for m in re.finditer(re.escape(kw), content_lower):
                    start = max(0, m.start() - 120)
                    end = min(len(content), m.end() + 120)
                    hits.append(content[start:end].strip())

            hit_count = len(hits)
            score = min(10, hit_count * 2) if hit_count > 0 else 0

            claim_results[claim_key] = {
                'claim': claim_key,
                'statute': claim_def['statute'],
                'description': claim_def['description'],
                'score': score,
                'hit_count': hit_count,
                'excerpts': hits[:5],
            }

        total_score = sum(c['score'] for c in claim_results.values())

        analysis = {
            'file_name': file_name,
            'claims': claim_results,
            'total_score': total_score,
            'claims_present': [k for k, v in claim_results.items() if v['score'] > 0],
        }

        self._db_execute(
            """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
               VALUES (?, 'housing_claim', ?, 'B', ?, ?, 'EVIDENCE_FACT', ?)""",
            (hashlib.sha1(f'K03|housing|{file_id}'.encode()).hexdigest()[:16],
             file_id, json.dumps(analysis), total_score, self.agent_id)
        )
        self.db.commit()

    def _lane_purity_check(self, content: str, file_name: str) -> None:
        """Raise LaneCrossContaminationError if Lane A custody signals detected."""
        content_lower = content.lower()
        for signal in LANE_A_SIGNALS:
            if signal in content_lower:
                raise LaneCrossContaminationError(
                    f"Lane A signal '{signal}' detected in Lane B file: {file_name}"
                )
