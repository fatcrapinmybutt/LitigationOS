"""
Multi-Brain Universe — Brain Manager Module
Unified interface for querying and managing all 5 LitigationOS brain databases.

Usage:
    from brain_manager import BrainManager
    bm = BrainManager()
    results = bm.search_all_brains("MCR 2.003")
    stats = bm.get_brain_stats()
"""
import sqlite3
import os
import sys
from contextlib import contextmanager
from datetime import datetime

try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
except (OSError, AttributeError):
    pass  # Handle redirected/piped stdout gracefully

BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))

BRAIN_NAMES = [
    'authority_brain',
    'narrative_brain',
    'entity_brain',
    'claims_brain',
    'interpretation_brain',
    'cross_brain_index',
]

# FTS5 tables per brain for universal search
BRAIN_FTS_TABLES = {
    'authority_brain': [
        'court_rules_fts', 'statutes_fts', 'case_law_fts',
        'evidence_rules_fts', 'benchbook_fts',
    ],
    'narrative_brain': [
        'timeline_fts', 'extractions_fts', 'orders_fts',
        'police_fts', 'testimony_fts', 'communications_fts',
    ],
    'entity_brain': [],
    'claims_brain': [],
    'interpretation_brain': [
        'arguments_fts', 'impeachment_fts', 'drafts_fts', 'applications_fts',
    ],
    'cross_brain_index': ['universal_search'],
}

PRAGMAS = """
PRAGMA busy_timeout = 120000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
"""


class BrainManager:
    """Unified interface for the Multi-Brain Universe."""

    def __init__(self, brain_dir=None):
        self.brain_dir = brain_dir or BRAIN_DIR

    def _db_path(self, brain_name):
        """Return the full path to a brain database file."""
        if not brain_name.endswith('.db'):
            brain_name = f"{brain_name}.db"
        path = os.path.join(self.brain_dir, brain_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Brain database not found: {path}")
        return path

    @contextmanager
    def open_brain(self, brain_name):
        """Context manager that returns a sqlite3 connection with all PRAGMAs set.

        Usage:
            with bm.open_brain('authority_brain') as conn:
                rows = conn.execute("SELECT * FROM court_rules LIMIT 5").fetchall()
        """
        conn = sqlite3.connect(self._db_path(brain_name))
        conn.row_factory = sqlite3.Row
        conn.executescript(PRAGMAS)
        try:
            yield conn
        finally:
            conn.close()

    def query_brain(self, brain_name, sql, params=None):
        """Execute a query on a specific brain and return all results as dicts.

        Args:
            brain_name: Name of the brain (e.g. 'authority_brain')
            sql: SQL query string
            params: Optional tuple of query parameters

        Returns:
            List of dicts, one per row.
        """
        with self.open_brain(brain_name) as conn:
            cursor = conn.execute(sql, params or ())
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def search_all_brains(self, search_term):
        """FTS5 search across all brain databases that have FTS tables.

        Args:
            search_term: The term to search for (supports FTS5 syntax like OR, AND, NEAR)

        Returns:
            List of dicts with keys: brain, fts_table, results
        """
        all_results = []
        for brain_name in BRAIN_NAMES:
            fts_tables = BRAIN_FTS_TABLES.get(brain_name, [])
            if not fts_tables:
                continue
            try:
                with self.open_brain(brain_name) as conn:
                    for fts_table in fts_tables:
                        try:
                            rows = conn.execute(
                                f"SELECT *, rank FROM {fts_table} WHERE {fts_table} MATCH ? ORDER BY rank LIMIT 20",
                                (search_term,)
                            ).fetchall()
                            if rows:
                                columns = [desc[0] for desc in conn.execute(
                                    f"SELECT * FROM {fts_table} LIMIT 0"
                                ).description] + ['rank']
                                results = [dict(zip(columns, row)) for row in rows]
                                all_results.append({
                                    'brain': brain_name,
                                    'fts_table': fts_table,
                                    'match_count': len(results),
                                    'results': results,
                                })
                        except sqlite3.OperationalError:
                            # FTS table may be empty or not match
                            continue
            except FileNotFoundError:
                continue
        return all_results

    def get_brain_stats(self):
        """Get row counts for all tables in all brains.

        Returns:
            Dict mapping brain_name -> {table_name: row_count, ...}
        """
        stats = {}
        for brain_name in BRAIN_NAMES:
            try:
                with self.open_brain(brain_name) as conn:
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    ).fetchall()
                    brain_stats = {}
                    for (tbl,) in tables:
                        try:
                            count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                            brain_stats[tbl] = count
                        except sqlite3.OperationalError:
                            brain_stats[tbl] = -1
                    stats[brain_name] = brain_stats
            except FileNotFoundError:
                stats[brain_name] = {'error': 'database not found'}
        return stats

    def add_provenance(self, brain_name, record_table, record_id,
                       source_file=None, source_page=None, source_url=None,
                       source_type=None, extraction_method=None,
                       extraction_confidence=1.0, sha256=None):
        """Track where a piece of data came from.

        Args:
            brain_name: Which brain the record lives in
            record_table: Table name within the brain
            record_id: Primary key of the record
            source_file: Path to source file (optional)
            source_page: Page number in source (optional)
            source_url: URL of source (optional)
            source_type: Type of source (e.g. 'pdf', 'transcript') (optional)
            extraction_method: How it was extracted (optional)
            extraction_confidence: Confidence score 0-1 (default 1.0)
            sha256: Hash of source content (optional)
        """
        with self.open_brain(brain_name) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO provenance
                   (record_table, record_id, source_file, source_page,
                    source_url, source_type, extraction_method,
                    extraction_confidence, sha256)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record_table, record_id, source_file, source_page,
                 source_url, source_type, extraction_method,
                 extraction_confidence, sha256)
            )
            conn.commit()

    def cross_reference(self, source_brain, source_table, source_id,
                        target_brain, target_table, target_id,
                        relationship, confidence=1.0):
        """Link records across brains via the cross-brain index.

        Args:
            source_brain: Name of the source brain
            source_table: Table in source brain
            source_id: Record ID in source brain
            target_brain: Name of the target brain
            target_table: Table in target brain
            target_id: Record ID in target brain
            relationship: Type of relationship (e.g. 'cites', 'supports', 'contradicts')
            confidence: Confidence score 0-1 (default 1.0)
        """
        with self.open_brain('cross_brain_index') as conn:
            conn.execute(
                """INSERT OR IGNORE INTO cross_references
                   (source_brain, source_table, source_id,
                    target_brain, target_table, target_id,
                    relationship_type, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (source_brain, source_table, source_id,
                 target_brain, target_table, target_id,
                 relationship, confidence)
            )
            conn.commit()

    def queue_extraction(self, file_path, priority=5, target_brain=None,
                         file_type=None, file_size=None, extraction_method=None):
        """Add a file to the extraction queue for processing.

        Args:
            file_path: Path to the file to be processed
            priority: 1 (highest) to 10 (lowest), default 5
            target_brain: Which brain should receive the extracted data
            file_type: Type of file (e.g. 'pdf', 'docx')
            file_size: File size in bytes
            extraction_method: Suggested extraction method
        """
        with self.open_brain('cross_brain_index') as conn:
            conn.execute(
                """INSERT OR IGNORE INTO extraction_queue
                   (file_path, file_type, file_size, priority,
                    target_brain, extraction_method)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (file_path, file_type, file_size, priority,
                 target_brain, extraction_method)
            )
            conn.commit()

    def get_queue_status(self):
        """Get the current status of the extraction queue.

        Returns:
            Dict with counts by status and the next pending items.
        """
        with self.open_brain('cross_brain_index') as conn:
            status_counts = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM extraction_queue GROUP BY status"
            ).fetchall()
            next_items = conn.execute(
                """SELECT file_path, priority, target_brain, queued_at
                   FROM extraction_queue
                   WHERE status = 'pending'
                   ORDER BY priority ASC, queued_at ASC
                   LIMIT 10"""
            ).fetchall()
            return {
                'counts': {row[0]: row[1] for row in status_counts},
                'next_pending': [
                    {'file_path': r[0], 'priority': r[1],
                     'target_brain': r[2], 'queued_at': r[3]}
                    for r in next_items
                ],
            }

    def snapshot_stats(self):
        """Take a snapshot of all brain statistics and store in cross_brain_index."""
        stats = self.get_brain_stats()
        with self.open_brain('cross_brain_index') as conn:
            rows = []
            now = datetime.utcnow().isoformat()
            for brain_name, tables in stats.items():
                if isinstance(tables, dict) and 'error' not in tables:
                    for table_name, count in tables.items():
                        rows.append((brain_name, table_name, count, now))
            if rows:
                conn.executemany(
                    "INSERT INTO brain_stats (brain_name, table_name, row_count, snapshot_at) VALUES (?, ?, ?, ?)",
                    rows
                )
                conn.commit()
        return stats


