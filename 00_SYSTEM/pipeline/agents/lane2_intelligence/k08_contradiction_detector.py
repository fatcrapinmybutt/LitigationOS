"""
DELTA9 — K08 Contradiction Detector Intelligence
Tier K · Lane 2 Intelligence · MAX LEVEL 9999++

Cross-references statements across files to find contradictions:
  - Sworn testimony vs. records
  - Opposing claims vs. evidence
  - Judge orders vs. MCR rules
Severity: sworn vs record = HIGH, claim vs evidence = MEDIUM.
"""
import json
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
    LaneCrossContaminationError,
)

# Contradiction type definitions with severity
CONTRADICTION_TYPES = {
    'sworn_vs_record': {
        'severity': 'HIGH',
        'severity_score': 9.0,
        'description': 'Sworn testimony contradicts documented record',
        'sworn_indicators': ['testified', 'under oath', 'sworn', 'affidavit', 'deposition',
                             'declaration under penalty', 'swore', 'affirmed'],
        'record_indicators': ['record shows', 'document', 'exhibit', 'evidence',
                              'report indicates', 'records reflect', 'file shows',
                              'log', 'transcript'],
    },
    'claim_vs_evidence': {
        'severity': 'MEDIUM',
        'severity_score': 6.0,
        'description': 'Party claim contradicted by available evidence',
        'claim_indicators': ['claimed', 'alleged', 'asserted', 'contended', 'argued',
                             'maintained', 'represented', 'stated', 'said'],
        'evidence_indicators': ['however', 'but', 'contrary', 'contradicts', 'inconsistent',
                                'despite', 'in fact', 'actually', 'nevertheless',
                                'notwithstanding', 'belied by'],
    },
    'order_vs_rule': {
        'severity': 'HIGH',
        'severity_score': 8.0,
        'description': 'Court order conflicts with MCR procedural requirements',
        'order_indicators': ['court ordered', 'order', 'it is ordered', 'the court orders',
                             'hereby ordered', 'judgment', 'ruling'],
        'rule_indicators': ['mcr', 'court rule', 'required by rule', 'rule requires',
                            'procedural requirement', 'mandatory', 'shall'],
    },
}

# Negation / contradiction signal patterns
CONTRADICTION_SIGNALS = re.compile(
    r'(?i)\b(?:however|but|contrary|contradicts?|inconsistent|despite|in\s+fact|'
    r'actually|nevertheless|notwithstanding|belied\s+by|false|untrue|incorrect|'
    r'inaccurate|misleading|not\s+true|never|did\s+not|failed\s+to|denied)\b'
)


