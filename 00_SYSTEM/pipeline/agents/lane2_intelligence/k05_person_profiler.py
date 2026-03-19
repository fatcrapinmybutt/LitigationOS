"""
DELTA9 — K05 Person Profiler Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Builds adversary profiles: tracks every mention, statement, role, and contradiction
for key persons across all processed files.
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

# Key persons with regex patterns and known roles
KEY_PERSONS = {
    'emily_watson': {
        'display_name': 'Emily Watson',
        'pattern': re.compile(r'(?i)emily\s*(a\.?\s*)?watson'),
        'aliases': ['emily', 'emily a watson', 'emily a. watson', 'e. watson', 'e watson'],
        'known_roles': ['party', 'petitioner', 'respondent'],
        'category': 'watson_family',
    },
    'albert_watson': {
        'display_name': 'Albert Watson',
        'pattern': re.compile(r'(?i)albert\s*(l\.?\s*)?watson'),
        'aliases': ['albert', 'albert l watson', 'albert l. watson', 'al watson'],
        'known_roles': ['party', 'petitioner', 'respondent'],
        'category': 'watson_family',
    },
    'lori_watson': {
        'display_name': 'Lori Watson',
        'pattern': re.compile(r'(?i)lori\s*(j\.?\s*)?watson'),
        'aliases': ['lori watson', 'lori j watson', 'lori j. watson'],
        'known_roles': ['family', 'witness'],
        'category': 'watson_family',
    },
    'cody_watson': {
        'display_name': 'Cody Watson',
        'pattern': re.compile(r'(?i)cody\s*(j\.?\s*)?watson'),
        'aliases': ['cody watson', 'cody j watson', 'cody j. watson'],
        'known_roles': ['family', 'witness'],
        'category': 'watson_family',
    },
    'david_rusco': {
        'display_name': 'David Rusco',
        'pattern': re.compile(r'(?i)david\s*(j\.?\s*)?rusco'),
        'aliases': ['david rusco', 'david j rusco', 'david j. rusco', 'atty rusco',
                    'attorney rusco', 'mr. rusco'],
        'known_roles': ['attorney', 'opposing counsel'],
        'category': 'attorney',
    },
    'pamela_rusco': {
        'display_name': 'Pamela Rusco',
        'pattern': re.compile(r'(?i)pamela\s*(j\.?\s*)?rusco'),
        'aliases': ['pamela rusco', 'pamela j rusco', 'pamela j. rusco', 'pam rusco'],
        'known_roles': ['FOC', 'friend of the court', 'case worker'],
        'category': 'foc',
    },
    'shady_oaks': {
        'display_name': 'Shady Oaks',
        'pattern': re.compile(r'(?i)shady\s+oaks'),
        'aliases': ['shady oaks', 'shady oaks mobile home', 'shady oaks mhp'],
        'known_roles': ['landlord', 'mobile home park', 'defendant'],
        'category': 'corporate',
    },
    'homes_of_america': {
        'display_name': 'Homes of America',
        'pattern': re.compile(r'(?i)homes\s+of\s+america'),
        'aliases': ['homes of america', 'hoa'],
        'known_roles': ['corporate owner', 'parent company', 'defendant'],
        'category': 'corporate',
    },
    'alden': {
        'display_name': 'Alden',
        'pattern': re.compile(r'(?i)\balden\b'),
        'aliases': ['alden', 'alden management', 'alden torch'],
        'known_roles': ['corporate owner', 'management company', 'defendant'],
        'category': 'corporate',
    },
    'judge_mcneill': {
        'display_name': 'Judge McNeill',
        'pattern': re.compile(r'(?i)(?:judge\s+)?mcneill'),
        'aliases': ['mcneill', 'judge mcneill', 'hon. mcneill'],
        'known_roles': ['judge', 'judicial officer'],
        'category': 'judge',
    },
    'judge_hoopes': {
        'display_name': 'Judge Hoopes',
        'pattern': re.compile(r'(?i)(?:judge\s+)?hoopes'),
        'aliases': ['hoopes', 'judge hoopes', 'hon. hoopes'],
        'known_roles': ['judge', 'judicial officer'],
        'category': 'judge',
    },
}


class PersonProfiler(Agent9999):
    """Person Profiler Intelligence — tracks mentions, statements, roles, contradictions."""

    def __init__(self):
        super().__init__(agent_id="K05-PERSONS")
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

        persons_found = []

        for person_key, person_def in KEY_PERSONS.items():
            matches = list(person_def['pattern'].finditer(content))
            if not matches:
                continue

            mentions = []
            for m in matches:
                start = max(0, m.start() - 150)
                end = min(len(content), m.end() + 150)
                context = content[start:end].strip()
                mentions.append({
                    'match': m.group(),
                    'position': m.start(),
                    'context': context,
                })

            # Detect statement patterns near person mentions
            statements = self._extract_statements(content, matches)

            # Detect role indicators
            detected_roles = self._detect_roles(content, matches, person_def)

            profile = {
                'person_key': person_key,
                'display_name': person_def['display_name'],
                'category': person_def['category'],
                'mention_count': len(matches),
                'mentions': mentions[:10],  # cap at 10
                'statements': statements[:5],
                'detected_roles': detected_roles,
                'known_roles': person_def['known_roles'],
            }

            persons_found.append(profile)

        if not persons_found:
            raise SkipItemError(f"No key persons found in {file_name}")

        for profile in persons_found:
            score = min(10.0, profile['mention_count'] * 0.5 + len(profile['statements']) * 2)

            self._db_execute(
                """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
                   VALUES (?, 'person_profile', ?, 'C', ?, ?, 'EVIDENCE_FACT', ?)""",
                (hashlib.sha1(f'K05|person|{file_id}|{profile["person_key"]}'.encode()).hexdigest()[:16],
                 file_id, json.dumps(profile), score, self.agent_id)
            )

        self.db.commit()

    def _extract_statements(self, content: str, matches: list) -> List[dict]:
        """Extract statements attributed to person (said, stated, testified, etc.)."""
        statement_patterns = [
            re.compile(r'(?:said|stated|testified|claimed|alleged|asserted|declared|reported)\s+(?:that\s+)?(.{10,200})', re.IGNORECASE),
            re.compile(r'(?:testimony|statement|affidavit|declaration)\s+(?:of|from|by)\s+.{0,40}?[:]\s*(.{10,200})', re.IGNORECASE),
        ]

        statements = []
        for m in matches:
            window_start = max(0, m.start() - 50)
            window_end = min(len(content), m.end() + 500)
            window = content[window_start:window_end]

            for sp in statement_patterns:
                for sm in sp.finditer(window):
                    statements.append({
                        'type': 'attributed_statement',
                        'text': sm.group(0)[:300],
                        'near_position': m.start(),
                    })

        return statements

    def _detect_roles(self, content: str, matches: list, person_def: dict) -> List[str]:
        """Detect role indicators near person mentions."""
        role_keywords = {
            'plaintiff': ['plaintiff', 'petitioner', 'complainant'],
            'defendant': ['defendant', 'respondent'],
            'judge': ['judge', 'hon.', 'honorable', 'the court'],
            'attorney': ['attorney', 'counsel', 'esq', 'lawyer', 'atty'],
            'witness': ['witness', 'testified', 'deponent'],
            'foc': ['foc', 'friend of the court', 'case worker', 'referee'],
        }

        detected = set()
        for m in matches:
            window_start = max(0, m.start() - 100)
            window_end = min(len(content), m.end() + 100)
            window_lower = content[window_start:window_end].lower()

            for role, keywords in role_keywords.items():
                if any(kw in window_lower for kw in keywords):
                    detected.add(role)

        return list(detected)