# ─────────────────────────────────────────────────────────
# Convenience functions (module-level)
# ─────────────────────────────────────────────────────────

_default_manager = None

def _mgr():
    global _default_manager
    if _default_manager is None:
        _default_manager = BrainManager()
    return _default_manager

def open_brain(brain_name):
    """Return a context manager for a brain connection."""
    return _mgr().open_brain(brain_name)

def query_brain(brain_name, sql, params=None):
    """Execute a query on a specific brain."""
    return _mgr().query_brain(brain_name, sql, params)

def search_all_brains(search_term):
    """FTS5 search across all brains."""
    return _mgr().search_all_brains(search_term)

def get_brain_stats():
    """Get row counts for all tables in all brains."""
    return _mgr().get_brain_stats()

def add_provenance(brain_name, record_table, record_id, **kwargs):
    """Track provenance for a record."""
    return _mgr().add_provenance(brain_name, record_table, record_id, **kwargs)

def cross_reference(source_brain, source_table, source_id,
                    target_brain, target_table, target_id,
                    relationship, confidence=1.0):
    """Link records across brains."""
    return _mgr().cross_reference(
        source_brain, source_table, source_id,
        target_brain, target_table, target_id,
        relationship, confidence
    )

def queue_extraction(file_path, priority=5, target_brain=None, **kwargs):
    """Add file to extraction queue."""
    return _mgr().queue_extraction(file_path, priority, target_brain, **kwargs)

def get_brain_stats_report():
    """Print a formatted report of all brain statistics."""
    stats = get_brain_stats()
    total_tables = 0
    total_rows = 0
    for brain_name, tables in stats.items():
        if isinstance(tables, dict) and 'error' not in tables:
            print(f"\n{'=' * 60}")
            print(f"  {brain_name.upper()}")
            print(f"{'=' * 60}")
            for tbl, count in sorted(tables.items()):
                print(f"  {tbl:<40} {count:>8} rows")
                total_tables += 1
                if count >= 0:
                    total_rows += count
    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {total_tables} tables, {total_rows} rows across all brains")
    print(f"{'=' * 60}")
    return stats


if __name__ == '__main__':
    print("Multi-Brain Universe — Status Report")
    print("=" * 60)
    get_brain_stats_report()