class ContradictionDetector(Agent9999):
    """Contradiction Detector Intelligence — cross-reference statements for inconsistencies."""

    def __init__(self):
        super().__init__(agent_id="K08-CONTRADICT")
        self.parallel_workers = 8   # I/O bound — parallelize file reads
        self.item_timeout = 15      # skip files that take >15s to read
        self.checkpoint_interval = 200
        self._person_statements: Dict[str, List[dict]] = {}

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
        # Load existing person_profile atoms for cross-referencing
        self._load_person_statements()

        cursor = self._db_execute("""
            SELECT id, full_path, file_name
            FROM files
            WHERE processed = 1
        """)
        return cursor.fetchall()

    def _load_person_statements(self) -> None:
        """Load existing person_profile atoms to build cross-reference corpus."""
        try:
            cursor = self._db_execute("""
                SELECT content, metadata FROM atoms
                WHERE atom_type = 'person_profile' AND created_by = 'K05-PERSONS'
            """)
            for row in cursor.fetchall():
                try:
                    profile = json.loads(row['content'])
                    person_key = profile.get('person_key', 'unknown')
                    statements = profile.get('statements', [])
                    mentions = profile.get('mentions', [])

                    if person_key not in self._person_statements:
                        self._person_statements[person_key] = []

                    for stmt in statements:
                        self._person_statements[person_key].append({
                            'type': 'statement',
                            'text': stmt.get('text', ''),
                            'source': profile.get('display_name', person_key),
                        })

                    for mention in mentions:
                        self._person_statements[person_key].append({
                            'type': 'mention',
                            'text': mention.get('context', ''),
                            'source': profile.get('display_name', person_key),
                        })
                except (json.JSONDecodeError, KeyError):
                    continue
        except Exception:
            self._log("WARN", "Could not load person_profile atoms — running without cross-ref")

    def _process_item(self, item: Any) -> None:
        file_id, full_path, file_name = item['id'], item['full_path'], item['file_name']

        try:
            with open(self.long_path(full_path), 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except (OSError, PermissionError) as e:
            raise SkipItemError(f"Cannot read {file_name}: {e}")

        if not content.strip():
            raise SkipItemError(f"Empty file: {file_name}")

        contradictions = []

        # Scan for each contradiction type
        for ctype_key, ctype_def in CONTRADICTION_TYPES.items():
            found = self._detect_contradiction_type(content, file_name, ctype_key, ctype_def)
            contradictions.extend(found)

        # Cross-reference with existing person statements
        cross_ref = self._cross_reference_persons(content, file_name)
        contradictions.extend(cross_ref)

        if not contradictions:
            raise SkipItemError(f"No contradictions detected in {file_name}")

        for contradiction in contradictions:
            self._db_execute(
                """INSERT OR IGNORE INTO atoms (id, atom_type, source_file_id, meek_lane, content, confidence, posture, created_by)
                   VALUES (?, 'contradiction', ?, 'C', ?, ?, 'EVIDENCE_FACT', ?)""",
                (hashlib.sha1(f'K08|contra|{file_id}'.encode()).hexdigest()[:16],
                 file_id, json.dumps(contradiction), contradiction['severity_score'], self.agent_id)
            )

        self.db.commit()

    def _detect_contradiction_type(self, content: str, file_name: str,
                                   ctype_key: str, ctype_def: dict) -> List[dict]:
        """Detect contradictions of a specific type within content."""
        results = []
        content_lower = content.lower()

        # Get the two indicator sets for this contradiction type
        indicator_keys = [k for k in ctype_def.keys() if k.endswith('_indicators')]
        if len(indicator_keys) < 2:
            return results

        set_a_key = indicator_keys[0]
        set_b_key = indicator_keys[1]
        set_a_indicators = ctype_def[set_a_key]
        set_b_indicators = ctype_def[set_b_key]

        # Find regions with set_a indicators
        set_a_positions = []
        for kw in set_a_indicators:
            for m in re.finditer(re.escape(kw), content_lower):
                set_a_positions.append((m.start(), m.end(), kw))

        # Find regions with set_b indicators
        set_b_positions = []
        for kw in set_b_indicators:
            for m in re.finditer(re.escape(kw), content_lower):
                set_b_positions.append((m.start(), m.end(), kw))

        # Find contradiction signals near co-occurring indicator pairs
        for a_start, a_end, a_kw in set_a_positions:
            for b_start, b_end, b_kw in set_b_positions:
                # Must be within 500 chars of each other
                distance = abs(a_start - b_start)
                if distance > 500:
                    continue

                # Check for contradiction signal between them
                region_start = min(a_start, b_start)
                region_end = max(a_end, b_end)
                region = content[region_start:region_end]

                if CONTRADICTION_SIGNALS.search(region):
                    ctx_start = max(0, region_start - 100)
                    ctx_end = min(len(content), region_end + 100)
                    context = content[ctx_start:ctx_end].strip()

                    results.append({
                        'contradiction_type': ctype_key,
                        'severity': ctype_def['severity'],
                        'severity_score': ctype_def['severity_score'],
                        'description': ctype_def['description'],
                        'indicator_a': a_kw,
                        'indicator_b': b_kw,
                        'context': context[:600],
                        'source_file': file_name,
                        'distance_chars': distance,
                    })

                    # Cap per type per file
                    if len(results) >= 10:
                        return results

        return results

    def _cross_reference_persons(self, content: str, file_name: str) -> List[dict]:
        """Cross-reference content against existing person statements for contradictions."""
        results = []
        content_lower = content.lower()

        for person_key, statements in self._person_statements.items():
            for stmt in statements:
                stmt_text = stmt.get('text', '')
                if not stmt_text or len(stmt_text) < 20:
                    continue

                # Extract key phrases from statement (first 50 chars as a signal)
                stmt_signal = stmt_text[:50].lower()

                # Check if this file references the same topic
                if stmt_signal[:20] not in content_lower:
                    continue

                # Check for contradiction signals near the reference
                idx = content_lower.find(stmt_signal[:20])
                if idx == -1:
                    continue

                region_start = max(0, idx - 200)
                region_end = min(len(content), idx + 200 + len(stmt_signal))
                region = content[region_start:region_end]

                if CONTRADICTION_SIGNALS.search(region):
                    results.append({
                        'contradiction_type': 'cross_reference',
                        'severity': 'MEDIUM',
                        'severity_score': 6.0,
                        'description': f'Potential contradiction with {stmt["source"]} statement',
                        'person': person_key,
                        'original_statement': stmt_text[:300],
                        'contradicting_context': region.strip()[:500],
                        'source_file': file_name,
                    })

                    if len(results) >= 5:
                        return results

        return results
