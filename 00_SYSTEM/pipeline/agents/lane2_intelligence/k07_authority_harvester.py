"""
DELTA9 — K07 Authority Harvester Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Extracts ALL MCL/MCR/MRE/case/federal citations from processed files.
Builds authority map: what we cite → what text we have → what's missing.
"""
import json
import hashlib
import re
from collections import defaultdict
from typing import Any, Dict, List

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
    LaneCrossContaminationError,
)

# Citation extraction patterns
CITATION_PATTERNS = {
    'MCL': re.compile(r'MCL\s+\d+[\.\d]*[a-z]?', re.IGNORECASE),
    'MCR': re.compile(r'MCR\s+\d+[\.\d]*[a-zA-Z]?(?:\(\d+\))*', re.IGNORECASE),
    'MRE': re.compile(r'MRE\s+\d+', re.IGNORECASE),
    'case_law': re.compile(r'\d+\s+(?:Mich|NW2d|US|F\.?(?:2d|3d)?)\s+\d+'),
    'federal_statute': re.compile(r'\d+\s+USC?\s+§?\s*\d+', re.IGNORECASE),
}


class AuthorityHarvester(Agent9999):
    """Authority Harvester Intelligence — citation extraction and authority mapping."""

    def __init__(self):
        super().__init__(agent_id="K07-AUTHORITY")
        self.parallel_workers = 8   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200
        self._authority_map: Dict[str, Dict] = defaultdict(lambda: {
            'cite': '',
            'cite_type': '',
            'files_found_in': [],
            'excerpts': [],
            'count': 0,
        })

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

        citations_found = []

        for cite_type, pattern in CITATION_PATTERNS.items():
            for m in pattern.finditer(content):
                cite_text = m.group().strip()
                cite_normalized = self._normalize_citation(cite_text, cite_type)

                # Extract surrounding context
                ctx_start = max(0, m.start() - 150)
                ctx_end = min(len(content), m.end() + 150)
                excerpt = content[ctx_start:ctx_end].strip()

                citation = {
                    'cite': cite_normalized,
                    'cite_raw': cite_text,
                    'cite_type': cite_type,
                    'excerpt': excerpt[:400],
                    'position': m.start(),
                    'source_file': file_name,
                }
                citations_found.append(citation)

                # Update authority map
                map_entry = self._authority_map[cite_normalized]
                map_entry['cite'] = cite_normalized
                map_entry['cite_type'] = cite_type
                map_entry['count'] += 1
                if file_name not in map_entry['files_found_in']:
                    map_entry['files_found_in'].append(file_name)
                if len(map_entry['excerpts']) < 3:
                    map_entry['excerpts'].append(excerpt[:300])

        if not citations_found:
            raise SkipItemError(f"No citations found in {file_name}")

        # Deduplicate citations within this file
        seen = set()
        unique_citations = []
        for c in citations_found:
            if c['cite'] not in seen:
                seen.add(c['cite'])
                unique_citations.append(c)

        for citation in unique_citations:
            score = self._score_citation(citation)

            self._db_execute(
                """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
                   VALUES (?, 'citation', ?, 'C', ?, ?, 'EVIDENCE_FACT', ?)""",
                (hashlib.sha1(f'K07|cite|{file_id}|{citation["cite"]}'.encode()).hexdigest()[:16],
                 file_id, json.dumps(citation), score, self.agent_id)
            )

        self.db.commit()

    def _normalize_citation(self, cite_text: str, cite_type: str) -> str:
        """Normalize citation for deduplication and mapping."""
        normalized = re.sub(r'\s+', ' ', cite_text).strip()
        if cite_type in ('MCL', 'MCR', 'MRE'):
            normalized = normalized.upper()
        return normalized

    def _score_citation(self, citation: dict) -> float:
        """Score citation importance."""
        score = 1.0

        cite_type = citation['cite_type']
        if cite_type == 'MCL':
            score += 2.0
        elif cite_type == 'MCR':
            score += 2.0
        elif cite_type == 'case_law':
            score += 3.0  # case law is high value
        elif cite_type == 'federal_statute':
            score += 2.5
        elif cite_type == 'MRE':
            score += 1.5

        return min(10.0, score)

    def _finalize(self) -> None:
        """Log authority map summary after all files processed."""
        total_unique = len(self._authority_map)
        by_type = defaultdict(int)
        for entry in self._authority_map.values():
            by_type[entry['cite_type']] += 1

        summary_parts = [f"{ct}: {count}" for ct, count in sorted(by_type.items())]
        self._log("AUTHORITY_MAP", f"{total_unique} unique citations — {', '.join(summary_parts)}")
